import re
from vcl2py.ast import *
from vcl2py.log import *

def output(out_file, grammar, params):
    global VocolaVersion

    VocolaVersion    = params["Vocola_version"]

    try:
        out = open(out_file, "w")
    except IOError, e:
        log_error("Unable to open output file '" + out_file + \
                  "' for writing: " + str(e))
        return

    global OUT
    OUT = out
    emit_file_header()

    global Grammar, Emitted_Rules
    Grammar = grammar
    Emitted_Rules = set()

    if () in grammar["CONTEXTS"].keys():
        rule_names = grammar["CONTEXTS"][()]
        for rule_name in rule_names:
            emit_rule(rule_name, grammar["RULES"][rule_name]) 

    emit_file_trailer()






    out.close()






def emit_rule(rule_name, rule):
    global Emitted_Rules
    if rule_name in Emitted_Rules:
        return
    Emitted_Rules.add(rule_name)
    element_code = code_for_element(rule)
    emit(0, "rule_" + rule_name + " = VocolaRule(\"" + rule_name + "\", " + element_code + ")\n")
    if re.match(r'^[0-9]*$', rule_name):
        emit(0, "grammar.add_rule(rule_" + rule_name + ")\n")

def code_for_element(element):
    type = element["TYPE"]
    if type == "empty":
        return "VocolaEmpty(None)"
    elif type == "terminal":
        return "VocolaTerminal(\"" + make_safe_python_string(element["TEXT"]) + \
            "\", \"" + make_safe_python_string(element["TEXT"]) + "\")"
            #"\", \"<<" + make_safe_python_string(element["TEXT"]) + ">>\")"
    elif type == "dictation":
        return "VocolaDictation()"
    elif type == "rule_reference":
        referenced = element["NAME"]
        emit_rule(referenced, Grammar["RULES"][referenced])
        return "VocolaRuleRef(rule_" + referenced + ")"
    elif type == "alternatives":
        elements = ", ".join([code_for_element(e) for e in element["CHOICES"]])
        return "VocolaAlternative([" + elements + "])"
    elif type == "sequence":
        elements = ", ".join([code_for_element(e) for e in element["ELEMENTS"]])
        return "VocolaSequence([" + elements + "], reduce_function)"
        #return "VocolaSequence([" + elements + "], echo_function)"
    else:
        implementation_error("Not all formal references transformed away")










def output2(out_file, module_name, statements, definitions,
           file_empty, should_emit_dictation_support,
           extension_functions, params):
    global NestedCallLevel
    global VocolaVersion, Should_emit_dictation_support
    global Module_name, Number_words, Definitions, Maximum_commands
    global Extension_functions

    Module_name                   = module_name
    Definitions                   = definitions
    Should_emit_dictation_support = should_emit_dictation_support
    Extension_functions           = extension_functions

    VocolaVersion    = params["Vocola_version"]
    Number_words     = params["number_words"]
    Maximum_commands = params["maximum_commands"]

    NestedCallLevel = 0

    try:
        out = open(out_file, "w")
    except IOError, e:
        log_error("Unable to open output file '" + out_file + \
                  "' for writing: " + str(e))
        return
        
    if not file_empty:
        emit_output(out, statements)
    else:
        # note that we write an empty output file for modification time comparisons
        log_warn("no commands in file.")
        
    out.close()


def implementation_error(error):
    log_error(error)
    raise RuntimeError, error    # <<<>>>



# ---------------------------------------------------------------------------
# Emit NatLink output

emitted_menus = {}



# term:
#    TYPE   - word/variable/range/menu/dictation/optionalterms
#    NUMBER - sequence number of this term
#    word:
#       TEXT     - text defining the word(s)
#       OPTIONAL - are these words optional?
#    variable:
#       TEXT     - name of variable being referenced
#       OPTIONAL - is this variable optional?
#    range:
#       FROM     - start number of range
#       TO       - end number of range
#    menu:
#       COMMANDS - list of "command" structures defining the menu
#    optionalterms:
#       TERMS   - list of "term" structures

