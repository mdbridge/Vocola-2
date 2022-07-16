###
### vocola_NatLink_runtime.py - Code used by Vocola's generated
###                               Python code produced by the NatLink backend
###

from __future__ import print_function

import importlib
import sys

import natlinkutils
import dragonfly

from VocolaUtils import (VocolaRuntimeError, do_flush, to_long, call_Dragon, eval_template)



##
## Element implementation using NatLink
##

# class Empty:
#     def to_NatLink_grammar_element(self):
#         raise undefined

class Term:
    def __init__(self, terminal_text):
         self.terminal_text = terminal_text

    def get_dependent_rules(self):
        return []

    def to_NatLink_grammar_element(self):
        return "'" + make_safe_python_string(self.terminal_text) + "'"

def make_safe_python_string(text):
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace("\"", "\\\"")
    text = text.replace("\n", "\\n")
    return text

class Dictation:
    def to_NatLink_grammar_element(self):
        return "<dgndictation>"

    def get_dependent_rules(self):
        return []

class RuleRef:
    def __init__(self, rule):
         self.rule = rule

    def get_dependent_rules(self):
        return [self.rule]

    def to_NatLink_grammar_element(self):
        return "<" + self.rule.get_name() + ">"


class Opt:
    def __init__(self, element):
         self.element = element

    def get_dependent_rules(self):
        return self.element.get_dependent_rules()

    def to_NatLink_grammar_element(self):
        return "[" + self.element.to_NatLink_grammar_element() + "]"

class Alt:
    def __init__(self, alternatives):
         self.alternatives = alternatives

    def get_dependent_rules(self):
        result = []
        for alternative in self.alternatives:
            result += alternative.get_dependent_rules()
        return result

    def to_NatLink_grammar_element(self):
        return "(" + " | ".join(c.to_NatLink_grammar_element() for c in self.alternatives) + ")"

class Seq:
    def __init__(self, elements):
         self.elements = elements

    def get_dependent_rules(self):
        result = []
        for element in self.elements:
            result += element.get_dependent_rules()
        return result

    def to_NatLink_grammar_element(self):
        return " ".join(c.to_NatLink_grammar_element() for c in self.elements)

class Slot:
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
    # def to_dragonfly(self):
    #      return dragonfly.Modifier(self.element.to_dragonfly(), 
    #                                lambda values: (self.number, self.reduce_to_action(values)))

class With:
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
    # def to_dragonfly(self):
    #      return dragonfly.Modifier(self.element.to_dragonfly(), 
    #                                lambda value: self.action.bind(self.get_bindings(value)))

class Without:
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
    # def to_dragonfly(self):
    #      return dragonfly.Modifier(self.element.to_dragonfly(), 
    #                                lambda values: Join(self.reduce_to_actions(values)))


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
## Actions except calls
##

# note that the type of bindings is Dict of int => Action

class Action:
    def bind(self, bindings):
        return BoundAction(bindings, self)

    def eval(self, is_top_level, bindings, preceding_text):
        return preceding_text

class BoundAction(Action):
    def __init__(self, bindings, action):
        self.bindings = bindings
        self.action = action

    def eval(self, is_top_level, bindings, preceding_text):
        return self.action.eval(is_top_level, self.bindings, preceding_text)


class Text(Action):
    def __init__(self, text):
        self.text = text

    def eval(self, is_top_level, bindings, preceding_text):
        return preceding_text + self.text

class Ref(Action):
    def __init__(self, slot):
         self.slot = slot

    def eval(self, is_top_level, bindings, preceding_text):
        if self.slot in bindings.keys():
            action = bindings[self.slot]
        else:
            action = Text("")
        return action.eval(is_top_level, bindings, preceding_text)

class Prog(Action):
    def __init__(self, actions):
        self.actions = actions

    def eval(self, is_top_level, bindings, preceding_text):
        for action in self.actions:
            # For conciseness, Prog allows passing strings instead of Text actions
            if isinstance(action, str):
                action = Text(action)
            preceding_text = action.eval(is_top_level, bindings, preceding_text)
        return preceding_text

class Join(Action):
    def __init__(self, actions):
        self.actions = actions

    def eval(self, is_top_level, bindings, preceding_text):
        result = preceding_text
        seen_new_text = False
        for action in self.actions:
            new_text = action.eval(False, bindings, "")
            if new_text != "":
                if seen_new_text:
                    result = result + " "
                else:
                    seen_new_text = True
                result = result + new_text
        return result



##
## Actions that call
##

class ActionCall(Action):
    def __init__(self, name, *arguments):
        self.name = name
        self.arguments = [Prog(actions) for actions in arguments]


class DragonCall(ActionCall):
    def eval(self, is_top_level, bindings, preceding_text):
        do_flush(not is_top_level, preceding_text)
        dragon_info = Dragon_functions[self.name][1]
        values = [argument.eval(False, bindings, "") for argument in self.arguments]
        call_Dragon(self.name, dragon_info, values)
        return ""

# Built in Dragon functions with (minimum number of arguments,
# template of types of all possible arguments); template has one
# letter per argument with s denoting string and i denoting integer:

