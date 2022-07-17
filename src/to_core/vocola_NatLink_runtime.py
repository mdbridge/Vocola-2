###
### vocola_NatLink_runtime.py - Code used by Vocola's generated
###                               Python code produced by the NatLink backend
###

from __future__ import print_function

import natlinkutils

from VocolaUtils import (VocolaRuntimeError)
from vocola_common_runtime import *


##
## Element implementation using NatLink
##

class Element:
    def get_dependent_rules(self):
        return []

    def outer_parse(self, words, offset_):
        print("  trying to parse " + repr(words[offset_:]))
        return self.parse(words, offset_)

    def parse(self, words, offset_):
        for offset, value in self.inner_parse(words, offset_):
            print("    ", self.to_NatLink_grammar_element(), ":", repr(words[offset_:offset]), " -> ", repr(value))
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
            value += [words[offset][0]]
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
        # for offset, value in self.rule.parse(words, offset_):
        #     yield offset, value
        

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
        return "(" + " | ".join(c.to_NatLink_grammar_element() for c in self.alternatives) + ")"

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

    def inner_parse_helper(self, remaining_elements, words, offset_):
        if len(remaining_elements) == 0:
            yield offset_, []
            return
        first_element = remaining_elements[0]
        remaining_elements = remaining_elements[1:]
        for offset, value in first_element.parse(words, offset_):
            for offset2, remaining_values in self.inner_parse_helper(remaining_elements, words, offset):
                yield offset2, [value] + remaining_values

    def inner_parse(self, words, offset_):
        return self.inner_parse_helper(self.elements, words, offset_)

class Slot(Element):
    def __init__(self, element, number):
         self.element = element
         self.number = number

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

    def reduce_to_action(self, value):
        actions = self.reduce_to_actions(value)
        return actions[0] if len(actions) > 0 else Text("")

    def get_dependent_rules(self):
        return self.element.get_dependent_rules()

    def to_NatLink_grammar_element(self):
        return self.element.to_NatLink_grammar_element()

    def inner_parse(self, words, offset_):
        for offset, value in self.element.parse(words, offset_):
            yield offset, (self.number, self.reduce_to_action(value))

class With(Element):
    def __init__(self, element, actions):
         self.element = element
         self.action = Prog(actions)

    def get_bindings(self, value):
        bindings = {}
        if isinstance(value, tuple):
            bindings[value[0]] = value[1]
        if isinstance(value, list):
            for v in value:
                b = self.get_bindings(v)
                bindings.update(b)
        return bindings

    def get_dependent_rules(self):
        return self.element.get_dependent_rules()

    def to_NatLink_grammar_element(self):
        return self.element.to_NatLink_grammar_element()

    def inner_parse(self, words, offset_):
        for offset, value in self.element.parse(words, offset_):
            yield offset, self.action.bind(self.get_bindings(value))

class Without(Element):
    def __init__(self, element):
         self.element = element

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
                                 "Without element received unexpected value from sub element: " +
                                 repr(value))
        
    def get_dependent_rules(self):
        return self.element.get_dependent_rules()

    def to_NatLink_grammar_element(self):
        return self.element.to_NatLink_grammar_element()

    def inner_parse(self, words, offset_):
        for offset, value in self.element.parse(words, offset_):
            yield offset, Join(self.reduce_to_actions(value))


#
# Dealing with formatting dictation:  <<<>>>
#

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



##
## Rule implementation using 
##

class Rule():
    def __init__(self, name_, element_):
        self.name = name_
        self.element = element_
        # dragonfly.Rule.__init__(self, name=name_, element=element_.to_dragonfly(), 
        #                         exported=False)
        #print("inner : " + repr(element_.to_dragonfly().gstring()))

    def get_name(self):
        return self.name

    def get_element(self):
        return self.element

    def get_dependent_rules(self):
        return self.element.get_dependent_rules()

    def is_exported(self):
        return False

class ExportedRule():
    def __init__(self, file_, name_, element_):
        self.name = name_
        self.element = element_
        # dragonfly.Rule.__init__(self, name=name_, element=element_.to_dragonfly())
        self.file = file_
        # print("loaded from " + file_ + " : " + repr(element_.to_dragonfly().gstring()))

    def process_recognition(self, node):
        try:
            print("\nExportedRule " + self.name + " from "+ self.file + " recognized: " + repr(node))
            action = node.value()
            text = action.eval(True, {}, "")
            print("resulting text is <" + text + ">")
            do_flush(False, text)
        except Exception as e:
            print(self.name + " threw exception: " + repr(e))
            import traceback
            traceback.print_exc(e)

    def to_NatLink_grammar_element(self):
        return self.element.to_NatLink_grammar_element()

    def get_name(self):
        return self.name

    def get_element(self):
        return self.element

    def get_dependent_rules(self):
        return self.element.get_dependent_rules()

    def is_exported(self):
        return True



##
## 
##

class Grammar(natlinkutils.GrammarBase):
    def __init__(self):
        natlinkutils.GrammarBase.__init__(self)
        self.rules = []

    def load_grammar(self):
        self.gramSpec = self.get_grammar_spec()
        print("loading grammar specification of:")
        print(self.gramSpec)
        self.load(self.gramSpec)
        self.currentModule = ("","",0)
        self.rule_state = {}
        self.activateAll()

    def unload_grammar(self):
        self.unload()
        pass

    def add_rule(self, rule):
        self.rules += [rule]

    def get_grammar_spec(self):
        done = set()
        spec = ""
        for rule in self.rules:
            done, spec = self.generate_grammar_spec(rule, done, spec)
        return spec

    def get_rule_name(self, rule):
        if isinstance(rule, str):
            return rule
        else:
            return rule.get_name()

    def generate_grammar_spec(self, rule, done=set(), before=""):
        rule_name = self.get_rule_name(rule)
        if rule_name in done:
            return done, before
        done.add(rule_name)
        if isinstance(rule, str):
            return done, before + "<" + rule_name + "> imported;\n"
        dependencies = rule.get_dependent_rules()
        for r in dependencies:
            r_name = self.get_rule_name(r)
            done, before = self.generate_grammar_spec(r, done, before)
        added_spec = "<" + rule_name + ">" + \
            (" exported" if rule.is_exported() else "") + " = " + \
            rule.get_element().to_NatLink_grammar_element() + ";\n"
        return done, before + added_spec
        
    def gotResultsInit(self, words, fullResults):
        print(repr(words), repr(fullResults))
        results = self.rules[0].get_element().outer_parse(fullResults, 0)
        found = False
        for offset, value in results:
            if offset != len(words):
                print("found partial parse: ",
                      words[0:offset], " -> ", repr(value))
                continue
            if found:
                print("found second parse: ",
                      words[0:offset], " -> ", repr(value))
                continue
            found = False
            print("found parse: ",
                  words[0:offset], " -> ", repr(value))
            try:
                action = value
                text = action.eval(True, {}, "")
                print("resulting text is <" + text + ">")
                do_flush(False, text)
            except Exception as e:
                print(" threw exception: " + repr(e))
                import traceback
                traceback.print_exc(e)
        print("no more parsing left\n")
