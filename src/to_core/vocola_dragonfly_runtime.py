###
### vocola_dragonfly_runtime.py - Code used by Vocola's generated
###                               Python code produced by the dragonfly backend
###

from __future__ import print_function

import dragonfly

from VocolaUtils import (VocolaRuntimeError, do_flush, call_Dragon)



##
## Element implementation using dragonfly
##

class Empty:
    def to_dragonfly(self):
        #         return Empty(value=self.value)
        #         return Optional(Impossible(), default=self.value)
        return dragonfly.Modifier(dragonfly.Optional(dragonfly.Impossible(), default=None),
                                  lambda value: None)

class Term:
    def __init__(self, terminal_text):
         self.terminal_text = terminal_text

    def to_dragonfly(self):
         return dragonfly.Literal(text=self.terminal_text, value=self.terminal_text)

class Dictation:
    def to_dragonfly(self):
         return dragonfly.Modifier(dragonfly.Dictation(format=False),
                                   lambda words: format_words(words))

class RuleRef:
    def __init__(self, rule):
         self.rule = rule

    def to_dragonfly(self):
         return dragonfly.RuleRef(rule=self.rule)

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
        
    def to_dragonfly(self):
         return dragonfly.Modifier(self.element.to_dragonfly(), 
                                   lambda values: (self.number, Join(self.reduce_to_actions(values))))

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

    def to_dragonfly(self):
         return dragonfly.Modifier(self.element.to_dragonfly(), 
                                   lambda value: self.action.bind(self.get_bindings(value)))


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
    def __init__(self, name, arguments):
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
        return preceding_text + "VocolaCall"

class ExtensionCall(ActionCall):
    def eval(self, is_top_level, bindings, preceding_text):
        return preceding_text + "ExtensionCall"
    

##
## Rule implementation using dragonfly
##

class Rule(dragonfly.Rule):
    def __init__(self, name_, element_):
        dragonfly.Rule.__init__(self, name=name_, element=element_.to_dragonfly())
        print(repr(element_.to_dragonfly().gstring()))

    def process_recognition(self, node):
        try:
            action = node.value()
            text = action.eval(True, {}, "")
            print("resulting text is <" + text + ">")
            do_flush(False, text)
        except Exception as e:
            print(self.name + " threw exception: " + repr(e))