Dragon_functions = {
                     "ActiveControlPick" : [1,"s"],
                     "ActiveMenuPick"    : [1,"s"],
                     "AppBringUp"        : [1,"ssis"],
                     "AppSwapWith"       : [1,"s"],
                     "Beep"              : [0,""],
                     "ButtonClick"       : [0,"ii"],
                     "ClearDesktop"      : [0,""],
                     "ControlPick"       : [1,"s"],
                     "DdeExecute"        : [3,"sssi"],
                     "DdePoke"           : [4,"ssss"],
                     "DllCall"           : [3,"sss"],
                     "DragToPoint"       : [0,"i"],
                     "GoToSleep"         : [0,""],
                     "HeardWord"         : [1,"ssssssss"],  # max 8 words
                     "HTMLHelp"          : [2,"sss"],
                     "MenuCancel"        : [0,""],
                     "MenuPick"          : [1,"s"],
                     "MouseGrid"         : [0,"ii"],
                     "MsgBoxConfirm"     : [3,"sis"],
                     "PlaySound"         : [1,"s"],
                     "RememberPoint"     : [0,""],
                     "RunScriptFile"     : [1,"s"],
                     "SendKeys"          : [1,"s"],
                     "SendDragonKeys"    : [1,"s"],
                     "SendSystemKeys"    : [1,"si"],
                     "SetMicrophone"     : [0,"i"],
                     "SetMousePosition"  : [2,"iii"],
                     "SetNaturalText"    : [1,"i"],
                     "ShellExecute"      : [1,"siss"],
                     "ShiftKey"          : [0,"ii"],
                     "TTSPlayString"     : [0,"ss"],
                     "Wait"              : [1,"i"],
                     "WaitForWindow"     : [1,"ssi"],
                     "WakeUp"            : [0,""],
                     "WinHelp"           : [2,"sii"],
                    }


class VocolaCall(ActionCall):
    def eval(self, is_top_level, bindings, preceding_text):
        name = self.name
        if   name == "EvalTemplate":
            values = [argument.eval(False, bindings, "") for argument in self.arguments]
            return preceding_text + eval_template(*values)
        elif name == "If":
            condition = self.arguments[0].eval(False, bindings, "")
            if condition.lower() == "true":
                return self.arguments[1].eval(is_top_level, bindings, preceding_text)
            elif len(self.arguments) > 2:
                return self.arguments[2].eval(is_top_level, bindings, preceding_text)
            else:
                return preceding_text
        elif name == "When":
            value = self.arguments[0].eval(False, bindings, "")
            if value != "":
                return self.arguments[1].eval(is_top_level, bindings, preceding_text)
            elif len(self.arguments) > 2:
                return self.arguments[2].eval(is_top_level, bindings, preceding_text)
            else:
                return preceding_text
        elif name == "Repeat":
            count = self.arguments[0].eval(False, bindings, "")
            count = to_long(count)
            for i in range(count):
                preceding_text = self.arguments[1].eval(is_top_level, bindings, preceding_text)
            return preceding_text
        elif name == "Unimacro":
            # <<<>>>
            raise VocolaRuntimeError("Unimacro gateway not yet implemented")
        else: 
            raise VocolaRuntimeError("Implementation error: " +
                                     "VocolaCall passed unknown Vocola function: " +
                                     name)


class ExtensionCall(ActionCall):
    def __init__(self, module_name, name, *arguments):
        self.module_name = module_name
        ActionCall.__init__(self, name, *arguments)

    def get_extension_implementation(self):
        if self.module_name in sys.modules:
            extension_module = sys.modules[self.module_name]
        else:
            print("automatically importing: " + self.module_name)
            extension_module = importlib.import_module(self.module_name)
        extension_routine = getattr(extension_module, self.name)
        return extension_routine

class ExtRoutine(ExtensionCall):
    def eval(self, is_top_level, bindings, preceding_text):
        values = [argument.eval(False, bindings, "") for argument in self.arguments]
        implementation = self.get_extension_implementation()
        result = implementation(*values)
        print(self.module_name + ":" + self.name + "(" +
              ", ".join([repr(v) for v in values]) + ") -> " + repr( result))
        return preceding_text + result

class ExtProc(ExtensionCall):
    def eval(self, is_top_level, bindings, preceding_text):
        if not is_top_level:
            raise VocolaRuntimeError(
                'attempt to call Vocola extension ' +
                'procedure ' +  self.name + ' in a functional context!')
        do_flush(not is_top_level, preceding_text)
        values = [argument.eval(False, bindings, "") for argument in self.arguments]
        implementation = self.get_extension_implementation()
        result = implementation(*values)
        return ""

    

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


##
## 
##

class Grammar(natlinkutils.GrammarBase):
    def __init__(self):
        pass

    def load_grammar(self):
        self.gramSpec = """
testing
"""
        #self.load(self.gramSpec)
        self.currentModule = ("","",0)
        self.rule_state = {}

    def unload_grammar(self):
        #self.unload()
        pass

    def add_rule(self, rule):
        print("adding rule with: ")
        done, before = self.generate_grammar_spec(rule)
        # print(repr(done))
        print(before)
        #print(repr(before))

    def generate_grammar_spec(self, rule, done=set(), before=""):
        rule_name = rule.get_name()
        if rule_name in done:
            return done, before
        done.add(rule_name)
        dependencies = rule.get_dependent_rules()
        # print(rule.get_name(), repr(dependencies))
        for r in dependencies:
            if not r.get_name() in done:
                done, before = self.generate_grammar_spec(r, done, before)
        added_spec = "<" + rule_name + "> = " + \
            rule.get_element().to_NatLink_grammar_element() + ";\n"
        return done, before + added_spec
        