def term_element(term):
    type = term["TYPE"]
    if type == "word":
        return "Literal('%s')" % (term["TEXT"])
    elif type == "variable":
        name = term["TEXT"]
        #return emit_menu_element(name)
        return "menu_" + name
    else:
        log_error("unable to handle element type " + type)
        return "UNKNOWN"
    
def terms_element_list(terms):
    return "[" + ", ".join([term_element(term) for term in terms]) + "]"

# statement: 
#    TYPE - command/definition/function/context/include/set
#    command:
#       NAME    - unique number
#       TERMS   - list of "term" structures
#       ACTIONS - list of "action" structures
#       LINE    - last line number of command if it is a top-level command
#       FILE    - filename of file containing command

unnamed_command_count = 0

def emit_command_element(command):
    global Variable_terms, OUT, unnamed_command_count

    terms = command["TERMS"]
    Variable_terms = get_variable_terms(terms) # used in emit_reference
    command_specification = unparse_terms(0, terms)
    if command.has_key("NAME"):
        name = command["NAME"]
    else:
        unnamed_command_count += 1
        name = "unnamed_" + str(unnamed_command_count)

    emit(0, "# ")
    print >>OUT, unparse_terms (0, terms),
    emit(0, "\n")
    emit(0, "def actions_%s(values, list_buffer, functional):\n" % (name))
    emit(1, "try:\n")

    if command.has_key("ACTIONS"):
        emit_actions("list_buffer", "functional", command["ACTIONS"], 2)
    else:
        emit(2, "list_buffer += '%s'\n" % (terms[0]["TEXT"]))
    emit(2, "return list_buffer\n")

    emit(1, "except Exception, e:\n")
    file = command["FILE"]
    emit(2, "handle_error('" + make_safe_python_string(file) \
            + "', " + str(command["LINE"]) + ", '"  \
            + make_safe_python_string(command_specification)  \
            + "', e)\n") 
    emit(0, "command_%s = CommandSequence(%s, actions_%s)\n" 
         % (name, terms_element_list(terms), name))
    emit(0, "\n")
    return "command_" + name


def emit_menu_element(name, menu):
    commands = menu["COMMANDS"]
    commands = flatten_menu(menu)
    elements = [emit_command_element(command) for command in commands]
    emit(0, "menu_"+name+" = Alternative([" + ", ".join(elements) + "])\n")
    emit(0, "\n")

def emit_output(out, statements):
    global Should_emit_dictation_support, OUT
    OUT = out
    emit_file_header()
    if Should_emit_dictation_support: emit_dictation_grammar()
    #    for statement in statements: 
    #        type = statement["TYPE"]
    #        if   type == "definition": emit_definition_grammar (statement)
    #        elif type == "command":    emit_command_grammar (statement)
    #    emit_sequence_and_context_code(statements)
    #    emit_number_words()
    for statement in statements:
        type = statement["TYPE"]
        if    type == "definition": emit_definition_actions (statement)
        if    type == "function":   pass
        elif type == "command":     emit_top_command_actions (statement)
    emit_file_trailer()

def emit_sequence_and_context_code(statements):
    # Build a list of context statements, and commands defined in each
    noop     = None
    context  = None
    contexts = []
    for statement in statements:
        type = statement["TYPE"]
        if type == "context":
            context = statement
            strings = context["STRINGS"]
            if strings[0] == "":   # <<<>>>
                # no-op context restriction
                if noop != None:
                    context = noop
                else:
                    noop = context
                    context["RULENAMES"] = []
                    contexts.append(context)
            else:
                context["RULENAMES"] = []
                contexts.append(context)
        elif type == "command":
            context["RULENAMES"].append(statement["NAME"])
    emit_sequence_rules(contexts)
    emit_file_middle()
    emit_context_definitions(contexts)
    emit_context_activations(contexts)

def emit_sequence_rules(contexts):
    global Maximum_commands
    # Emit rules allowing speaking a sequence of commands
    # (and add them to the RULENAMES for the context in question)
    number = 0
    any = ""
    for context in contexts:
        names = context["RULENAMES"]
        if len(names) == 0: continue
        number += 1
        suffix = ""
        rules = '<' + '>|<'.join(names) + '>'
        strings = context["STRINGS"]
        if strings[0] == "":
            emit(2, "<any> = " + rules + ";\n")
            any = "<any>|"
        else:
            suffix = "_set" + str(number)
            emit(2, "<any" + suffix + "> = " + any + "" + rules + ";\n")
        rule_name = "sequence" + suffix
        context["RULENAMES"] = [rule_name]
        emit(2, "<" + rule_name + "> exported = " +
                repeated_upto("<any" + suffix + ">", Maximum_commands) + ";\n")

