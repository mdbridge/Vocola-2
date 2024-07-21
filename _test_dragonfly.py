from dragonfly.all import Grammar, Sequence, Rule, Literal, Alternative
from VocolaUtils import *

class CommandSequence(Sequence):
    def __init__(self, terms, actions, name=None):
        Sequence.__init__(self, children=terms, name=name)
        self.actions = actions

    def value(self, node):
        values = super(CommandSequence, self).value(node)
        def thunk(list_buffer, functional):
            return self.actions(values, list_buffer, functional)
        return thunk

class VocolaRule(Rule):
    def __init__(self, name=None, element=None, context=None):
        Rule.__init__(self, name, element, context, False, True)

    def process_recognition(self, node):
        thunk = self.value(node)
        top_buffer = thunk("", False)
        #top_buffer = thunk("", True)
        do_flush(False, top_buffer)



grammar = Grammar("example grammar")


def actions_1(values, list_buffer, functional):
        try:
            list_buffer += 'fun'
            return list_buffer
        except Exception, e:
            handle_error('input.vcl', 7, '\'this is a test\'', e)
command_1 = CommandSequence([Literal('this is a test')], actions_1)

grammar.add_rule(VocolaRule("test1", command_1, None))


def actions_2(values, list_buffer, functional):
        try:
            list_buffer = do_flush(functional, list_buffer);
            call_Dragon('Beep', '', [])
            return list_buffer
        except Exception, e:
            handle_error('input.vcl', 9, '\'I want you to beep\'', e)
command_2 = CommandSequence([Literal('I want you to beep')], actions_2)

grammar.add_rule(VocolaRule("test2", command_2, None))


# 'red'
def actions_unnamed_1(values, list_buffer, functional):
    try:
        list_buffer += 'red'
        return list_buffer
    except Exception, e:
        handle_error('input.vcl', 3, '\'red\'', e)
command_unnamed_1 = CommandSequence([Literal('red')], actions_unnamed_1)

# 'blue'
def actions_unnamed_2(values, list_buffer, functional):
    try:
        list_buffer += '2'
        return list_buffer
    except Exception, e:
        handle_error('input.vcl', 3, '\'blue\'', e)
command_unnamed_2 = CommandSequence([Literal('blue')], actions_unnamed_2)

# 'green'
def actions_unnamed_3(values, list_buffer, functional):
    try:
        list_buffer += 'green'
        return list_buffer
    except Exception, e:
        handle_error('input.vcl', 3, '\'green\'', e)
command_unnamed_3 = CommandSequence([Literal('green')], actions_unnamed_3)

menu_list = Alternative([command_unnamed_1, command_unnamed_2, command_unnamed_3])


# 'try color' <list>
def actions_3(values, list_buffer, functional):
    print repr(values)
    try:
        list_buffer += '<'
        list_buffer = values[1](list_buffer,functional)
        list_buffer += '>'
        return list_buffer
    except Exception, e:
        handle_error('input.vcl', 10, '\'try color\' <list>', e)
command_3 = CommandSequence([Literal('try color'), menu_list], actions_3)

grammar.add_rule(VocolaRule("test3", command_3, None))


#command_foo = CommandSequence([Literal('extended'), Alternative(menu_list, command_3)], actions_3)
possibilities = Alternative([command_unnamed_1, command_unnamed_2, command_unnamed_3, command_3])

command_foo = CommandSequence([Literal('extended'), possibilities], actions_3)
grammar.add_rule(VocolaRule("testf", command_foo, None))



def e1_actions(values, list_buffer, functional):
    return "Hello: " + repr(values)

header = Literal("Superman")

e1 = CommandSequence([header, Literal("17")], e1_actions)
e2 = CommandSequence([header, Literal("water")], e1_actions)
them = Alternative([e1,e2])

def e3_actions(values, list_buffer, functional):
    return "Bye: " + repr(values[1]())


e3 = CommandSequence([header, them], e3_actions)


#rule = VocolaRule("test", e1, None)
rule = VocolaRule("test", Alternative([e1,e2,e3]), None)
grammar.add_rule(rule)


grammar.load()                                      # Load the grammar.
def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None
