###
### Vortex: attempt to provide basic text control for nonstandard applications
###
### Inspired by windict.py, written by Joel Gould.
###
###
### Copyright 2015-2016 by Mark Lillibridge.
###
### Permission is hereby granted, free of charge, to any person
### obtaining a copy of this software and associated documentation files
### (the "Software"), to deal in the Software without restriction,
### including without limitation the rights to use, copy, modify, merge,
### publish, distribute, sublicense, and/or sell copies of the Software,
### and to permit persons to whom the Software is furnished to do so,
### subject to the following conditions:
### 
### The above copyright notice and this permission notice shall be
### included in all copies or substantial portions of the Software.
### 
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
### EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
### MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
### NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
### BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
### ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
### CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
### SOFTWARE.
###

from __future__ import print_function

import os.path
import re
import string
import sys
import time

import win32gui

import natlink
from   natlinkutils import *
import VocolaUtils

import vocola_ext_clipboard
import vocola_ext_keys
import vocola_ext_dragon_proxy



###########################################################################
#                                                                         #
# Blacklisting application/windows                                        #
#                                                                         #
###########################################################################

#
# Don't ever automatically turn Vortex on for windows belonging to
# these executables:
#
Blacklisted_applications = [
    # Dragon's own programs (except spelling window) have FullTextControl:
    #   DragonPad, dictation box, Command Browser, vocabulary editor, 
    #   NatLink messages but not (whitelisted below) spelling window
    "natspeak.exe",
    
    # Dragon provides FullTextControl for most Microsoft office applications:
    "excel.exe",
    "lync.exe",
    "outlook.exe",
    "winword.exe",
    # PowerPoint does not have FullTextControl so benefits from Vortex on

    # editors with text controls that Dragon gives FullTextControl for:
    "notepad.exe",
    "win32pad.exe",
    "wordpad.exe",

    # all controls of normal File Explorer windows that can be
    # enabled, Dragon gives FullTextControl
    #   (also includes control panel, settings dialog boxes)
    "explorer.exe"
]

def blacklisted(moduleInfo):
    executable = os.path.basename(moduleInfo[0]).lower()
    title      = moduleInfo[1]
    handle     = moduleInfo[2]
    #class_name = win32gui.GetClassName(handle)

    if executable=="natspeak.exe" and title=="Spelling Window":
        return False

    return executable in Blacklisted_applications



###########################################################################
#                                                                         #
# DictationObject: wrapper for NatLink voice dictation object (DictObj)   #
#                                                                         #
###########################################################################

class DictationObject:

    # Initially we are not activated for any window.  The following
    # methods of handler will be called per the DictObj documentation:
    #
    #    dictation_begin_callback
    #    dictation_change_callback
    #
    # Note that dictation_begin_callback is called even for
    # unactivated DictObj's.
    def __init__(self, handler):
        self.my_handle = None
        self.handler   = handler
        self.underlying_DictObj = natlink.DictObj()
        self.underlying_DictObj.setBeginCallback (handler.dictation_begin_callback)
        self.underlying_DictObj.setChangeCallback(handler.dictation_change_callback)

    # Activate us for window handle (None means deactivate).  If
    # already activated for another window, deactivate first.  May
    # throw natlink.BadWindow, leaving us unactivated.
    def activate(self, handle):
        if self.my_handle:
            self.underlying_DictObj.deactivate()
            self.my_handle = None
        if handle:
            # this can throw natlink.BadWindow:
            self.underlying_DictObj.activate(handle)
            self.my_handle = handle

    # This must be called before finishing with us to free underlying
    # resources.
    def terminate(self):
        self.activate(None)
        self.underlying_DictObj.setBeginCallback (None)
        self.underlying_DictObj.setChangeCallback(None)
        self.underlying_DictObj = None

    # Forward calls to: 
    #   setLock, setText, setTextSel, setVisibleText,
    #   getLength, getText, getTextSel, getVisibleText.
    def __getattr__(self, attribute):
        if self.underlying_DictObj:
            return getattr(self.underlying_DictObj, attribute)
        raise AttributeError(attribute)



###########################################################################
#                                                                         #
# ApplicationControl: control an application (e.g., selection)            #
#                                                                         #
###########################################################################

