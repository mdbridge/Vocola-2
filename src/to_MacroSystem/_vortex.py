###
### Vortex: attempt to provide basic text control for nonstandard applications
###

#
# code adapted from windict.py, which is copyright 1999 by Joel Gould
#

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


#---------------------------------------------------------------------------
# What windows should not be automatically enabled when vortex on
# everywhere is in use.
#

#
# Don't ever automatically turn vortex on for windows belonging to
# these executables:
#
Blacklisted_applications = [
    # Dragon's own programs (except spelling window) have FullTextControl:
    #   DragonPad, dictation box, Command Browser, vocabulary editor, 
    #   NatLink messages but not (whitelisted) spelling window
    "natspeak.exe",
    

    # Dragon provides FullTextControl for most Microsoft office applications:
    "excel.exe",
    "winword.exe",
    "outlook.exe",
    "lync.exe",
    # PowerPoint does not have FullTextControl so benefits from vortex on

    # editors with text controls that Dragon gives FullTextControl for:
    "notepad.exe",
    "wordpad.exe",
    "win32pad.exe",

    # all controls that can be enabled, Dragon gives FullTextControl:
    "explorer.exe"
]

def blacklisted(moduleInfo):
    executable = os.path.basename(moduleInfo[0]).lower()

    if executable=="natspeak.exe" and moduleInfo[1]=="Spelling Window":
        return False

    return executable in Blacklisted_applications



#---------------------------------------------------------------------------
# VoiceDictation client
#
# This class provides a way of encapsulating the voice dictation (DictObj)
# of NatLink.  We can not derive a class from DictObj because DictObj is an
# exported C class, not a Python class.  But we can create a class that
# references a DictObj instance and makes it look like the class was
# inherited from DictObj.        

class VoiceDictation:

    def __init__(self):
        self.dictObj = None

    # Initialization.  Create a DictObj instance associated with the
    # given dialog box class, dlg.  If handle given, activate the
    # DictObj instance for window handle.  All callbacks from the
    # DictObj instance will go directly to the dialog class.
    def initialize(self, dlg, handle=None):
        self.dlg = dlg
        self.dictObj = natlink.DictObj()
        self.dictObj.setBeginCallback(dlg.onTextBegin)
        self.dictObj.setChangeCallback(dlg.onTextChange)
        self.my_handle = None
        self.activate(handle)

    # Activate the Dictobj instance for window handle (None means
    # deactivate).  If already activated for another window,
    # deactivate first.
    def activate(self, handle):
        if self.my_handle:
            self.dictObj.deactivate()
        self.my_handle = handle
        if handle:
            self.dictObj.activate(handle)

    # Call this function to cleanup.  We have to reset the callback
    # functions or the object will not be freed.
    def terminate(self):
        self.activate(None)
        self.dictObj.setBeginCallback(None)
        self.dictObj.setChangeCallback(None)
        self.dictObj = None

    # This makes it possible to access the member functions of the DictObj
    # directly as member functions of this class.
    def __getattr__(self,attr):
        try:
            if attr != '__dict__':
                dictObj = self.__dict__['dictObj']
                if dictObj is not None:
                    return getattr(dictObj,attr)
        except KeyError:
            pass
        raise AttributeError, attr


#---------------------------------------------------------------------------