def repeated_upto(spec, count):
    # Create grammar for a spec repeated 1 upto count times
    if count>99: return spec + "+"

    result = spec
    while count > 1:
        result = spec + " [" + result + "]"
        count = count - 1
    return result

def emit_context_definitions(contexts):
    global OUT
    # Emit a "rule set" definition containing all command names in this context
    number = 0
    for context in contexts:
        names = context["RULENAMES"]
        if len(names) == 0: continue
        number += 1
        first_name = names[0]
        emit(2, "self.ruleSet" + str(number) + " = ['" + first_name + "'")
        for name in names[1:]: print >>OUT, ",'" + name + "'"
        emit(0, "]\n")

def emit_context_activations(contexts):
    global Module_name
    app = Module_name
    module_is_global = (app.startswith("_"))
    #emit(2, "self.activateAll()\n") if module_is_global;
    emit(0, "\n    def gotBegin(self,moduleInfo):\n")
    if module_is_global:
        emit(2, "window = moduleInfo[2]\n")
    else:
        emit(2, "# Return if wrong application\n")
        executable = app
        emit(2, "window = matchWindow(moduleInfo,'" + executable + "','')\n")
        while executable.find("_") != -1:
            match = re.match(r'^(.+?)_+[^_]*$', executable)
            if not match: break
            executable = match.group(1)
            emit(2, "if not window: window = matchWindow(moduleInfo,'" + \
                    executable + "','')\n")
        emit(2, "if not window: return None\n")
    emit(2, "self.firstWord = 0\n")
    emit(2, "# Return if same window and title as before\n")
    emit(2, "if moduleInfo == self.currentModule: return None\n")
    emit(2, "self.currentModule = moduleInfo\n\n")
    emit(2, "self.deactivateAll()\n")
    emit(2, "title = string.lower(moduleInfo[1])\n")

    # Emit code to activate the context's commands if one of the context
    # strings matches the current window
    number = 0
    for context in contexts:
        if len(context["RULENAMES"]) == 0: continue
        number += 1
        targets = context["STRINGS"]
        targets = [make_safe_python_string(target) for target in targets]
        tests = " or ".join(["string.find(title,'" + target + "') >= 0" for target in targets])
        emit(2, "if " + tests + ":\n")
        emit(3, "for rule in self.ruleSet" + str(number) + ":\n")
        if module_is_global: emit(4, "self.activate(rule)\n")
        else:
            emit(4, "try:\n")
            emit(5, "self.activate(rule,window)\n")
            emit(4, "except natlink.BadWindow:\n")
            emit(5, "pass\n")
    emit(0, "\n")

#        if (not $module_is_global) {
#            emit(3, "    self.activate(rule,window)\n");
#        } else {
#            emit(3, "    if rule not in self.activeRules:\n");
#            emit(3, "        self.activate(rule,window)\n");
#            emit(2, "else:\n");
#            emit(3, "for rule in self.ruleSet$number:\n");
#            emit(3, "    if rule in self.activeRules:\n");
#            emit(3, "        self.deactivate(rule,window)\n");
#        }

def emit_dictation_grammar():
    emit(2, "<dgndictation> imported;\n")

def emit_definition_grammar(definition):
    emit(2, "<" + definition["NAME"] + "> = ")
    emit_menu_grammar (definition["MENU"]["COMMANDS"])
    emit(0, ";\n")

def emit_command_grammar(command):
    inline_a_term_if_nothing_concrete(command)
    (first, last) = find_terms_for_main_rule(command)
    terms = command["TERMS"]
    main_terms = terms[first:last+1]
    name = command["NAME"]
    name_a = name + "a"
    name_b = name + "b"
    if first > 0: main_terms = [create_variable_node(name_a)] + main_terms
    if last < len(terms)-1: main_terms.append(create_variable_node(name_b))
    emit_rule(command["NAME"], "", main_terms)
    if first > 0: emit_rule(name_a, "", terms[0:first])
    if last < len(terms)-1: emit_rule(name_b, "", terms[last+1:])

