from vcl2py.log import *

def output(out_file, module_name, statements, definitions,
           file_empty, should_emit_dictation_support,
           extension_functions, params):
    try:
        out = open(out_file.replace("_vcl.py", ".vcl"), "w")
    except IOError, e:
        log_error("Unable to open output file '" + out_file + \
                  "' for writing: " + str(e))
        return

    #print unparse_statements(statements)
    print >>out, unparse_statements(statements)
        
    out.close()


def unparse_statements(statements):
    result = ""
    for statement in statements:
        type = statement["TYPE"]
        if type == "context" or type == "include" or type == "set":
            result += unparse_directive(statement)
        elif type == "definition":
            result += unparse_definition(statement)
        elif type == "function":
            #result += unparse_function_definition(statement)
            pass
        elif type == "command":
            result += unparse_command(statement, True) + ";\n"
    return result + "\n"

def unparse_directive(statement):
    type = statement["TYPE"]
    if type == "set":
        return "$set '" + statement["KEY"] + "' '" + statement["TEXT"] + "';\n"
    elif type == "context":
        return "|".join(statement["STRINGS"]) + ":\n"
    else:
        return statement["TYPE"] + ":  '" + statement["TEXT"] + "'\n"

def unparse_definition(statement):
    return "<" + statement["NAME"] + "> := " + \
        unparse_menu(statement["MENU"], True) + ";\n"

def unparse_function_definition(statement):
    result = statement["NAME"] + "(" + ",".join(statement["FORMALS"])
    result += ") := " + unparse_actions(statement["ACTIONS"])
    return result + ";\n"

def unparse_command(command, show_actions):
    result = unparse_terms(show_actions, command["TERMS"])
    if command.has_key("ACTIONS") and show_actions:
        #        result += " = " + unparse_actions(command["ACTIONS"])
        result += " = redacted"# + unparse_actions(command["ACTIONS"])
    return result

def unparse_terms(show_actions, terms):
    result = unparse_term(terms[0], show_actions)
    for term in terms[1:]:
        result += " " + unparse_term(term, show_actions)
    return result

def unparse_term(term, show_actions):
    if term["TYPE"] == "optionalterms":
        return "[" + unparse_terms(show_actions, term["TERMS"]) + "]"

    result = ""
    if term.get("OPTIONAL"): result +=  "["

#    if   term["TYPE"] == "word":      result += term["TEXT"]
    if   term["TYPE"] == "word":      result += "'" + term["TEXT"].replace("'","''") + "'"
    elif term["TYPE"] == "variable":  result += "<" + term["TEXT"] + ">"
    elif term["TYPE"] == "dictation": result += "<_anything>"
    elif term["TYPE"] == "menu":
        result += unparse_menu(term, show_actions)
    elif term["TYPE"] == "range":
        result += str(term["FROM"]) + ".." + str(term["TO"])

    if term.get("OPTIONAL"): result +=  "]"
    return result

def unparse_menu(menu, show_actions):
    commands = menu["COMMANDS"]
    result = "(" + unparse_command(commands[0], show_actions)
    for command in commands[1:]:
        result += " | " + unparse_command(command, show_actions)
    return result + ")"

def unparse_actions(actions):
    if len(actions) == 0: return ""  # bug fix <<<>>>
    result  = unparse_action(actions[0])
    for action in actions[1:]:
        result += " " + unparse_action(action)
    return result

def unparse_action(action):
    if   action["TYPE"] == "word":      return unparse_word(action)
    elif action["TYPE"] == "reference": return "$" + action["TEXT"]
    elif action["TYPE"] == "formalref": return "$" + action["TEXT"]
    elif action["TYPE"] == "call":
        result = action["TEXT"] + "("
        arguments = action["ARGUMENTS"]
        if len(arguments) > 0:
            result += unparse_argument(arguments[0])
            for argument in arguments[1:]:
                result += ", " + unparse_argument(argument)
        return result + ")"
    else:
        return "<UNKNOWN ACTION>"  # should never happen...

def unparse_word(action):
    word = action["TEXT"]
    word = word.replace("'", "''")

    return "'" + word + "'"

def unparse_argument(argument):
    return unparse_actions(argument)