class BasicTextControl:
    def __init__(self, handle=None):
        self.my_handle = handle
        if handle:
            print "BasicTextControl attaching to window ID 0x%08x" % (handle)
            print "  with title '%s'" % (win32gui.GetWindowText(handle))

        self.set_buffer_unknown()
        self.dictObj = VoiceDictation()
        self.dictObj.initialize(self, handle)
        if handle:
            self.updateState()

    def attach(self, handle=None):
        if self.my_handle:
            print "unattaching BasicTextControl attached to window ID 0x%08x" % (self.my_handle)
        if handle:
            print "BasicTextControl attaching to window ID 0x%08x" % (handle)
            print "  with title '%s'" % (win32gui.GetWindowText(handle))
        self.my_handle = handle
        self.dictObj.activate(handle)
        self.set_buffer_unknown()
        self.updateState()

    def unload(self):
        if self.my_handle:
            print "unloading BasicTextControl attached to window ID 0x%08x" % (self.my_handle)
        else:
            print "unloading BasicTextControl"
        self.dictObj.terminate()
        self.dictObj = None


    def set_buffer(self, text, unknown_prefix=False, select_all=False):
        buffer_text = ""
        if unknown_prefix:
            # Effectively set state to no capitalization and no space
            # required before next word, hopefully not affecting
            # language model any:
            buffer_text = "First, "
        start = len(buffer_text)
        self.fake_prefix = start

        buffer_text += text
        end = len(buffer_text)
        if not select_all:
            start = end

        # text in application around cursor except for
        # [0:self.fake_prefix]:
        self.text = buffer_text
        # application selection:
        self.app_start, self.app_end = start, end  
        # what we claim is selected to DNS (can differ due to fake
        # prefix):
        self.selStart,  self.selEnd  = start, end  
        self.keys = ""  # any pending keystrokes for application

        self.showState()

    def set_buffer_unknown(self):
        self.set_buffer("", True)

    def showState(self):
        text = self.text
        h = self.my_handle
        if not h: h = 0
        print "0x%08x: '%s<%s>%s'" % (h, text[:self.selStart], 
                                      text[self.selStart:self.selEnd],
                                      text[self.selEnd:])
        if self.selStart != self.app_start or self.selEnd != self.app_end:
            print "            '%s[%s]%s'" % (text[:self.app_start], 
                                              text[self.app_start:self.app_end],
                                              text[self.app_end:])
        if self.keys != "":
            print "  postponed keys: '%s'" % (self.keys)



    ##
    ## Application control routines
    ##
    ## Invariant: after sending self.keys to application, the selection
    ##            is [self.app_start,self.app_end) with the cursor
    ##            before self.app_end.
    ##
    ## Invariants: self.app_{start,end} >= self.fake_prefix
    ##             self.app_start <= self.app_end
    ##

    # returns end-start except counts each \r\n as 1 character:
    def distance(self, start, end):
        sign = 1
        if end < start:
            sign = -1
            start, end = end, start
        size = len(self.text[start:end].replace("\r", ""))
        return size * sign

    def unselect(self):
        size = self.distance(self.app_start, self.app_end) # selection size
        if size > 0:
            self.keys += "{shift+left " + str(size) + "}"
            self.app_end = self.app_start

    def move_to(self, target):
        self.unselect()
        move = self.distance(self.app_end, target)
        if move > 0:
            self.keys += "{right %d}" % (move)
        elif move < 0:
            self.keys += "{left %d}"  % (-move)
        self.app_start = self.app_end = target

    def select(self, start, end):
        # do not allow selecting fake prefix:
        start = max(self.fake_prefix, start)
        end   = max(self.fake_prefix, end)

        if start != self.app_start or end != self.app_end:
            self.move_to(start)
            size = self.distance(start, end)
            self.keys += "{shift+right " + str(size) + "}"
            self.app_end = end

    def replace(self, start, end, new_text):
        #while start<self.fake_prefix and start<end and len(new_text)>0:
        #    # attempt to replace a fake prefix character
        #    old = self.text[start]
        #    new = new_text[0]
        #    if old == new:
        #        print "  nop overwrite of leading fake prefix character ignored"
        #    elif old.lower() == new.lower():
        #        print "  case change of leading fake prefix character ignored"
        #    elif old == " " and new == "-":
        #        print "  attempt to hyphenate fake prefix ignored"
        #    else:
        #        break
        #    start += 1
        #    new_text = new_text[1:]

        #if start+1== self.fake_prefix and start<end and self.text[start]==" ":
        #    # trying to delete trailing space of fake prefix:
        #    print "  attempt to remove trailing space of fake prefix ignored"
        #    start += 1

        if start < self.fake_prefix and start != end:
            print >> sys.stderr
            print >> sys.stderr, \
                "***** ATTEMPT TO DELETE (PART OF) FAKE PREFIX DENIED!"
            print >> sys.stderr
        if end   < self.fake_prefix and new_text != "":
            print >> sys.stderr
            print >> sys.stderr, \
                "***** ATTEMPT TO INSERT IN FAKE PREFIX DENIED!"
            print >> sys.stderr
        start = max(self.fake_prefix, start)
        end   = max(self.fake_prefix, end)

        size = self.distance(start, end)
        if size != 0:
            self.move_to(end)
            self.keys += "{backspace " + str(size) + "}"
            self.text = self.text[0:start] + self.text[end:]
            self.app_start = self.app_end = start
        if new_text != "":
            self.move_to(start)
            self.keys += new_text.replace("\r", "").replace("{", "{{}")
            self.text = self.text[0:start] + new_text + self.text[start:]
            self.app_start = self.app_end = start + len(new_text)

    def play_string(self,keys):
        shift = "{" + VocolaUtils.name_for_shift() + "}"

        # the following does not work because it causes onTextChange to be called:
        #natlink.playString(shift + keys)

        keys = keys.replace("\n", "{enter}")
        vocola_ext_keys.send_input(shift + keys)


    ##
    ## Routines for interacting with DNS:
    ##

    # We get this callback just before recognition starts. This is our
    # chance to update the dictation object just in case we missed a change
    # made to the edit control.
    def onTextBegin(self,moduleInfo):
        self.updateState()
        pass

    # This subroutine transfers the contents and state of the edit control
    # into the dictation object.  We currently don't bother to indicate
    # exactly what changed.  The dictation object will compare the text we
    # write with the contents of its buffer and only make the necessary
    # changes (as long as only one contigious region has changed).
    def updateState(self):
        #print "updating state..."
        self.dictObj.setLock(1)
        self.dictObj.setText(self.text, 0, 0x7FFFFFFF)
        self.dictObj.setTextSel(self.selStart, self.selEnd)
        # assume everything except fake prefix is visible all the time:
        visStart,visEnd = self.fake_prefix, len(self.text)
        self.dictObj.setVisibleText(visStart, visEnd)
        self.dictObj.setLock(0)


    # We get this callback when something in the dictation object changes
    # like text is added or something is selected by voice.  We then update
    # the edit control to match the dictation object.
    def onTextChange(self,delStart,delEnd,newText,selStart,selEnd):
        print "onTextChange %d,%d, %s, %d,%d" % \
            (delStart,delEnd,repr(newText),selStart,selEnd)

        # corrections can attempt to remove the last space of the fake
        # prefix (e.g., correct Fred to .c); "select all", "scratch
        # that" also tries to do that.  Corrections can also attempt
        # to replace the prefix's trailing space with another space.
        if delStart+1==self.fake_prefix and delStart<delEnd and \
           self.text[delStart]==" ":
            # attempting to delete/replace trailing whitespace in fake prefix
            if len(newText)>0 and newText[0]==" ":
                print "  ignoring nop overwrite to trailing space in fake prefix"
                delStart += 1
                newText = newText[1:]
            else:
                print "  ignoring attempt to remove trailing space in fake prefix"
                delStart += 1
                selStart += 1
                selEnd   += 1

        if self.fake_prefix>0 and delStart<delEnd and newText!="":
            if delStart==self.fake_prefix and \
               self.text[delStart]==" " and newText[0]!=" ":
                print >> sys.stderr, \
                    "***** SPACE GUARD preserved leading space"
                delStart += 1
                selStart += 1
                selEnd   += 1
            if delEnd==len(self.text) and self.text[delEnd-1]==" " and \
               newText[-1]!=" ":
                print >> sys.stderr, \
                    "***** SPACE GUARD preserved trailing space"
                delEnd -= 1
                if selStart==delStart+len(newText) and selStart==selEnd:
                    selStart += 1
                    selEnd   += 1
                    

        self.replace(delStart, delEnd, newText)

        # prevent "select all" from selecting fake prefix:
        selStart = max(self.fake_prefix, selStart)
        selEnd   = max(self.fake_prefix, selEnd)

        self.select(selStart, selEnd)
        self.selStart = selStart
        self.selEnd   = selEnd

        if delStart==delEnd and newText=="":
            # give spelling window time to pop up if it's going to:
            time.sleep(.1)

        keys = self.keys
        handle = win32gui.GetForegroundWindow()
        if handle == self.my_handle:
            print "  sending: " + keys
            self.play_string(keys)
            keys = ""
        else:
            print "  WARNING: delaying keys due to different active window, window ID 0x%08x" % (handle)

        self.keys = keys
        self.showState()
        print "end onTextChange"


    ##
    ## Routines for interacting with Vocola:
    ##

    def vocola_pre_action(self, keys):
        if self.my_handle == win32gui.GetForegroundWindow():
            if self.keys != "":
                print "  sending: " + keys
                self.play_string(keys)
                self.keys = ""
            if keys and  keys.find("{") == -1:
                print "  assuming typed: " + keys
                self.replace(self.app_start, self.app_end, keys)
                self.selStart,  self.selEnd  = self.app_start, self.app_end
                self.keys = ""
                self.showState()
            else:
                self.set_buffer_unknown()
        else:
            if not keys:
                self.set_buffer_unknown()



