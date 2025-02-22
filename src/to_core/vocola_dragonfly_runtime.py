###
### vocola_dragonfly_runtime.py - Code used by Vocola's generated
###                               Python code produced by the dragonfly backend
###

from __future__ import print_function

import dragonfly

from VocolaUtils import (VocolaRuntimeError, VocolaRuntimeAbort)
from vocola_common_runtime import *


##
## Basic element implementation using dragonfly
##

class Term:
    def __init__(self, terminal_text):
         self.terminal_text = terminal_text

    def to_dragonfly(self):
         return dragonfly.Literal(text=self.terminal_text.decode("Windows-1252"), 
                                  value=self.terminal_text)

class Dictation:
    def to_dragonfly(self):
         return dragonfly.Modifier(dragonfly.Dictation(format=False),
                                   lambda words: format_words(words))

class RuleRef:
    def __init__(self, rule):
         self.rule = rule

    def to_dragonfly(self):
         return dragonfly.RuleRef(rule=self.rule)


class Opt:
    def __init__(self, element):
         self.element = element

    def to_dragonfly(self):
         return dragonfly.Optional(child=self.element.to_dragonfly(),
                                   default=None)

class Alt:
    def __init__(self, alternatives):
         self.alternatives = alternatives

    def to_dragonfly(self):
         return dragonfly.Alternative(children=[alternative.to_dragonfly() 
                                                for alternative in self.alternatives])

class Seq:
    def __init__(self, elements):
         self.elements = elements

    def to_dragonfly(self):
         return dragonfly.Sequence(children=[element.to_dragonfly() for element in self.elements])

class Modifier:
    def __init__(self, element):
        self.element = element

    def transform(self, value):
        return value

    def to_dragonfly(self):
        return dragonfly.Modifier(self.element.to_dragonfly(), 
                                  lambda value: self.transform(value))


#
# Dealing with formatting dictation:  <<<>>>
#

def format_words(word_list):
    word_list = [word.encode('Windows-1252') for word in word_list]
    result = ""
    for word in word_list:
        # Convert to written form if necessary, e.g. "@\at-sign" --> "@"
        backslashPosition = str.find(word, "\\")
        if backslashPosition > 0:
            word = word[:backslashPosition]
        if result != "":
            result = result + " "
        result = result + word
    vlog(1, "    format_words: %s -> '%s'"  % (repr(word_list), result))
    return result

def format_words2(word_list):
    format_words(word_list)  # for print side effect
    word_list = [word.encode('Windows-1252') for word in word_list]
    try:
        from natlink import nsformat
    except ImportError:
        import nsformat
    state = [nsformat.flag_no_space_next]
    result, _new_state = nsformat.formatWords(word_list, state)
    vlog(1, "    format_words2: %s -> '%s'"  % (repr(word_list), result))
    return result



##
## Standard derived elements
##

class Slot(Modifier):
    def __init__(self, element, number):
        Modifier.__init__(self, element)
        self.number = number

    def transform(self, value):
        return (self.number, self.reduce_to_action(value))

    def reduce_to_action(self, value):
        actions = self.reduce_to_actions(value)
        return actions[0] if len(actions) > 0 else Text("")

    def reduce_to_actions(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [Text(value)]
        if isinstance(value, Action):
            return [value]
        if isinstance(value, list):
            result = []
            for v in value:
                result += self.reduce_to_actions(v)
            return result
        raise VocolaRuntimeError("Implementation error: " +
                                 "Slot element received unexpected value from sub element: " +
                                 repr(value))

class With(Modifier):
    def __init__(self, element, actions):
        Modifier.__init__(self, element)
        self.action = Prog(actions)

    def transform(self, value):
        return self.action.bind(self.get_bindings(value))

    def get_bindings(self, value):
        bindings = {}
        if isinstance(value, tuple):
            bindings[value[0]] = value[1]
        if isinstance(value, list):
            for v in value:
                b = self.get_bindings(v)
                bindings.update(b)
        return bindings

class Without(Modifier):
    def __init__(self, element):
        Modifier.__init__(self, element)

    def transform(self, value):
        return Join(self.reduce_to_actions(value))

    def reduce_to_actions(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [Text(value)]
        if isinstance(value, Action):
            return [value]
        if isinstance(value, list):
            result = []
            for v in value:
                result += self.reduce_to_actions(v)
            return result
        raise VocolaRuntimeError("Implementation error: Without element " + 
                                 "received unexpected value from sub element: " +
                                 repr(value))
        

##
## Rule implementation using Dragonfly
##

class BasicRule(dragonfly.Rule):
    def __init__(self, exported, name_, element_, context=None):
        dragonfly.Rule.__init__(self, name=name_, element=element_.to_dragonfly(), 
                                exported=exported, context=context)
        self.vocola_element = element_

    def get_element(self):
        return self.vocola_element

class Rule(BasicRule):
    def __init__(self, name_, element_):
        BasicRule.__init__(self, False, name_, element_)

class ExportedRule(BasicRule):
    def __init__(self, name_, context_, element_):
        BasicRule.__init__(self, True, name_, element_, 
                           context=context_.to_dragonfly())
        self.file = "unknown"

    def set_grammar(self, grammar):
        self.vocola_grammar = grammar
        self.file = grammar.get_file()

    def process_recognition(self, node):
        vlog(1, "\nRule " + self.name + " from " + self.file + ":")
        try:
            vlog(1, "    recognized: " + repr(node))
            action = node.value()
            vlog(2, "    ->  " + repr(action))
            text = action.eval(True, {}, "")
            vlog(1, "    resulting text is <" + text + ">")
            do_playString(text)
        except VocolaRuntimeAbort:
            vlog(1, "    command aborted")
        except Exception as e:
            vlog(1, "    Rule " + self.name + " threw exception: " + repr(e))
            import traceback
            traceback.print_exc(e)


##
## Context implementation using Dragonfly
##

class Context:
    def __init__(self, executables=[], invert_executables=False, titles=[], 
                 high_priority=False):
        self.executables = executables
        self.invert_executables = invert_executables
        self.titles = titles
        # currently dragonfly has no way of implementing this so ignore
        self.high_priority = high_priority

    def context_for_executables(self, executables):
        if len(executables) == 0:
            return dragonfly.AppContext()
        result = ~dragonfly.AppContext()
        for executable in executables:
            context = dragonfly.AppContext(executable=executable)
            result = result | context
        return result

    def context_for_titles(self, titles):
        if len(titles) == 0:
            return dragonfly.AppContext()
        result = ~dragonfly.AppContext()
        for title in titles:
            context = dragonfly.AppContext(title=title.decode('Windows-1252'))
            result = result | context
        return result

    def to_dragonfly(self):
        executables_context = self.context_for_executables(self.executables)
        titles_context = self.context_for_titles(self.titles)
        result = executables_context
        if self.invert_executables:
            result = ~result
        result = result & titles_context
        return result


##
## Grammar implementation using dragonfly
##

class Grammar:
    def __init__(self, file):
        self.file = file
        self.dragonfly_grammar = dragonfly.Grammar(file)

    def get_file(self):
        return self.file

    def load_grammar(self):
        vlog(3, "***** loading " + self.file + "...")
        self.dragonfly_grammar.load()

    def unload_grammar(self):
        vlog(3, "***** unloading " + self.file + "...")
        self.dragonfly_grammar.unload()

    def add_rule(self, rule):
        rule.set_grammar(self)
        self.dragonfly_grammar.add_rule(rule)
        vlog(3, "loaded from " + self.file + ": " + 
             repr(rule.get_element().to_dragonfly().gstring()))