class ApplicationControl:

    ## Invariant: after sending self.postponed_keys to the application
    ##            window my_handle, the selection is
    ##
    ##              self.text[self.start,self.end) with the cursor 
    ##              before self.end.
    ##
    ## Invariant: self.start <= self.end

    def __init__(self, handle):
        self.my_handle = handle
        self.set_state("")

    def show_state(self, prefix=""):
        print("  0x%08x: '%s%s<%s>%s'" % (self.my_handle, prefix,
                                        self.text[:self.start], 
                                        self.text[self.start:self.end],
                                        self.text[self.end:]))
        if self.postponed_keys != "":
            print("    postponed keys: '%s'" % (self.postponed_keys))

    def get_state(self):
        return (self.text, self.start, self.end)
    

    # precondition: application cursor is at the end of new_text and
    #               selection is either all of new_text (select_all)
    #               or nothing.
    def set_state(self, new_text, select_all=False):
        self.text = new_text        
        self.end  = len(new_text)
        if select_all:
            self.start = 0
        else:
            self.start = self.end
        self.postponed_keys = ""

    # precondition: self.postponed_keys == ""
    def assume_selection_replaced(self, new_text):
        self.text  = self.text[0:self.start] + new_text + self.text[self.end:]
        self.start = self.end = self.start + len(new_text)


    def unselect(self):
        size = self.distance(self.start, self.end) # selection size
        if size > 0:
            self.postponed_keys += "{shift+left " + str(size) + "}"
            self.end = self.start

    def move_to(self, target):
        self.unselect()
        move = self.distance(self.end, target)
        if move > 0:
            self.postponed_keys += "{right %d}" % (move)
        elif move < 0:
            self.postponed_keys += "{left %d}"  % (-move)
        self.start = self.end = target

    def select(self, start, end):
        if start != self.start or end != self.end:
            self.move_to(start)
            size = self.distance(start, end)
            if size > 0:
                self.postponed_keys += "{shift+right " + str(size) + "}"
                self.end = end

    def replace(self, start, end, new_text):
        size = self.distance(start, end)
        if size != 0:
            self.move_to(end)
            self.postponed_keys += "{backspace " + str(size) + "}"
            self.text  = self.text[0:start] + self.text[end:]
            self.start = self.end = start
        if new_text != "":
            self.move_to(start)
            self.postponed_keys += new_text.replace("\r", "").replace("{", "{{}")
            self.text  = self.text[0:start] + new_text + self.text[start:]
            self.start = self.end = start + len(new_text)


    def try_flush(self):
        keys = self.postponed_keys
        if keys == "":
            return True
        handle = win32gui.GetForegroundWindow()
        if handle == self.my_handle:
            print("  sending: '" + keys + "'")
            self.play_string(keys)
            self.postponed_keys = ""
            return True
        print("  WARNING: delaying keys due to different active window, window ID 0x%08x" % (handle))
        self.postponed_keys = keys
        return False


    # returns end-start except counts each \r\n as 1 character:
    def distance(self, start, end):
        sign = 1
        if end < start:
            sign = -1
            start, end = end, start
        size = len(self.text[start:end].replace("\r", ""))
        return size * sign

    def play_string(self, keys):
        keys  = keys.replace("\n", "{enter}")
        shift = "{" + VocolaUtils.name_for_shift() + "}"

        # the following does not work because it causes
        # dictation_change_callback to be called:
        #natlink.playString(shift + keys)

        vocola_ext_keys.send_input(shift + keys)



###########################################################################
#                                                                         #
# BasicTextControl: provide basic text control for a window               #
#                                                                         #
###########################################################################

