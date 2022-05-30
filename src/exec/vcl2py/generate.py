from vcl2py.ast import *
from vcl2py.iil import *
from vcl2py.log import *

def generate_grammar(statements, definitions, module_name, params_per_file):
    global Number_words
    Number_words = params_per_file["number_words"]

    grammar = {}
    grammar["EXECUTABLE"] = generate_executable_list(module_name)
    grammar["MAX_COMMANDS"] = params_per_file["maximum_commands"]
    contexts, rules = generate_rules(definitions, statements)
    grammar["RULES"] = rules
    grammar["CONTEXTS"] = contexts
    return grammar

def generate_executable_list(module_name):
    name = module_name
    if name.startswith("_"):
        return []
    executable_list = [name]
    while name.find("_") != -1:
        match = re.match(r'^(.+?)_+[^_]*$', name)
        if not match: break
        name = match.group(1)
        executable_list.append(name)
    return executable_list

def generate_rules(definitions, statements):
    contexts = {}
    rules = {}
    for name, definition in definitions.items():
        rule = generate_from_term(definition["MENU"])
        rules[definition["NAME"]] = rule       
    context = ()
    for statement in statements:
        if statement["TYPE"] == "command":
            rules[statement["NAME"]] = generate_from_command(statement)
            if context not in contexts.keys():
                contexts[context] = []
            contexts[context].append(statement["NAME"])
        elif statement["TYPE"] == "context":
            ast_context = statement["STRINGS"]
            if ast_context ==[""]:
                context = ()
            else:
                context = tuple(ast_context)
    return contexts, rules


def generate_from_command(command):
    element = generate_from_terms(command["TERMS"])
    if "ACTIONS" not in command.keys():
        return element
    ast_actions = command["ACTIONS"]
    rule = {}
    rule["TYPE"] = "act"
    rule["ELEMENT"] = element
    rule["ACTIONS"] = generate_from_actions(ast_actions)
    return rule
    
def generate_from_terms(terms):
    if len(terms) == 1:
        return generate_from_term(terms[0])
    rule = {}
    rule["TYPE"] = "sequence"
    rule["ELEMENTS"] = [generate_from_term(term) for term in terms]
    return rule

def generate_from_term(term):
    if "OPTIONAL" in term.keys() and term["OPTIONAL"] and term["TYPE"] != "optionalterms":
        empty = {}
        empty["TYPE"] = "empty"
        rule = {}
        rule["TYPE"] = "alternatives"
        rule["CHOICES"] = [generate_from_terms(term["TERMS"]), empty]
        return rule
    return generate_from_nonoptional_term(term)

def generate_from_nonoptional_term(term):
    rule = {}
    type = term["TYPE"]
    if type == "word":
        rule = generate_from_word(term["TEXT"])
    elif type == "variable":
        rule["TYPE"] = "rule_reference"
        rule["NAME"] = term["TEXT"]
    elif type == "range":
        rule = generate_from_range(term)
    elif type == "menu":
        commands = term["COMMANDS"]
        if len(commands) == 1:
            return generate_from_command(commands[0])
        rule["TYPE"] = "alternatives"
        rule["CHOICES"] = [generate_from_command(command) for command in commands]
    elif type == "dictation":
        rule["TYPE"] = "dictation"
    elif type == "optionalterms":
        rule["TYPE"] = "alternatives"
        empty = {}
        empty["TYPE"] = "empty"
        rule["CHOICES"] = [generate_from_terms(term["TERMS"]), empty]
    else:
        rule["TYPE"] = "unknown:" + term["TYPE"]
    return rule

def generate_from_word(text):
    rule = {}
    rule["TYPE"] = "terminal"
    rule["TEXT"] = text
    return rule
    
def generate_from_range(term):
    rule = {}
    rule["TYPE"] = "alternatives"
    choices = []
    for number in range(term["FROM"], term["TO"]):
        choices.append(generate_from_number(number))
    rule["CHOICES"] = choices
    return rule

def generate_from_number(number):
    if number not in Number_words.keys():
        return generate_from_word(str(number))
    number_text = Number_words[number]
    element = generate_from_word(number_text)
    rule = {}
    rule["TYPE"] = "act"
    rule["ELEMENT"] = element
    rule["ACTIONS"] = [generate_text_action(str(number))]
    return rule

    
def generate_from_actions(ast_actions):
    return [generate_from_action(ast_action) for ast_action in ast_actions]

def generate_from_action(ast_action):
    action = {}
    type = ast_action["TYPE"]
    if type == "word":
        return generate_text_action(ast_action["TEXT"])
    elif type == "reference":
        action["TYPE"] = "reference"
        action["SLOT"] = ast_action["TEXT"]
    elif type == "call":
        action["TYPE"] = "call"
        action["NAME"] = ast_action["TEXT"]
        action["CALLTYPE"] = ast_action["CALLTYPE"]
        action["ARGUMENTS"] = [generate_from_actions(a) for a in ast_action["ARGUMENTS"]]
    else:
        action["TYPE"] = "unknown:" + ast_action["TYPE"]
    return action

def generate_text_action(text):
    action = {}
    action["TYPE"] = "text"
    action["TEXT"] = text
    return action

