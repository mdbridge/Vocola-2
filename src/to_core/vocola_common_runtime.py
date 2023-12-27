###
### Common runtime code shared across backends
###

from __future__ import print_function

import importlib
import sys

from VocolaUtils import (VocolaRuntimeError, VocolaRuntimeAbort, 
                         call_playString, to_long, eval_template, 
                         call_Dragon, call_Unimacro)


##
## Verbosity level
##

# Verbosity levels (cumulative effects)
# 
#   0: no verbose output
#   1: basic output per command recognized
#   2: output for most command execution steps, details of resulting actions from parse
#   3: output for loading/unloading grammars and activating/deactivating rules
#      output for EvalTemplate steps

vocola_verbosity = 1

def get_vocola_verbosity():
    return vocola_verbosity

def set_vocola_verbosity(level):
    global vocola_verbosity
    vocola_verbosity = level

def vlog(level, *args, **kwargs):
    if level <= vocola_verbosity:
        print(*args, **kwargs)


##
## Sending text
##

def do_playString(buffer):
    if buffer != "":
        call_playString(buffer)
        vlog(2, "    playString(" + repr(buffer) + ")")


##
## Actions except calls
##

# note that the type of bindings is Dict of int => Action

class Action:
    def __repr__(self):
        return "Action(" + self.to_string() + ")"

    def to_string(self):
        return "<base_class>"

    def bind(self, bindings):
        return BoundAction(bindings, self)

    def eval(self, is_top_level, bindings, preceding_text):
        return preceding_text

class BoundAction(Action):
    def __init__(self, bindings, action):
        self.bindings = bindings
        self.action = action

    def to_string(self):
        result = ""
        for key in sorted(self.bindings.keys()):
            if result != "":
                result += " "
            result += "$" + str(key) + "=" +  self.bindings[key].to_string()
        return "[" + result + "] " + self.action.to_string()

    def eval(self, is_top_level, bindings, preceding_text):
        return self.action.eval(is_top_level, self.bindings, preceding_text)

class CatchAction(Action):
    def __init__(self, specification, filename, line, actions):
        self.specification = specification
        self.filename      = filename
        self.line          = line
        self.action        = Prog(actions)

    def to_string(self):
        return "^(" + self.action.to_string() + ")"

    def eval(self, is_top_level, bindings, preceding_text):
        try:
            return self.action.eval(is_top_level, bindings, preceding_text)
        except VocolaRuntimeAbort:
            raise
        except Exception as exception:
            print()
            print("While executing the following Vocola command:", file=sys.stderr)
            print("    " + self.specification, file=sys.stderr)
            print("defined at line " + str(self.line) + " of " + self.filename +",", file=sys.stderr)
            print("the following error occurred:", file=sys.stderr)
            print("    " + exception.__class__.__name__ + ": " \
                  + str(exception), file=sys.stderr)
            raise VocolaRuntimeAbort()


class Text(Action):
    def __init__(self, text):
        self.text = text

    def to_string(self):
        return '"' + self.text.replace('"', '""') + '"'

    def eval(self, is_top_level, bindings, preceding_text):
        return preceding_text + self.text

class Ref(Action):
    def __init__(self, slot):
         self.slot = slot

    def to_string(self):
        return "$" + str(self.slot)

    def eval(self, is_top_level, bindings, preceding_text):
        if self.slot in bindings.keys():
            action = bindings[self.slot]
        else:
            action = Text("")
        return action.eval(is_top_level, bindings, preceding_text)

class Prog(Action):
    def __init__(self, actions):
        self.actions = []
        for action in actions:
            # For conciseness, Prog allows passing strings instead of Text actions
            if isinstance(action, str):
                action = Text(action)
            self.actions.append(action)

    def to_string(self):
        return ";".join([action.to_string() for action in self.actions])

    def eval(self, is_top_level, bindings, preceding_text):
        for action in self.actions:
            preceding_text = action.eval(is_top_level, bindings, preceding_text)
        return preceding_text

class Join(Action):
    def __init__(self, actions):
        self.actions = actions

    def to_string(self):
        return "Join(" + ",".join([action.to_string() for action in self.actions]) + ")"

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
        self.module_name = None
        self.arguments = [Prog(actions) for actions in arguments]

    def full_name(self):
        if self.module_name is not None:
            separator = ":"
            if isinstance(self,ExtProc):
                separator = "!"
            return self.module_name + separator + self.name
        else:
            return self.name

    def to_string(self):
        return self.full_name() + "(" + \
            ",".join([argument.to_string() for argument in self.arguments]) + ")"

    def call_description(self, values):
         return self.full_name() + "(" + \
             ", ".join([repr(v) for v in values]) + ")"

    def do_flush(self, functional_context, buffer):
        if functional_context:
            raise VocolaRuntimeError(
                'attempt to call Unimacro, Dragon, or a Vocola extension ' +
                'procedure in a functional context!\n    ' + 
                'Procedure name was ' + self.full_name())
        do_playString(buffer)


class DragonCall(ActionCall):
    def eval(self, is_top_level, bindings, preceding_text):
        self.do_flush(not is_top_level, preceding_text)
        dragon_info = Dragon_functions[self.name][1]
        values = [argument.eval(False, bindings, "") for argument in self.arguments]
        call_Dragon(self.name, dragon_info, values)
        vlog(2, "    " +  self.call_description(values) + "!")
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
            result = eval_template(*values)
            vlog(3, "    " +  self.call_description(values) + " -> " + repr(result))
            return preceding_text + result
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
            self.do_flush(not is_top_level, preceding_text)
            values = [argument.eval(False, bindings, "") for argument in self.arguments]
            call_Unimacro(values[0])
            vlog(2, "    " +  self.call_description(values) + "!")
            return ""
        else: 
            raise VocolaRuntimeError("Implementation error: " +
                                     "VocolaCall passed unknown Vocola function: " +
                                     name)


class ExtensionCall(ActionCall):
    def __init__(self, module_name, name, *arguments):
        ActionCall.__init__(self, name, *arguments)
        self.module_name = module_name

    def get_extension_implementation(self):
        if self.module_name in sys.modules:
            extension_module = sys.modules[self.module_name]
        else:
            vlog(2, "    automatically importing:", self.module_name)
            extension_module = importlib.import_module(self.module_name)
        extension_routine = getattr(extension_module, self.name)
        return extension_routine


class ExtRoutine(ExtensionCall):
    def eval(self, is_top_level, bindings, preceding_text):
        values = [argument.eval(False, bindings, "") for argument in self.arguments]
        implementation = self.get_extension_implementation()
        try:
            result = implementation(*values)
            vlog(2, "    " +  self.call_description(values) + " -> " + repr(result))
            return preceding_text + result
        except Exception as e:
            vlog(2, "    " +  self.call_description(values) + " -> threw " + 
                 type(e).__name__)
            raise
class ExtProc(ExtensionCall):
    def eval(self, is_top_level, bindings, preceding_text):
        self.do_flush(not is_top_level, preceding_text)
        values = [argument.eval(False, bindings, "") for argument in self.arguments]
        implementation = self.get_extension_implementation()
        try:
            result = implementation(*values)
            vlog(2, "    " +  self.call_description(values) + "!")
        except Exception as e:
            vlog(2, "    " +  self.call_description(values) + " threw " + 
                 type(e).__name__)
            raise

        return ""