class BasicTextControl:

    ##
    ## Setup and termination
    ##
    
    def __init__(self):
        self.my_handle           = None
        self.title               = None   # non-None if  self.my_handle
        self.application_control = None   # non-None iff self.my_handle
        # creation of DictationObject below calls
        # dictation_begin_callback so must follow above assignments:
        self.dictation_object    = DictationObject(self)

    def name(self):
        result = "BasicTextControl"
        if self.my_handle:
            result += " @ 0x%08x [%s]" % (self.my_handle, self.title)
        return result

    # Activate us for window handle (None means deactivate).  If
    # already activated for another window, deactivate first.  May
    # throw natlink.BadWindow, leaving us unactivated.
    def attach(self, handle):
        if self.my_handle:
            print("unattaching " + self.name())
            self.dictation_object.activate(None)
            self.my_handle           = None
            self.application_control = None
        if handle:
            self.title = win32gui.GetWindowText(handle)
            print("BasicTextControl attaching to window ID 0x%08x" % (handle))
            print("  with title '%s'" % (self.title))
            try:
                self.my_handle           = handle
                self.application_control = ApplicationControl(handle)
                # activate below may call dictation_begin_callback so want state set:
                self.set_buffer_unknown()
                self.dictation_object.activate(handle)
            except Exception as e:
                self.my_handle           = None
                self.application_control = None
                print("  ATTACHMENT FAILED: " + repr(e), file=sys.stderr)
                raise
        if self.my_handle:
            self.update_dictation_object_state()

    # WARNING: calling this from a gotBegin callback causes Dragon to
    # hang once in a while.  I could not narrow down what causes this
    # but even delaying tens of utterances after the window in
    # question no longer exists does not avoid the hang problem.
    def unload(self):
        print("unloading " + self.name())
        self.dictation_object.terminate()
        self.dictation_object = None


    ##
    ## Initializing, displaying our state
    ##

    def show_state(self):
        if self.application_control:
            self.application_control.show_state(self.fake_prefix_text)
        else:
            print("<unattached " + self.name() + ">")

    def set_buffer(self, text, unknown_prefix=False, select_all=False):
        self.application_control.set_state(text, select_all)
        self.fake_prefix_text = ""
        if unknown_prefix:
            # Effectively set state to no capitalization and no space
            # required before next word, hopefully not affecting
            # language model any:
            self.fake_prefix_text = "First, "
        self.show_state()

    def set_buffer_unknown(self):
        if not self.application_control: 
            return
        self.set_buffer("", True)



    ##
    ## Routines for interacting with DNS:
    ##

    def dictation_begin_callback(self, module_info):
        if self.application_control:
            self.update_dictation_object_state()

    def update_dictation_object_state(self):
        #print "updating state..."
        self.dictation_object.setLock(1)
        text, start, end = self.application_control.get_state()
        fake_prefix      = len(self.fake_prefix_text)
        shown_text       = self.fake_prefix_text + text
        start           += fake_prefix
        end             += fake_prefix
        # assume everything except fake prefix is visible all the time:
        visible_start, visible_end = fake_prefix, len(shown_text)
        self.dictation_object.setText(shown_text, 0, 0x7FFFFFFF)
        self.dictation_object.setTextSel(start, end)
        self.dictation_object.setVisibleText(visible_start, visible_end)
        self.dictation_object.setLock(0)


    def dictation_change_callback(self, deletion_start, deletion_end, new_text, 
                                  selection_start, selection_end):
        print("dictation_change_callback %d,%d, %s, %d,%d" % \
            (deletion_start, deletion_end, repr(new_text), selection_start,
             selection_end))

        fake_prefix        = len(self.fake_prefix_text)
        text, _start, _end = self.application_control.get_state()
        text               = self.fake_prefix_text + text

        # corrections can attempt to remove the last space of the fake
        # prefix (e.g., correct Fred to .c); "select all", "scratch
        # that" also tries to do that.  Corrections can also attempt
        # to replace the prefix's trailing space with another space.
        if deletion_start+1==fake_prefix and deletion_start<deletion_end and \
           self.fake_prefix_text[-1]==" ":
            # attempting to delete/replace trailing whitespace in fake prefix
            if len(new_text)>0 and new_text[0]==" ":
                print("  ignoring nop overwrite to trailing space in fake prefix")
                deletion_start += 1
                new_text = new_text[1:]
            else:
                print("  ignoring attempt to remove trailing space in fake prefix")
                deletion_start  += 1
                selection_start += 1
                selection_end   += 1

        # SPACE GUARD
        if fake_prefix>0 and deletion_start<deletion_end and new_text!="":
            if deletion_start==fake_prefix and \
               text[deletion_start]==" " and new_text[0]!=" ":
                print("  ***** SPACE GUARD preserved leading space", file=sys.stderr)
                deletion_start  += 1
                selection_start += 1
                selection_end   += 1
            if deletion_end==len(text) and deletion_start<deletion_end \
               and text[-1]==" " and new_text[-1]!=" ":
                print("  ***** SPACE GUARD preserved trailing space", file=sys.stderr)
                deletion_end -= 1
                if selection_start==deletion_start+len(new_text) \
                   and selection_start==selection_end:
                    selection_start += 1
                    selection_end   += 1

        # Block other attempts to alter fake prefix:
        #   (I haven't seen Dragon try any of these yet.)
        if deletion_start < fake_prefix:
            if deletion_start < deletion_end:
                print("\n  ***** ATTEMPT TO DELETE (PART OF) FAKE PREFIX DENIED!", file=sys.stderr)
                print(file=sys.stderr)
            if deletion_end<fake_prefix and new_text != "":
                print("\n  ***** ATTEMPT TO INSERT IN FAKE PREFIX DENIED!", file=sys.stderr)
                print(file=sys.stderr)
            deletion_start = max(fake_prefix, deletion_start)
            deletion_end   = max(fake_prefix, deletion_end)
            
        self.application_control.replace(deletion_start - fake_prefix, 
                                         deletion_end   - fake_prefix, new_text)

        # prevent "select all" from selecting fake prefix:
        selection_start = max(fake_prefix, selection_start)
        selection_end   = max(fake_prefix, selection_end)

        self.application_control.select(selection_start - fake_prefix, 
                                        selection_end   - fake_prefix)

        if deletion_start==deletion_end and new_text=="":
            # give spelling window time to pop up if it's going to:
            time.sleep(.1)

        self.application_control.try_flush()
        self.show_state()
        #print "end dictation_change_callback"


    ##
    ## Routines for interacting with Vocola:
    ##

    def vocola_pre_action(self, keys, action):
        if not self.application_control:
            return

        if self.my_handle != win32gui.GetForegroundWindow():
            # we are not the active window
            if action and win32gui.IsWindowVisible(self.my_handle):
                if re.search("ButtonClick|DragToPoint|Unimacro", action):
                    self.set_buffer_unknown()
            return

        # we are the active window
        self.application_control.try_flush()

        if keys:
            if keys.find("{") == -1:
                print("  assuming typed: " + keys)
                self.application_control.assume_selection_replaced(keys)
                self.show_state()
            else:
                self.set_buffer_unknown()
        elif action:
            if re.search("ActiveControlPick|ActiveMenuPick|ButtonClick|ControlPick|DragToPoint|MenuCancel|MenuPick|SendKeys|SendSystemKeys|Unimacro", action):
                self.set_buffer_unknown()



