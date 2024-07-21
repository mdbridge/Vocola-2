import re
from vcl2py.ast import *
from vcl2py.log import *

def output(out_file, grammar, params):
    # <<<>>>
    # this is a hack to cover for the fact that dragonfly doesn't have priorities yet
    global InvertExecutables
    InvertExecutables = False
    if len(grammar["EXECUTABLE"]) == 0:
        if re.match(r'.*(short|range).*', out_file):
            InvertExecutables = True
            grammar["EXECUTABLE"] = ['emacs', 'xwin']

    global Grammar, VocolaVersion
    Grammar = grammar
    VocolaVersion = params["Vocola_version"]
    maximum_commands = params["maximum_commands"]

    global OUT
    try:
        OUT = open(out_file, "w")
    except IOError, e:
        log_error("Unable to open output file '" + out_file + \
                  "' for writing: " + str(e))
        return

    emit_file_header()

    global Emitted_Rules
    Emitted_Rules = set()

    have_non_title_specific_commands = () in grammar["CONTEXTS"].keys()
    rule_set = 0
    for titles in sorted(grammar["CONTEXTS"].keys()):
        rule_set_all      = str(rule_set) + "_set"
        rule_set_repeated = str(rule_set) + "_set_repeated"
        rule_set += 1
        rule_names = grammar["CONTEXTS"][titles]
        if titles != () and maximum_commands != 1 and have_non_title_specific_commands:
            rule_names += ["0_set"]
        grammar["RULES"][rule_set_all] = one_of(rule_names)
        if maximum_commands == 1:
            grammar["CONTEXTS"][titles] = [rule_set_all]
        else:
            grammar["RULES"][rule_set_repeated] = magic_with(
                repeated_element(rule_ref(rule_set_all), maximum_commands), maximum_commands)
            grammar["CONTEXTS"][titles] = [rule_set_repeated]

    for titles in sorted(grammar["CONTEXTS"].keys()):
        rule_names = grammar["CONTEXTS"][titles]
        for rule_name in rule_names:
            emit_rule(rule_name, grammar["RULES"][rule_name], True, titles) 
        emit(0, "\n\n")

    # <<<>>>
    if len(Emitted_Rules) > 0:
        emit_file_trailer()
    OUT.close()

def implementation_error(error):
    log_error(error)
    raise RuntimeError, error    # <<<>>>

def magic_with(element, count):
    rule = {}
    rule["TYPE"] = "with"
    rule["ELEMENT"] = element
    rule["ACTIONS"] = [reference_action(i) for i in range(count,0, -1)]
    return rule

def reference_action(i):
    action = {}
    action["TYPE"] = "reference"
    action["SLOT"] = i
    return action

def one_of(rule_names):
    rule = {}
    rule["TYPE"] = "alternatives"
    rule["CHOICES"] = [rule_ref(rule_name) for rule_name in rule_names]
    return rule

def rule_ref(rule_name):
    rule = {}
    rule["TYPE"] = "rule_reference"
    rule["NAME"] = rule_name
    return rule

def repeated_element(element, count):
    if count == 1:
        return slotted_element(element, count)
    rule = {}
    rule["TYPE"] = "sequence"
    rule["ELEMENTS"] = [slotted_element(element, count), 
                        optional_element(repeated_element(element, count - 1))]
    return rule

def slotted_element(element, slot):
    rule = {}
    rule["TYPE"] = "slot"
    rule["NUMBER"] = slot
    rule["ELEMENT"] = element
    return rule

def optional_element(element):
    rule = {}
    rule["TYPE"] = "optional"
    rule["ELEMENT"] = element
    return rule


# ---------------------------------------------------------------------------
# Emit dragonfly output

def emit_rule(rule_name, rule, top_level, titles):
    global Emitted_Rules
    if rule_name in Emitted_Rules:
        return
    Emitted_Rules.add(rule_name)
    # the next line emits as a side effect any rules we are dependent on:
    element_code = [code_for_element(rule)]
    rule_class = "ExportedRule" if top_level else "Rule"
    if top_level:
        element_code = [code_for_context(titles)] + element_code
    element_code = [make_string(rule_name)] + element_code
    rule_variable = "rule_" + rule_name
    rule_code = make_assignment(rule_variable, make_call(rule_class, element_code))
    emit_code(rule_code)
    if top_level:
        emit(0, "grammar.add_rule(" + rule_variable + ")\n")

  # this reuses the same variable so use the result immediately
def code_for_context(titles):
    context_variable = "context"
    executables = Grammar["EXECUTABLE"]
    high_priority = len(executables) > 0 or titles != ()
    text = context_variable + " = Context(executables=" + \
        make_python_list(executables) + ",titles=" + \
        make_python_list(titles) + \
        (",high_priority=True" if high_priority else "") + \
        (",invert_executables=True" if InvertExecutables else "") + \
        ")\n"
    emit(0, text)
    return make_variable(context_variable)

def make_python_list(strings):
    return "[" + ",".join('"' + make_safe_python_string(s) + '"' for s in strings) + "]"