#---------------------------------------------------------------------------
# Command grammar

# window ID -> BasicTextControl instance or None
basic_control    = {}

spare_control    = None

# should we try and turn on vortex for each new window?
auto_on = False

nonexistent_windows = []


class CommandGrammar(GrammarBase):

    gramSpec = """
        <start> exported = vortex (on | off);
        <all>   exported = vortex (on | off) everywhere;
        <load>  exported = vortex (load | line);
        <clip>  exported = vortex load clipboard;
    """

    def initialize(self):
        print "Init Vortex"
        self.visible_spelling_windows = []
        self.load(self.gramSpec)
        self.activateAll()
    
    def terminate(self):
        global spare_control
        print "Exit vortex"
        self.vortex_off_everywhere()
        if spare_control:
             spare_control.unload()
             spare_control = None
        self.unload()


    def gotBegin(self, moduleInfo):
        global spare_control, nonexistent_windows
        handle = moduleInfo[2]

        # unload controls for/forget about no longer existing windows:
        for window in nonexistent_windows:
            if basic_control[window]:
                basic_control[window].unload()
            del basic_control[window]
        nonexistent_windows = []

        control = basic_control.get(handle, -1)
        if control==-1 and auto_on:
            for window in basic_control:
                if not win32gui.IsWindow(window):
                    nonexistent_windows += [window]

            if blacklisted(moduleInfo):
                print "auto turning OFF vortex for new window '%s'" % (
                    moduleInfo[1])
                basic_control[handle] = None
            else:
                print "auto turning ON vortex for new window:"
                if spare_control:
                    basic_control[handle] = spare_control
                    spare_control.attach(handle)
                    spare_control = BasicTextControl()
                else:
                    print "  not using spare control"
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
                    print "loaded from spelling window: "+ repr(text)
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
        global auto_on
        auto_on = False
        for ID in basic_control:
            control = basic_control[ID]
            if control:
                control.unload()
        basic_control.clear()

    def vortex_on(self):
        self.vortex_off()
        handle  = win32gui.GetForegroundWindow()
        control = BasicTextControl(handle)
        basic_control[handle] = control
        return control

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
        print "loaded: "+ repr(text)
        control.set_buffer(text)

    def gotResults_clip(self,words,fullResults):
        control = self.vortex_on()
        text    = vocola_ext_clipboard.clipboard_get()
        print "loaded: "+ repr(text)
        control.set_buffer(text)



## 
## Starting up and stopping our command grammar:
## 

def pre_action(keys):
    if not basic_control:
        return
    print "pre-Vocola action: " + repr(keys)
    for ID in basic_control:
        control = basic_control[ID]
        if control:
            control.vocola_pre_action(keys)
VocolaUtils.callback = pre_action


command = CommandGrammar()
command.initialize()

def unload():
    global command
    if command:
        command.terminate()
    command = None
    VocolaUtils.callback = VocolaUtils.do_nothing
