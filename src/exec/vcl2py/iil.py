import re

# Internal instruction language

# grammar:
#       EXECUTABLE    - Python list of names of executables restricted to or [] if not
#       MAX_COMMANDS  - maximum number of commands per utterance
#       CONTEXTS      - Python map from contexts (Python tuple of strings) to rule names
#                       (empty tuple means applies everywhere)
#       RULES         - Python map from rule names to named rules
#
# rule:
#    TYPE - empty/terminal/dictation/rule_reference/sequence/alternatives
#    empty:
#       ACTIONS    - Python list of actions
#    terminal:
#       TEXT    - text defining the terminal; can be multiple words
#       ACTIONS    - Python list of actions
#    dictation:
#    rule_reference:
#       NAME    - The rule name being referenced; must be defined in the grammar's RULES field
#    alternatives:
#       CHOICES    - Python list of alternatives, each a rule (need not be named)
#    sequence:
#       ELEMENTS    - Python list of elements making up the sequence, each a rule (need not be named)
#       ACTIONS    - Python list of actions


# ---------------------------------------------------------------------------
# Unparsing (for debugging and generating error messages)

def unparse_grammar(grammar):
    result = "grammar:\n"
    result += "  EXECUTABLE: " + ",".join(grammar["EXECUTABLE"]) + "\n"
    result += "  MAX_COMMANDS: " + str(grammar["MAX_COMMANDS"]) + "\n"
    result += "  CONTEXTS:\n" + unparse_contexts(grammar["CONTEXTS"])
    result += "  RULES:\n"
    for name, rule in sorted(grammar["RULES"].items(), key=_rule_ordering):
    	result += unparse_rule(name, rule)
    return result 

  # first come all rules that are #s in numerical order 
  # then everything else lexicographically
def _rule_ordering(x):
    x = x[0]
    if re.match(r'^[0-9]*$', x):
        return "A_" + str(int(x)+100000)
    return "B_" + x

def unparse_contexts(contexts):
    result = ""
    for context, rule_names in sorted(contexts.items()):
        result += unparse_context(context) + ":"
        for rule_name in rule_names:
            result += " <" + rule_name + ">"
        result += "\n"
    return result

def unparse_context(context):
    return "|".join(context)

def unparse_rule(name, rule):
    result = ""
    if name:
       result += "<" + name + "> ::= "
    return result +  unparse_element(rule) + "\n"

def unparse_element(element):
    type = element["TYPE"]
    if type == "empty":
        return "&EMPTY"
    elif type == "terminal":
        text = element["TEXT"]
        if re.match(r'^[a-zA-Z0-9_]*$', text):
            return text
        else:
            return "'" + text.replace("'", "''") + "'"
    elif type == "dictation":
        return "&DICTATION"
    elif type == "rule_reference":
        return "<" +  element["NAME"] + ">"
    elif type == "alternatives":
        inner = [unparse_element(choice) for choice in element["CHOICES"]]
        return "(" + " | ".join(inner) + ")"
    elif type == "sequence":
        inner = [unparse_element(choice) for choice in element["ELEMENTS"]]
        return "{" + " ".join(inner) + "}"
    else:
        return "&UNKNOWN:" + type