def code_for_element(element):
    type = element["TYPE"]
    if type == "terminal":
        return make_call("Term", [make_string(element["TEXT"])])
    elif type == "dictation":
        return make_call("Dictation", [])
    elif type == "rule_reference":
        referenced = element["NAME"]
        emit_rule(referenced, Grammar["RULES"][referenced], False, None)
        return make_call("RuleRef", [make_variable("rule_" + referenced)])
    elif type == "optional":
        element_code = code_for_element(element["ELEMENT"])
        return make_call("Opt", [element_code])
    elif type == "alternatives":
        codes = [make_list([code_for_element(e) for e in element["CHOICES"]])]
        return make_call("Alt", codes)
    elif type == "sequence":
        codes = [make_list([code_for_element(e) for e in element["ELEMENTS"]])]
        return make_call("Seq", codes)
    elif type == "slot":
        element_code = code_for_element(element["ELEMENT"])
        return make_call("Slot", [element_code, make_integer(element["NUMBER"])])
    elif type == "with":
        element_code = code_for_element(element["ELEMENT"])
        actions_code = code_for_actions(element["ACTIONS"])
        return make_call("With", [element_code, actions_code])
    elif type == "without":
        element_code = code_for_element(element["ELEMENT"])
        return make_call("Without", [element_code])
    else:
        implementation_error("code_for_element: unknown element type: " + type)

def code_for_actions(actions):
    return make_list([code_for_action(action) for action in actions])

def code_for_action(action):
    type = action["TYPE"]
    if type == "text":
        return make_string(action["TEXT"])
    elif type == "reference":
        return make_call("Ref", [make_integer(action["SLOT"])])
    elif type == "call":
        return code_for_call(action)
    elif type == "catch":
        return code_for_catch(action)
    else:
        implementation_error("Unknown action type: '" + type + "'")

def code_for_call(call):
    call_type = call["CALLTYPE"]
    name_code = [make_string(call["NAME"])]
    module_code = []
    if "MODULE" in call.keys():
        module_code = [make_string(call["MODULE"])]
    argument_code = [code_for_actions(a) for a in call["ARGUMENTS"]]
    codes = module_code + name_code + argument_code
    return make_call(call_type_name(call_type), codes)

def call_type_name(call_type):
    if call_type == "dragon":
        return "DragonCall"
    elif call_type == "vocola":
        return "VocolaCall"
    elif call_type == "extension_routine":
        return "ExtRoutine"
    elif call_type == "extension_procedure":
        return "ExtProc"
    else:
        implementation_error("Unknown call type: '" + call_type + "'")

def code_for_catch(catch):
    body = code_for_actions(catch["ACTIONS"])
    return make_call("CatchAction", [make_string(catch["SPEC"]), 
                                     make_string(catch["FILE"]),  
                                     make_integer(catch["LINE"]), 
                                     body])


# ---------------------------------------------------------------------------
# Code for emitting pretty printed Python code

#
# These are used to generate *code*, which can be later pretty printed:
#

def make_variable(variable):
    return make_leaf(variable)

def make_integer(number):
    return make_leaf(str(number))

def make_string(text):
    return make_leaf('"' + make_safe_python_string(text) + '"')
    
def make_list(codes):
    return make_branch("[", "]", codes)

def make_call(name, codes):
    return make_branch(name + "(", ")", codes)

def make_assignment(variable, code):
    return add_prefix(variable + " = ", code)


#
# These are the underlying primitives used by the above
#

Indent = 2
Separator = ", "

def make_leaf(text):
    return (text, len(text), 0)

def make_branch(head_text, tail_text, codes):
    size = len(head_text) + len(tail_text)
    depth = 1
    if len(codes) > 0:
        depth = max(c[2] for c in codes) + 1
        size = size + len(Separator)*(len(codes)-1) + \
            sum(c[1] for c in codes)
    return ([head_text, tail_text, codes], size, depth)

def add_prefix(text, code):
    info, size, depth = code
    if isinstance(info, str):
        return (text + info, size + len(text), depth)
    head_text, tail_text, codes = info
    return ([text + head_text, tail_text, codes], size + len(text), depth)

def make_safe_python_string(text):
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace("\"", "\\\"")
    text = text.replace("\n", "\\n")
    return text


#
# Actual code for emitting
#

Wrap_column = 100

def emit_code(code, indent=0, trailer=""):
    #emit(0, flatten_code(code) + "\n")
    #return
    info, size, depth = code
    if isinstance(info, str) or indent*Indent + size < Wrap_column:
        emit(indent, flatten_code(code) +  trailer + "\n")
        return
    head_text, tail_text, codes = info
    emit(indent, head_text + "\n")
    for code in codes:
        emit_code(code, indent + 1, ",")
    emit(indent, tail_text +  trailer + "\n")

def flatten_code(code):
    info = code[0]
    if isinstance(info, str):
        return info
    head_text, tail_text, codes = info
    return head_text + Separator.join([flatten_code(c) for c in codes]) + tail_text

def emit(indent, text):
    global OUT
    OUT.write(' ' * (Indent * indent) + text)



# ---------------------------------------------------------------------------
# Pieces of the output Python file

def emit_file_header():
    global VocolaVersion, OUT
    from time import localtime, strftime

    now = strftime("%a %b %d %H:%M:%S %Y", localtime())
    print >>OUT, "# NatLink macro definitions for dragonfly" 
    print >>OUT, "# coding: Windows-1252"
    print >>OUT, "# Generated by vcl2py " + VocolaVersion + ", " + now
    print >>OUT, '''
from __future__ import print_function

import dragonfly

from vocola_dragonfly_runtime import *


#
# Our grammar's rules:
#

grammar = Grammar(__file__)


''',

def emit_file_trailer():
    print >>OUT, '''

grammar.load_grammar()
def unload():
    global grammar
    if grammar: grammar.unload_grammar()
    grammar = None
''',