# def emit_rule(name, exported, terms):
#     emit(2, "<" + name + ">" + exported + " = ")
#     emit_command_terms(terms)
#     emit(0, ";\n")

def emit_command_terms(terms):
    for term in terms:
        if term.get("OPTIONAL", False): emit(0, "[ ")
        if term["TYPE"] == "word":
            word = term["TEXT"].replace("\\", "\\\\")
            if word.find("'") != -1: emit(0, '"' + word + '" ')
            else:               emit(0, "'" + word + "' ")
        elif term["TYPE"] == "dictation": emit(0, "<dgndictation> ")
        elif term["TYPE"] == "variable":  emit_variable_term(term)
        elif term["TYPE"] == "range":     emit_range_grammar(term)
        elif term["TYPE"] == "menu":
            emit(0, "(")
            emit_menu_grammar(term["COMMANDS"])
            emit(0, ") ")
        if term.get("OPTIONAL", False): emit(0, "] ")

def emit_variable_term(term):
    text = term["TEXT"]
    emit(0, "<" + text + "> ")

def emit_menu_grammar(commands):
    emit_command_terms(commands[0]["TERMS"])
    for command in commands[1:]:
        emit(0, "| ")
        emit_command_terms(command["TERMS"])

def emit_range_grammar(range_term):
    i  = range_term["FROM"]
    to = range_term["TO"]
    emit(0, "(" + emit_number_word(i))
    for i in range(i+1,to+1):
        emit(0, " | " + emit_number_word(i))
    emit(0, ") ")

def emit_number_word(i):
    global Number_words
    if Number_words.has_key(i):
        return "'" + Number_words[i] + "'"
    return str(i)

def emit_number_words():
    global Number_words
    emit(1, "def convert_number_word(self, word):\n")

    if len(Number_words) == 0:
        emit(2, "return word\n\n")
        return
    elif_keyword = "if  "
    numbers = Number_words.keys()
    numbers.sort()
    for number in numbers:
        emit(2, elif_keyword + " word == '" + Number_words[number]+ "':\n")
        emit(3, "return '" + str(number) + "'\n")
        elif_keyword = "elif"
    emit(2, "else:\n")
    emit(3, "return word\n\n")

def emit_definition_actions(definition):
    emit_menu_element(definition["NAME"], definition["MENU"])
    return
    emit(1,
         "def get_" + definition["NAME"] + "(self, list_buffer, functional, word):\n")
    emit_menu_actions("list_buffer", "functional", definition["MENU"], 2)
    emit(2, "return list_buffer\n\n")

def emit_top_command_actions(command):
    global Variable_terms, OUT

    emit_command_element(command)
    name = command["NAME"]
    emit(0, "grammar.add_rule(VocolaRule('%s', command_%s, None))\n" % (name, name))
    emit(0, "\n")
    return

    terms = command["TERMS"]
    nterms = len(terms)
    function = "gotResults_" + command["NAME"]
    Variable_terms = get_variable_terms(terms) # used in emit_reference

    command_specification = unparse_terms(0, terms)

    emit(1, "# ")
    print >>OUT, unparse_terms (0, terms),
    emit(0, "\n")
    emit(1, "def " + function + "(self, words, fullResults):\n")
    emit(2, "if self.firstWord<0:\n")
    emit(3, "return\n")
    emit_optional_term_fixup(terms)
    emit(2, "try:\n")
    emit(3, "top_buffer = ''\n")
    emit_actions("top_buffer", "False", command["ACTIONS"], 3)
    emit_flush("top_buffer", "False", 3)
    emit(3, "self.firstWord += " + str(nterms) + "\n")

    # If repeating a command with no <variable> terms (e.g. "Scratch That
    # Scratch That"), our gotResults function will be called only once, with
    # all recognized words. Recurse!
    if not has_variable_term(terms):
        emit(3, "if len(words) > " + str(nterms) + ": self." + function + \
                "(words[" + str(nterms) + ":], fullResults)\n")
    emit(2, "except Exception, e:\n")
    file = command["FILE"]
    emit(3, "handle_error('" + make_safe_python_string(file) +
            "', " + str(command["LINE"]) + ", '" +
            make_safe_python_string(command_specification) +
            "', e)\n")
    emit(3, "self.firstWord = -1\n")
    emit(0, "\n")

