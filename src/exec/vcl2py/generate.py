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
    # print(unparse_grammar(grammar))
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


def generate_from_terms(terms):
    rule = {}
    rule["TYPE"] = "sequence"
    elements = []
    for term in terms:
        elements.append(generate_from_term(term))
    rule["ELEMENTS"] = elements
    return rule

def generate_from_term(term):
    if "OPTIONAL" in term.keys() and term["OPTIONAL"] and term["TYPE"] != "optionalterms":
        empty = {}
        empty["TYPE"] = "empty"
        rule = {}
        rule["TYPE"] = "alternatives"
        rule["CHOICES"] = [generate_terms(term["TERMS"]), empty]

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
        choices = []
        for command in commands:
            choices.append(generate_from_command(command))
        rule["CHOICES"] = choices
    elif type == "dictation":
        rule["TYPE"] = "dictation"
    elif type == "optionalterms":
        # print(repr(term))
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
        if number in Number_words.keys():
            number_text = Number_words[number]
        else:
            number_text = str(number)
        choices.append(generate_from_word(number_text))
    rule["CHOICES"] = choices
    return rule

def generate_from_command(command):
    return generate_from_terms(command["TERMS"])
