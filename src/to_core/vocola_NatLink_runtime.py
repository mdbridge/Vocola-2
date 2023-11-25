###
### vocola_NatLink_runtime.py - Code used by Vocola's generated
###                             Python code produced by the NatLink backend
###

from __future__ import print_function

import os, os.path

try:
    from natlink.natlinkutils import *
except ImportError:
    from natlinkutils import *

from VocolaUtils import (VocolaRuntimeError)
from vocola_common_runtime import *


##
## Basic element implementation using NatLink
##

class Element:
    def get_dependent_rules(self):
        return []

    def outer_parse(self, words, offset_):
        #print("  trying to parse " + repr(words[offset_:]))
        return self.parse(words, offset_)

    def parse(self, words, offset_):
        for offset, value in self.inner_parse(words, offset_):
            #print("    ", self.to_NatLink_grammar_element(), ":", repr(words[offset_:offset]), " -> ", repr(value))
            yield offset, value
        #print("done parsing: ", self.to_NatLink_grammar_element(), ":", repr(words[offset_:]))

    def inner_parse(self, words, offset_):
        return


class Term(Element):
    def __init__(self, terminal_text):
         self.terminal_text = terminal_text

    def to_NatLink_grammar_element(self):
        word = self.terminal_text
        if not "'" in word:
            return "'" + word + "'"
        else:
            return '"' + word + '"'

    def inner_parse(self, words, offset_):
        if offset_ >= len(words):
            return
        if words[offset_][0] == self.terminal_text:
            yield offset_ + 1, self.terminal_text

def make_safe_python_string(text):
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace("\"", "\\\"")
    text = text.replace("\n", "\\n")
    return text

class Dictation(Element):
    def to_NatLink_grammar_element(self):
        return "<dgndictation>"

    def get_dependent_rules(self):
        return ["dgndictation"]

    def inner_parse(self, words, offset_):
        offset = offset_
        value = []
        while offset < len(words):
            if words[offset][1] != 'dgndictation':
                break
            value.append(words[offset][0])
            offset += 1
        if value != []:
            yield offset, format_words(value)

class RuleRef(Element):
    def __init__(self, rule):
         self.rule = rule

    def get_dependent_rules(self):
        return [self.rule]

    def to_NatLink_grammar_element(self):
        return "<" + self.rule.get_name() + ">"

    def inner_parse(self, words, offset_):
        return self.rule.get_element().parse(words, offset_)
        

class Opt(Element):
    def __init__(self, element):
         self.element = element

    def get_dependent_rules(self):
        return self.element.get_dependent_rules()

    def to_NatLink_grammar_element(self):
        return "[" + self.element.to_NatLink_grammar_element() + "]"

    def inner_parse(self, words, offset_):
        for offset, value in self.element.parse(words, offset_):
            yield offset, value
        yield offset_, None

class Alt(Element):
    def __init__(self, alternatives):
         self.alternatives = alternatives

    def get_dependent_rules(self):
        result = []
        for alternative in self.alternatives:
            result += alternative.get_dependent_rules()
        return result

    def to_NatLink_grammar_element(self):
        return "(" + " | ".join(c.to_NatLink_grammar_element() for c in self.alternatives) \
            + ")"

    def inner_parse(self, words, offset_):
        for alternative in self.alternatives:
            for offset, value in alternative.parse(words, offset_):
                yield offset, value

class Seq(Element):
    def __init__(self, elements):
         self.elements = elements

    def get_dependent_rules(self):
        result = []
        for element in self.elements:
            result += element.get_dependent_rules()
        return result

    def to_NatLink_grammar_element(self):
        return " ".join(c.to_NatLink_grammar_element() for c in self.elements)

    def inner_parse(self, words, offset_):
        return self.inner_parse_helper(self.elements, words, offset_)


    def inner_parse_helper(self, remaining_elements, words, offset_):
        if len(remaining_elements) == 0:
            yield offset_, []
            return
        first_element = remaining_elements[0]
        remaining_elements = remaining_elements[1:]
        for offset, value in first_element.parse(words, offset_):
            for offset2, remaining_values in self.inner_parse_helper(remaining_elements, words, offset):
                yield offset2, [value] + remaining_values

class Modifier(Element):
    def __init__(self, element):
         self.element = element

    def get_dependent_rules(self):
        return self.element.get_dependent_rules()

    def to_NatLink_grammar_element(self):
        return self.element.to_NatLink_grammar_element()

    def inner_parse(self, words, offset_):
        for offset, value in self.element.parse(words, offset_):
            yield offset, self.transform(value)


#
# Dealing with formatting dictation:  <<<>>>
#

def format_words(word_list):
    word_list = [word.encode('Windows-1252') for word in word_list]
    format_words2(word_list)  # for print side effect
    try:
        from natlink import nsformat
    except ImportError:
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
## Rule implementation using NatLink
##

class BasicRule:
    def __init__(self, exported, name_, element_, context_=None):
        self.exported = exported
        self.name = name_
        self.element = element_
        self.context = context_

    def is_exported(self):
        return self.exported

    def get_name(self):
        return self.name

    def get_element(self):
        return self.element

    def get_context(self):
        return self.context

class Rule(BasicRule):
    def __init__(self, name_, element_):
        BasicRule.__init__(self, False, name_, element_)