def emit_flush(buffer, functional, indent):
    emit(indent, buffer + " = do_flush(" + functional + ", " + buffer + ");\n")

def has_variable_term(unnamed):
    for term in unnamed:
        if term["TYPE"] == "variable" or term["TYPE"] == "dictation": return 1
    return 0

# Our indexing into the "fullResults" array assumes all optional terms were
# spoken.  So we emit code to insert a dummy entry for each optional word
# that was not spoken.  (The strategy used could fail in the uncommon case
# where an optional word is followed by an identical required word.)

def emit_optional_term_fixup(unnamed):
    for term in unnamed:
        index = term["NUMBER"]
        if term.get("OPTIONAL", False):
            text = term["TEXT"]
            emit(2, "opt = " + str(index) + " + self.firstWord\n")
            emit(2, "if opt >= len(fullResults) or fullResults[opt][0] != '" + text + "':\n")
            emit(3, "fullResults.insert(opt, 'dummy')\n")
        elif term["TYPE"] == "dictation":
            emit(2, "fullResults = combineDictationWords(fullResults)\n")
            emit(2, "opt = " + str(index) + " + self.firstWord\n")
            emit(2, "if opt >= len(fullResults) or fullResults[opt][1] != 'converted dgndictation':\n")
            emit(3, "fullResults.insert(opt, ['', 'converted dgndictation'])\n")

def emit_actions(buffer, functional, actions, indent):
    for action in actions:
        type = action["TYPE"]
        if type == "reference":
            emit_reference(buffer, functional, action, indent)
        elif type == "formalref":
            implementation_error("Not all formal references transformed away")
        elif type == "word":
            safe_text = make_safe_python_string(action["TEXT"])
            emit(indent, buffer + " += '" + safe_text + "'\n")
        elif type == "call":
            emit_call(buffer, functional, action, indent)
        else:
            implementation_error("Unknown action type: '" + type + "'")

def emit_reference(buffer, functional, action, indent):
    global Variable_terms
    reference_number = int(action["TEXT"]) - 1
    variable         = Variable_terms[reference_number]
    term_number      = variable["NUMBER"]
    emit(indent, buffer + " = values[" + str(term_number) + "]("+buffer+","+functional+")\n")

def emit_menu_actions(buffer, functional, menu, indent):
    if not menu_has_actions(menu):
        if menu_is_range(menu):
            emit(indent, buffer + " += self.convert_number_word(word)\n")
        else:
            emit(indent, buffer + " += word\n")
    else:
        commands = flatten_menu(menu)
        if_keyword = "if"
        for command in commands:
            text = command["TERMS"][0]["TEXT"]
            text = text.replace("\\", "\\\\")
            text = text.replace("'", "\\'")
            emit(indent, if_keyword + " word == '" + text + "':\n")
            if command.has_key("ACTIONS"):
                if len(command["ACTIONS"]) != 0:
                    emit_actions(buffer, functional,
                                 command["ACTIONS"], indent+1)
                else:
                    emit(indent+1, "pass  # no actions\n")
            else:
                emit(indent+1, buffer + " += '" + text + "'\n")
            if_keyword = "elif"

def emit_call(buffer, functional, call, indent):
    callType = call["CALLTYPE"]
    begin_nested_call()
    if   callType == "dragon":
        emit_dragon_call(buffer, functional, call, indent)
    elif callType == "extension":
        emit_extension_call(buffer, functional, call, indent)
    elif callType == "user"     :
        implementation_error("No user function call should be present here!")
    elif callType == "vocola":
        callName = call["TEXT"]
        if    callName == "Eval":
            implementation_error("Eval not transformed away")
        elif callName == "EvalTemplate":
            emit_call_eval_template(buffer, functional, call, indent)
        elif callName == "If":
            emit_call_if(buffer, functional, call, indent)
        elif callName == "Repeat":
            emit_call_repeat(buffer, functional, call, indent)
        elif callName == "Unimacro":
            emit_call_Unimacro(buffer, functional, call, indent)
        elif callName == "When":
            emit_call_when(buffer, functional, call, indent)
        else: implementation_error("Unknown Vocola function: '" + callName + "'")
    else: implementation_error("Unknown function call type: '" + callType + "'")
    end_nested_call()