###########################################################################
#                                                                         #
# Catch all grammar for unloading BasicTextControl's                      #
#                                                                         #
###########################################################################

# window ID -> BasicTextControl instance or None
basic_control       = {}

nonexistent_windows = []


class CatchAllGrammar(GrammarBase):

    gramSpec = """
        <start> exported = {emptyList};
    """

    def initialize(self):
        self.load(self.gramSpec, allResults=1)
        self.activateAll()

    def gotResultsObject(self,recogType,resObj):
        global nonexistent_windows
        if recogType == 'reject':
            return
        print("utterance")
        
        # unload controls for/forget about no longer existing windows:
        # once enough utterances have passed
        #while len(nonexistent_windows) > 100:
        while len(nonexistent_windows) > 10:
            window              = nonexistent_windows[0]
            nonexistent_windows = nonexistent_windows[1:]
            if window >= 0:
                if basic_control.get(window) and not win32gui.IsWindow(window):
                    basic_control[window].unload()
                    del basic_control[window]
        nonexistent_windows += [-1]


catchAllGrammar = CatchAllGrammar()
catchAllGrammar.initialize()



###########################################################################
#                                                                         #
# Vortex command grammar                                                  #
#                                                                         #
###########################################################################

spare_control    = None

# should we try and turn on Vortex for each new window?
auto_on = True


