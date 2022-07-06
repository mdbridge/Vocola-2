import re
from vcl2py.ast import *
from vcl2py.log import *

def output(out_file, grammar, params):
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

    executables = grammar["EXECUTABLE"]
    if len(executables) == 0:
         # <<<>>>
        if re.match(r'.*(short|range).*', out_file):
            emit(0, "context = (~dragonfly.AppContext(executable='emacs')) & ~dragonfly.AppContext(executable='xwin')\n")
        else:
            emit(0, "context = dragonfly.AppContext()\n")
    else:
        # <<<>>>
        executable = executables[-1]
        emit(0, "context = dragonfly.AppContext(executable='" + executable + "')\n")
    # emit(0, 'context = dragonfly.AppContext(executable="emacs", title="yellow emacs")'+ "\n")


    emit(0, "grammar = dragonfly.Grammar('Test grammar', context=context)\n\n\n")


    global Emitted_Rules
    Emitted_Rules = set()

    # <<<>>>
    if () in grammar["CONTEXTS"].keys():
        rule_names = grammar["CONTEXTS"][()]
        grammar["RULES"]["0_all"] = one_of(rule_names)
        if maximum_commands == 1:
            grammar["CONTEXTS"][()] = ["0_all"]
        else:
            grammar["RULES"]["1_all"] = magic_with(repeated_element(rule_ref("0_all"), maximum_commands), maximum_commands)
            grammar["CONTEXTS"][()] = ["1_all"]

    # don't do title-specific contexts yet:
    if () in grammar["CONTEXTS"].keys():
        rule_names = grammar["CONTEXTS"][()]
        for rule_name in rule_names:
            emit_rule(rule_name, grammar["RULES"][rule_name], True) 

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
    rule["TYPE"] = "alternatives"
    rule["CHOICES"] = [element, empty_element()]
    return rule

def empty_element():
    empty = {}
    empty["TYPE"] = "empty"
    return empty


# ---------------------------------------------------------------------------
# Emit dragonfly output

def emit_rule(rule_name, rule, top_level):
    global Emitted_Rules
    if rule_name in Emitted_Rules:
        return
    Emitted_Rules.add(rule_name)
    # the next line emits as a side effect any rules we are dependent on:
    element_code = code_for_element(rule)
    class_ = "ExportedRule(__file__," if top_level else "Rule("
    emit(0, "rule_" + rule_name + " = " + class_ + '"' + rule_name + "\", " + element_code + ")\n")
    if top_level:
        emit(0, "grammar.add_rule(rule_" + rule_name + ")\n")

def code_for_element(element):
    type = element["TYPE"]
    if type == "empty":
        return "Empty()"
    elif type == "terminal":
        return "Term(\"" + make_safe_python_string(element["TEXT"]) + "\")"
    elif type == "dictation":
        return "Dictation()"
    elif type == "rule_reference":
        referenced = element["NAME"]
        emit_rule(referenced, Grammar["RULES"][referenced], False)
        return "RuleRef(rule_" + referenced + ")"
    elif type == "alternatives":
        elements = ", ".join([code_for_element(e) for e in element["CHOICES"]])
        return "Alt([" + elements + "])"
    elif type == "sequence":
        elements = ", ".join([code_for_element(e) for e in element["ELEMENTS"]])
        return "Seq([" + elements + "])"
    elif type == "slot":
        element_code = code_for_element(element["ELEMENT"])
        return "Slot(" + element_code + "," + str(element["NUMBER"]) + ")"
    elif type == "with":
        element_code = code_for_element(element["ELEMENT"])
        actions_code = code_for_actions(element["ACTIONS"])
        return "With(" + element_code + ",\n    " + actions_code + ")"
    elif type == "without":
        element_code = code_for_element(element["ELEMENT"])
        return "Without(" + element_code + ")"
    else:
        implementation_error("code_for_element: unknown element type: " + type)

def code_for_actions(actions):
    return "["+ ", ".join([code_for_action(action) for action in actions]) + "]"

def code_for_action(action):
    type = action["TYPE"]
    if type == "text":
        text = action["TEXT"]
        return '"' + make_safe_python_string(text) + '"'
    elif type == "reference":
        return "Ref(" + str(action["SLOT"]) + ")"
    elif type == "call":
        return code_for_call(action)
    else:
        implementation_error("Unknown action type: '" + type + "'")

def code_for_call(call):
    call_type = call["CALLTYPE"]
    result = call_type_name(call_type) + "("
    if "MODULE" in call.keys():
        result = result + '"' + make_safe_python_string(call["MODULE"]) + '",'
    result = result + '"' + make_safe_python_string(call["NAME"]) + '",' + \
        '[' + ",".join([code_for_actions(a) for a in call["ARGUMENTS"]]) + "])"
    return result

def call_type_name(call_type):
    if call_type == "dragon":
        return "DragonCall"
    elif call_type == "vocola":
        return "VocolaCall"
    elif call_type == "extension_routine":
        return "ExtensionRoutine"
    elif call_type == "extension_procedure":
        return "ExtensionProcedure"
    else:
        implementation_error("Unknown call type: '" + call_type + "'")

# ---------------------------------------------------------------------------
# Utilities used by "emit" methods

def emit(indent, text):
    global OUT
    OUT.write(' ' * (4 * indent) + text)

def make_safe_python_string(text):
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace("\"", "\\\"")
    text = text.replace("\n", "\\n")
    return text


# ---------------------------------------------------------------------------
# Pieces of the output Python file

def emit_file_header():
    global VocolaVersion, OUT
    from time import localtime, strftime

    now = strftime("%a %b %d %H:%M:%S %Y", localtime())
    print >>OUT, "# NatLink macro definitions for dragonfly" 
    print >>OUT, "# coding: latin-1"
    print >>OUT, "# Generated by vcl2py " + VocolaVersion + ", " + now
    print >>OUT, '''
from __future__ import print_function

import dragonfly

from vocola_dragonfly_runtime import *


#
# Our grammar's rules:
#

''',

def emit_file_trailer():
    print >>OUT, '''

print("***** loading" + __file__ + "...")
grammar.load()
def unload():
    global grammar
    print("***** unloading" + __file__ + "...")
    if grammar: grammar.unload()
    grammar = None
''',