def begin_nested_call():
    global NestedCallLevel
    NestedCallLevel += 1

def end_nested_call():
    global NestedCallLevel
    NestedCallLevel -= 1

def get_nested_buffer_name(root):
    global NestedCallLevel
    if NestedCallLevel == 1:
        return root
    else:
        return root + str(NestedCallLevel)

def emit_call_repeat(buffer, functional, call, indent):
    arguments = call["ARGUMENTS"]

    argument_buffer = get_nested_buffer_name("limit")
    emit(indent, argument_buffer + " = ''\n")
    emit_actions(argument_buffer, "True", arguments[0], indent)
    emit(indent, "for i in range(to_long(" + argument_buffer + ")):\n")
    emit_actions(buffer, functional, arguments[1], indent+1)

def emit_call_if(buffer, functional, call, indent):
    arguments = call["ARGUMENTS"]

    argument_buffer = get_nested_buffer_name("conditional_value")
    emit(indent, argument_buffer + " = ''\n")
    emit_actions(argument_buffer, "True", arguments[0], indent)
    emit(indent, "if " + argument_buffer + ".lower() == \"true\":\n")
    emit_actions(buffer, functional, arguments[1], indent+1)
    if len(arguments)>2:
        emit(indent, "else:\n")
        emit_actions(buffer, functional, arguments[2], indent+1)

def emit_call_when(buffer, functional, call, indent):
    arguments = call["ARGUMENTS"]

    argument_buffer = get_nested_buffer_name("when_value")
    emit(indent, argument_buffer + " = ''\n")
    emit_actions(argument_buffer, "True", arguments[0], indent)
    emit(indent, "if " + argument_buffer + " != \"\":\n")
    emit_actions(buffer, functional, arguments[1], indent+1)
    if len(arguments)>2:
        emit(indent, "else:\n")
        emit_actions(buffer, functional, arguments[2], indent+1)

def emit_arguments(call, name, indent):
    arguments = ""

    i=0
    for argument in call["ARGUMENTS"]:
        if i != 0:  arguments += ", "
        i += 1
        argument_buffer = get_nested_buffer_name(name) + "_arg" + str(i)
        emit(indent, argument_buffer + " = ''\n")
        emit_actions(argument_buffer, "True", argument, indent)
        arguments += argument_buffer
    return arguments

def emit_dragon_call(buffer, functional, call, indent):
    callName  = call["TEXT"]
    argumentTypes = call["ARGTYPES"]

    emit_flush(buffer, functional, indent)
    arguments = emit_arguments(call, "dragon", indent)
    emit(indent,
         "call_Dragon('" + callName + "', '" + argumentTypes + "', [" + arguments + "])\n")

def emit_extension_call(buffer, functional, call, indent):
    global Extension_functions
    callName      = call["TEXT"]
    callFormals   = Extension_functions[callName]
    needsFlushing = callFormals[2]
    import_name   = callFormals[3]
    function_name = callFormals[4]

    if needsFlushing:  emit_flush(buffer, functional, indent)
    arguments = emit_arguments(call, "extension", indent)
    emit(indent, "import " + import_name + "\n")
    if needsFlushing:
        emit(indent, function_name + "(" + arguments + ")\n")
    else:
        emit(indent, buffer + " += str(" + function_name + "(" + arguments + "))\n")

def emit_call_eval_template(buffer, functional, call, indent):
    arguments = emit_arguments(call, "eval_template", indent)
    emit(indent, buffer + " += eval_template(" + arguments + ")\n")

def emit_call_Unimacro(buffer, functional, call, indent):
    emit_flush(buffer, functional, indent)
    arguments = emit_arguments(call, "unimacro", indent)
    emit(indent, "call_Unimacro(" + arguments + ")\n")