class VortexGrammar(GrammarBase):

    gramSpec = """
        <start> exported = Vortex (on | off);
        <all>   exported = Vortex (on | off) everywhere;
        <load>  exported = Vortex (load | line);
        <clip>  exported = Vortex load clipboard;
    """

    def initialize(self):
        print("\nInit Vortex")
        self.visible_spelling_windows = []
        self.load(self.gramSpec)
        self.activateAll()
    
    def terminate(self):
        global spare_control, nonexistent_windows
        print("Exiting Vortex")
        self.vortex_off_everywhere()
        nonexistent_windows = []
        self.unload()


    def gotBegin(self, moduleInfo):
        global spare_control, nonexistent_windows
        handle = moduleInfo[2]
        if not handle:
            print("***** Dragon passed "+repr(handle)+" as the handle!", file=sys.stderr)
            return

        control = basic_control.get(handle, -1)
        if control==-1 and auto_on:
            for window in basic_control:
                if not win32gui.IsWindow(window):
                    if basic_control[window]:
                        print("no longer existing: " + basic_control[window].name())
                    nonexistent_windows += [window]

            if blacklisted(moduleInfo):
                print("auto turning OFF Vortex for new window '%s'" % (
                    moduleInfo[1]))
                basic_control[handle] = None
            else:
                print("auto turning ON Vortex for new window:")
                if spare_control:
                    basic_control[handle] = spare_control
                    try:
                        spare_control.attach(handle)
                        spare_control = BasicTextControl()
                    except natlink.BadWindow:
                        del basic_control[handle]
                else:
                    print("  not using spare control")
                    self.vortex_on()
                    spare_control = BasicTextControl()

        if moduleInfo[1]=="Spelling Window":
            control = basic_control.get(handle, None)
            if control != None:
                # DNS reuses spelling windows, so we load each
                # time a spelling window becomes visible:
                if not handle in self.visible_spelling_windows:
                    vocola_ext_keys.send_input("{shift}" + "{ctrl+Ins}")
                    time.sleep(.1)
                    text = vocola_ext_clipboard.clipboard_get()
                    print("loaded from spelling window: "+ repr(text))
                    control.set_buffer(text, True, True)
            self.track_visible_spelling_windows(handle)
        else:
            self.track_visible_spelling_windows()

    # remove BasicControls for spelling windows as soon as they
    # become non-visible (DNS reuses spelling Windows):
    def track_visible_spelling_windows(self, handle=-1):
        still_visible = []
        for window in self.visible_spelling_windows:
            if win32gui.IsWindowVisible(window):
                still_visible += [window]
        if handle != -1 and not handle in still_visible:
            still_visible += [handle]
        self.visible_spelling_windows = still_visible


    def vortex_off(self):
        handle  = win32gui.GetForegroundWindow()
        control = basic_control.get(handle, None)
        if control:
            control.unload()
        basic_control[handle] = None

    def vortex_off_everywhere(self):
        global auto_on, spare_control
        auto_on = False
        for ID in basic_control:
            control = basic_control[ID]
            if control:
                control.unload()
        basic_control.clear()
        if spare_control:
            spare_control.unload()
            spare_control = None

    def vortex_on(self):
        self.vortex_off()
        handle  = win32gui.GetForegroundWindow()
        control = BasicTextControl()
        try:
            control.attach(handle)
            basic_control[handle] = control
            return control
        except natlink.BadWindow:
            control.unload()
            return None

    def vortex_on_everywhere(self):
        global auto_on, spare_control
        auto_on = True
        self.vortex_on()
        if not spare_control:
            spare_control = BasicTextControl()
        

    def gotResults_start(self,words,fullResults):
        option = words[1]
        if option == "on":
            self.vortex_on()
        elif option == "off":
            self.vortex_off()

    def gotResults_all(self,words,fullResults):
        option = words[1]
        if option == "on":
            self.vortex_on_everywhere()
        elif option == "off":
            self.vortex_off_everywhere()

    def gotResults_load(self,words,fullResults):
        control = self.vortex_on()
        if not control: return
        option = words[1]
        if option == "load":
            selector = "{ctrl+home}{ctrl+shift+end}"
            unselect = "{ctrl+end}"
        elif option == "line":
            selector = "{home}{shift+end}"
            unselect = "{end}"
        natlink.playString("{shift}" + selector + "{ctrl+Ins}" + unselect)
        time.sleep(.1)
        text = vocola_ext_clipboard.clipboard_get()
        print("loaded: "+ repr(text))
        control.set_buffer(text)

    def gotResults_clip(self,words,fullResults):
        control = self.vortex_on()
        if not control: return
        text    = vocola_ext_clipboard.clipboard_get()
        print("loaded: "+ repr(text))
        control.set_buffer(text)



## 
## Starting up and stopping our command grammar:
## 

def pre_action(keys, action):
    if not basic_control:
        return

    if keys:
        print("pre-Vocola keys: " + repr(keys))
    if action:
        print("pre-Vocola action: " + repr(action))

    for ID in basic_control:
        control = basic_control[ID]
        if control:
            control.vocola_pre_action(keys, action)
vocola_ext_dragon_proxy.callback = pre_action


command = VortexGrammar()
command.initialize()

def unload():
    global command
    if command:
        command.terminate()
    command = None
    vocola_ext_dragon_proxy.callback = vocola_ext_dragon_proxy.do_nothing
    
    global catchAllGrammar
    if catchAllGrammar:
        catchAllGrammar.unload()
    catchAllGrammar = None
