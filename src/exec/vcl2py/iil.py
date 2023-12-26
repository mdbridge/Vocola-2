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
#    TYPE        - terminal/dictation/rule_reference/optional/
#                  sequence/alternatives/slot/with/without
#    terminal:
#       TEXT	 - text defining the terminal; can be multiple words
#    dictation:
#    rule_reference:
#       NAME	 - The rule name being referenced; must be defined in the grammar's 
#                  RULES field
#    optional:
#       ELEMENT  - A single element that may be omitted
#    alternatives:
#       CHOICES  - Python list of alternatives, each a rule (need not be named)
#    sequence:
#       ELEMENTS - Python list of elements making up the sequence, each a rule (need not be named)
#    slot:
#       ELEMENT  - A single element that defines the slot's grammar
#       NUMBER   - The number of the slot
#    with:
#       ELEMENT  - The single element that may provide slot(s)
#       ACTIONS  - Python list of actions
#         next 3 fields are only present for explicit commands; they
#         are not available for implicit commands like 1..10 under $set numbers:
#       SPEC     - short string describing the command grammar (e.g., "'up' 1..10")
#       FILE     - filename of file containing command
#       LINE     - line number of command's = or the separator following the command if none
#    without:
#       ELEMENT  - a single element
#
# action:
#    TYPE - text/reference/call
#    text:
#       TEXT      - the string value of the action
#    reference:
#       SLOT      - the number of the slot being referenced
#    call:
#       NAME      - the string name of the function being called
#       CALLTYPE  - dragon/vocola/extension_routine/extension_procedure
#       ARGUMENTS - list of lists of actions, to be passed in call
#       MODULE    - for extension types, the Python extension name

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
    if type == "terminal":
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
    elif type == "optional":
        return "[" + unparse_element(element["ELEMENT"]) + "]"
    elif type == "sequence":
        inner = [unparse_element(choice) for choice in element["ELEMENTS"]]
        return "{" + " ".join(inner) + "}"
    elif type == "slot":
        return "$" + str(element["NUMBER"]) + ":" + unparse_element(element["ELEMENT"])
    elif type == "with":
        return unparse_element(element["ELEMENT"]) + "=" + unparse_actions(element["ACTIONS"])
    elif type == "without":
        return unparse_element(element["ELEMENT"]) + "@"
    else:
        return "&UNKNOWN:" + type


def unparse_actions(actions):
     return ";".join([unparse_action(action) for action in actions])

def unparse_action(action):
    type = action["TYPE"]
    if type == "text":
        text = action["TEXT"]
        return '"' + text.replace('"', '""') + '"'
    elif type == "reference":
        return "$" + str(action["SLOT"])
    elif type == "call":
        module_prefix = ""
        if "MODULE" in action.keys():
            call_type = action["CALLTYPE"]
            module_prefix = action["MODULE"]
            if call_type == "extension_procedure":
                module_prefix = module_prefix + "!"
            else:
                module_prefix = module_prefix + ":"
        return module_prefix + action["NAME"] + \
            "(" +  ",".join([unparse_actions(a) for a in action["ARGUMENTS"]]) + ")"
    else:
        return "&UNKNOWN:" + type