# ---------------------------------------------------------------------------
# Utilities for transforming command terms into NatLink rules
#
# For each Vocola command, we define a NatLink rule and an associated
# "gotResults" function. When the command is spoken, we want the gotResults
# function to be called exactly once. But life is difficult -- NatLink calls a
# gotResults function once for each contiguous sequence of spoken words
# specifically present in the associated rule. There are two problems:
#
# 1) If a rule contains only references to other rules, it won't be called
#
# We solve this by "inlining" variables (replacing a variable term with the
# variable's definition) until the command is "concrete" (all branches contain
# a non-optional word).
#
# 2) If a rule is "split" (e.g. "Kill <n> Words") it will be called twice
#
# We solve this by generating two rules, e.g.
#    <1> exported = 'Kill' <n> <1a> ;
#    <1a> = 'Words' ;

def find_terms_for_main_rule(command):
    # Create a "variability profile" summarizing whether each term is
    # concrete (c), variable (v), or optional (o). For example, the
    # profile of "[One] Word <direction>" would be "ocv". (Menus are
    # assumed concrete, and dictation variables are treated like
    # normal variables.)

    pattern = ""
    for term in command["TERMS"]:
        if term["TYPE"] == "variable" or term["TYPE"] == "dictation":
            pattern += "v"
        elif term.get("OPTIONAL", False):
            pattern += "o"
        else:
            pattern += "c"
    # Identify terms to use for main rule.
    # We might not start with the first term. For example:
    #     [Move] <n> Left  -->  "Left" is the first term to use
    # We might not end with the last term. For example:
    #     Kill <n> Words   -->  "Kill" is the last term to use
    # And in this combined example, our terms would be "Left and Kill"
    #     [Move] <n> Left and Kill <n> Words

    match = re.match(r'v*o+v[ov]*c', pattern)
    if match:
        first = match.end(0)-1
    else:
        first = 0

    match = re.match(r'([ov]*c[co]*)v+[co]+', pattern)
    if match:
        last = match.end(1)-1
    else:
        last = len(pattern)-1

    return (first, last)

def inline_a_term_if_nothing_concrete(command):
    while not command_has_a_concrete_term(command):
        inline_a_term(command)

def command_has_a_concrete_term(command):
    for term in command["TERMS"]:
        if term_is_concrete(term): return True
    return False

def term_is_concrete(term):
    type = term["TYPE"]
    if   type == "menu":                            return True
    elif type == "variable" or type == "dictation": return False
    else: return not term["OPTIONAL"]

def inline_a_term(unnamed):
    global Definitions
    terms = unnamed["TERMS"]

    # Find the array index of the first non-optional term
    index = 0
    while (index < terms) and (terms[index]["OPTIONAL"] or terms[index]["TYPE"] == "dictation"): index += 1

    type = terms[index]["TYPE"]
    number = terms[index]["NUMBER"]
    if type == "variable":
        variable_name = terms[index]["TEXT"]
        #print "inlining variable $variable_name\n";
        definition = Definitions[variable_name]
        terms[index] = definition["MENU"]
        terms[index]["NUMBER"] = number
    elif type == "menu":
        for command in terms[index]["COMMANDS"]:
            inline_a_term(command)
    else: implementation_error("Inlining term of type '" + type + "'")

# ---------------------------------------------------------------------------
# Utilities used by "emit" methods

def emit(indent, text):
    global OUT
    OUT.write(' ' * (4 * indent) + text)

def menu_has_actions(menu):
    for command in menu["COMMANDS"]:
        if command.has_key("ACTIONS"): return True
        for term in command["TERMS"]:
            if term["TYPE"] == "menu" and menu_has_actions(term): return True
    return False

def menu_is_range(menu):  # verified menu => can contain only 1 range as a 1st term
    commands = menu["COMMANDS"]
    for command in commands:
        terms = command["TERMS"]
        type = terms[0]["TYPE"]
        if type == "menu" and menu_is_range(terms[0]):  return True
        if type == "range":  return True
    return False