class ExportedRule(BasicRule):
    def __init__(self, name_, context_, element_):
        BasicRule.__init__(self, True, name_, element_, context_)


##
## Context implementation for NatLink
##

class Context:
    def __init__(self, executables=[], titles=[], high_priority=False):
        self.executables = executables
        self.titles = titles
        self.high_priority = high_priority

    def is_high_priority(self):
        return self.high_priority

    def should_be_active(self, executable_basename, window_title):
        return (self.executable_matches(executable_basename) and 
                self.title_matches(window_title))

    def executable_matches(self, executable_basename):
        if len(self.executables) == 0:
            return True
        for executable in self.executables:
            if executable == executable_basename:
                return True
        return False

    def title_matches(self, window_title):
        if len(self.titles) == 0:
            return True
        for title in self.titles:
            if str.find(window_title, title) >= 0:
                return True
        return False
        

##
## Grammar implementation using NatLink
##

#class Grammar(natlinkutils.GrammarBase):
class Grammar(GrammarBase):
    def __init__(self, file):
        # natlinkutils.GrammarBase.__init__(self)
        GrammarBase.__init__(self)
        self.file = file
        self.rules = []

    def load_grammar(self):
        print("***** loading " + self.file + "...")
        self.gramSpec = self.get_grammar_spec()
        print("  grammar specification is:")
        print(self.gramSpec)
        self.load(self.gramSpec)
        #self.currentModule = ("","",0)
        self.rule_state = {}
        #self.activateAll()

    def unload_grammar(self):
        print("***** unloading " + self.file + "...")
        self.unload()

    def add_rule(self, rule):
        self.rules += [rule]


    def get_grammar_spec(self):
        done = set()
        spec = ""
        for rule in self.rules:
            done, spec = self.generate_grammar_spec(rule, done, spec)
        return spec

    def generate_grammar_spec(self, rule, done=set(), before=""):
        rule_name = self.get_rule_name(rule)
        if rule_name in done:
            return done, before
        done.add(rule_name)
        if isinstance(rule, str):
            return done, before + "<" + rule_name + "> imported;\n"
        dependencies = rule.get_element().get_dependent_rules()
        for r in dependencies:
            done, before = self.generate_grammar_spec(r, done, before)
        added_spec = "<" + rule_name + ">" + \
            (" exported" if rule.is_exported() else "") + " = " + \
            rule.get_element().to_NatLink_grammar_element() + ";\n"
        return done, before + added_spec

    def get_rule_name(self, rule):
        if isinstance(rule, str):
            return rule
        else:
            return rule.get_name()

        
    def gotResultsInit(self, words, fullResults):
        print("\nGrammar from " + self.file + ":")
        print("  recognized: " + repr(fullResults))
        for rule in self.rules:
            print("  trying rule " + rule.get_name() + ":")
            results = rule.get_element().outer_parse(fullResults, 0)
            found = False
            for offset, value in results:
                if offset != len(words):
                    # print("    found partial parse: ",
                    #       words[0:offset], "->", repr(value))
                    continue
                if found:
                    print("    FOUND SECOND PARSE: ",
                          words[0:offset], "->", repr(value))
                    continue
                found = False
                print("    found parse: ",
                      words[0:offset], "->", repr(value))
                try:
                    action = value
                    text = action.eval(True, {}, "")
                    print("    resulting text is <" + text + ">")
                    do_flush(False, text)
                    return
                except Exception as e:
                    print("    threw exception: " + repr(e))
                    import traceback
                    traceback.print_exc(e)
                    return


    def gotBegin(self, moduleInfo):
        if len(moduleInfo)<3 or not moduleInfo[0]: 
            executable_basename = "unknown"
            window_title = "unknown"
        else:
            executable_basename = getBaseName(moduleInfo[0]).lower()
            window_title = moduleInfo[1].lower()

        for rule in self.rules:
            if not rule.is_exported():
                continue
            context = rule.get_context()
            high_priority = context.is_high_priority()
            status = context.should_be_active(executable_basename, window_title)
            if high_priority:
                self.activate_rule_for_window(rule.get_name(), moduleInfo[2], status)
            else:
                self.activate_rule_for_everywhere(rule.get_name(), status)

    def getBaseName(name):
        return os.path.splitext(os.path.split(name)[1])[0]

    def activate_rule_for_window(self, rule_name, window, status):
        current = self.rule_state.get(rule_name)
        active = (current == window)
        if status == active: return
        if current:
            print("Deactivating " + rule_name + "@" + self.file + 
                  " (was active for " + repr(current) + ")")
            self.deactivate(rule_name)
            self.rule_state[rule_name] = None
        if status:
            try:
                print("Activating " + rule_name + "@" + self.file + " for window " + repr(window))
                self.activate(rule_name, window)
                self.rule_state[rule_name] = window
            except natlink.BadWindow:
                pass

    def activate_rule_for_everywhere(self, rule_name, status):
        active = self.rule_state.get(rule_name) is not None
        if status == active: return
        if status:
            try:
                print("Activating " + rule_name + "@" + self.file + " globally")
                self.activate(rule_name)
                self.rule_state[rule_name] = "global"
            except natlink.BadWindow:
                pass
        else:
            print("Deactivating " + rule_name + "@" + self.file)
            self.deactivate(rule_name)
            self.rule_state[rule_name] = None
