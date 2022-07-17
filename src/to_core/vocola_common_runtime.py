###
### Common runtime code shared across backends
###

from __future__ import print_function

import importlib
import sys

from VocolaUtils import (VocolaRuntimeError, do_flush, to_long, call_Dragon, eval_template)


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

    