# To emit actions for a menu, build a flat list of (canonicalized) commands:
#     - recursively extract commands from nested menus
#     - distribute actions, i.e. (day|days)=d --> (day=d|days=d)
# Note that error checking happened during parsing, in verify_referenced_menu

def flatten_menu(menu, actions_to_distribute=[]):
    new_commands = []
    for command in menu["COMMANDS"]:
        if command.has_key("ACTIONS"): new_actions = command["ACTIONS"]
        else:                          new_actions = actions_to_distribute
        terms = command["TERMS"]
        type = terms[0]["TYPE"]
        if type == "word":
            if new_actions: command["ACTIONS"] = new_actions
            new_commands.append(command)
        elif type == "menu":
            commands = flatten_menu (terms[0], new_actions)
            new_commands.extend(commands)
    return new_commands

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
from dragonfly import (
    Alternative, 
    AppContext,
    BasicRule, 
    Dictation,
    Empty, 
    Grammar,
    Impossible, 
    Literal, 
    Modifier, 
    Optional,
    RuleRef, 
    Sequence, 
)

def format_words(word_list):
    word_list = [word.encode('Windows-1252') for word in word_list]
    format_words2(word_list)  # for print side effect
    import nsformat
    state = [nsformat.flag_no_space_next]
    result, _new_state = nsformat.formatWords(word_list, state)
    print("format_words: %s -> '%s'"  % (repr(word_list), result))
    return result

def format_words2(word_list):
    result = ""
    for word in word_list:
        # Convert to written form if necessary, e.g. "@\at-sign" --> "@"
        backslashPosition = str.find(word, "\\\\")
        if backslashPosition > 0:
            word = word[:backslashPosition]
        if result != "":
            result = result + " "
        result = result + word
    print("format_words2: %s -> '%s'"  % (repr(word_list), result))
    return result


#
# Elements
#

class VocolaEmpty:
    def __init__(self, value):
         self.value = value

    def to_dragonfly(self):
        #         return Empty(value=self.value)
        #         return Optional(Impossible(), default=self.value)
         return Modifier(Optional(Impossible(), default=self.value),
                         lambda value: value if value else self.value)

class VocolaTerminal:
    def __init__(self, terminal, value):
         self.terminal = terminal
         self.value = value

    def to_dragonfly(self):
         return Literal(text=self.terminal, value=self.value)

class VocolaDictation:
    def to_dragonfly(self):
         return Modifier(Dictation(format=False),
                         lambda words: format_words(words))

class VocolaRuleRef:
    def __init__(self, rule):
         self.rule = rule

    def to_dragonfly(self):
         return RuleRef(rule=self.rule)

class VocolaAlternative:
    def __init__(self, alternatives):
         self.alternatives = alternatives

    def to_dragonfly(self):
         return Alternative(children=[alternative.to_dragonfly() for alternative in self.alternatives])

class VocolaSequence:
    def __init__(self, elements, value_function):
         self.elements = elements
         self.value_function = value_function

    def to_dragonfly(self):
         return Modifier(Sequence(children=[element.to_dragonfly() for element in self.elements]), 
                         lambda values: self.value_function(values))

#
# Rules
#

class VocolaRule(Rule):
    def __init__(self, name_, element_):
        Rule.__init__(self, name=name_, element=element_.to_dragonfly())
        print(repr(element_.to_dragonfly().gstring()))

    def process_recognition(self, node):
        try:
            print(self.name + " got result " + repr(node.value()))
        except Exception as e:
            print(repr(e))


context = AppContext(executable="emacs", title="yellow emacs")
grammar = Grammar("Test grammar", context=context)

def echo_function(x):
    print("seq: " + repr(x))
    return x

def reduce_function(words):
    words = [w for w in words if w is not None]
    if len(words)>0:
       return " ".join(words)
    else:
       return None
''',

def emit_file_middle():
    print >>OUT, '''    """
    
    def initialize(self):
        self.load(self.gramSpec)
        self.currentModule = ("","",0)
''',

def emit_file_trailer():
    print >>OUT, '''

print("***** loading...")
grammar.load()
def unload():
    global grammar
    print("***** unloading...")
    if grammar: grammar.unload()
    grammar = None
''',

