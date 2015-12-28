###
### Vortex: attempt to provide basic text control for nonstandard applications
###

#
# code adapted from windict.py, which is copyright 1999 by Joel Gould
#

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

    # Initialization.  Create a DictObj instance and activate it for the
    # dialog box window.  All callbacks from the DictObj instance will go
    # directly to the dialog box.

    def initialize(self,dlg):
        self.dlg = dlg
        self.dictObj = natlink.DictObj()
        self.dictObj.setBeginCallback(dlg.onTextBegin)
        self.dictObj.setChangeCallback(dlg.onTextChange)
        self.dictObj.activate(dlg.GetSafeHwnd())

    # Call this function to cleanup.  We have to reset the callback
    # functions or the object will not be freed.
        
    def terminate(self):
        self.dictObj.deactivate()
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
    def __init__(self, handle):
        print "BasicTextControl attaching to window ID 0x%08x" % (handle)
        print "  with title '%s'" % (win32gui.GetWindowText(handle))
        self.my_handle = handle

        self.set_buffer_unknown()

        self.dictObj = VoiceDictation()
        self.dictObj.initialize(self)
        self.updateState()

    def unload(self):
        print "unloading BasicTextControl attached to window ID 0x%08x" % (self.my_handle)
        self.dictObj.terminate()
        self.dictObj = None

    def GetSafeHwnd(self):
        return self.my_handle


    def set_buffer(self, text):
        self.fake_prefix = 0
        # text in application around cursor except for
        # [0:self.fake_prefix]:
        self.text = text   

        end = len(text)
        # application selection:
        self.app_start, self.app_end = end, end  
        # what we claim is selected to DNS (can differ due to fake
        # prefix):
        self.selStart,  self.selEnd  = end, end  
        self.keys = ""  # any pending keystrokes for application

        self.showState()

    def set_buffer_unknown(self):
        # Effectively set state to no capitalization and no space
        # required before next word, hopefully not affecting language
        # model any:
        self.set_buffer("First, ")
        self.fake_prefix = self.app_end

    def showState(self):
        text = self.text
        print "text: '%s<%s>%s'" % (text[:self.selStart], 
                                    text[self.selStart:self.selEnd],
                                    text[self.selEnd:])
        if self.selStart != self.app_start or self.selEnd != self.app_end:
            print "      '%s[%s]%s'" % (text[:self.app_start], 
                                        text[self.app_start:self.app_end],
                                        text[self.app_end:])
        if self.keys != "":
            print "  postponed keys: '%s'" % (self.keys)



    #
    # Application control routines
    #
    # Invariant: after sending self.keys to application, the selection
    #            is [self.app_start,self.app_end) with the cursor
    #            before self.app_end.
    #
    # Invariants: self.app_{start,end} >= self.fake_prefix
    #             self.app_start <= self.app_end
    #

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
        if start < self.fake_prefix and end >= self.fake_prefix:
            fake_deletion = self.text[start:self.fake_prefix]
            if new_text.startswith(fake_deletion):
                print "nop overwrite of fake prefix ignored"
                start = max(self.fake_prefix, start)
                new_text = new_text[len(fake_deletion):]

        if start < self.fake_prefix and start != end:
            print
            print "***** ATTEMPT TO DELETE (PART OF) FAKE PREFIX DENIED!"
            print
        if end   < self.fake_prefix and new_text != "":
            print
            print "***** ATTEMPT TO INSERT IN FAKE PREFIX DENIED!"
            print
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
        # the following does not work because it causes onTextChange to be called:
        #natlink.playString("{shift}" + keys)

        keys = keys.replace("\n", "{enter}")
        vocola_ext_keys.send_input(keys)


    #
    # Routines for interacting with DNS:
    #

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
        #self.dictObj.setLock(1)
        print "onTextChange %d,%d,%s,%d,%d" % (delStart,delEnd,newText,selStart,selEnd)
        #print "onTextChange %d,%d,%s,%d,%d" % (delStart,delEnd,repr(newText),selStart,selEnd)

        self.replace(delStart, delEnd, newText)
        self.select(selStart, selEnd)
        self.selStart = selStart
        self.selEnd   = selEnd

        if delStart==delEnd and newText=="":
            # give spelling window time to pop up if it's going to:
            time.sleep(.1)

        keys = self.keys
        handle = win32gui.GetForegroundWindow()
        if handle == self.my_handle:
            print "sending: " + keys
            self.play_string(keys)
            keys = ""
        else:
            print "WARNING: delaying keys due to different active window, window ID 0x%08x" % (handle)

        self.keys = keys
        self.showState()
        print "end onTextChange"
        #self.dictObj.setLock(0)


    #
    # Routines for interacting with Vocola:
    #

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
            else:
                self.set_buffer_unknown()
            self.showState()
        else:
            if not keys:
                self.set_buffer_unknown()
                self.showState()                



#---------------------------------------------------------------------------
# Command grammar

# window ID -> BasicTextControl instance or None
basic_control = {}

# should we try and turn on vortex for each new window?
auto_on = False


class CommandGrammar(GrammarBase):

    gramSpec = """
        <start> exported = vortex (on | off);
        <all>   exported = vortex (on | off) everywhere;
        <load>  exported = vortex (load | line);
    """

    def initialize(self):
        print "Init Vortex"
        self.load(self.gramSpec)
        self.activateAll()
    
    def terminate(self):
        print "Exit vortex"
        self.vortex_off_everywhere()
        self.unload()


    def gotBegin(self,moduleInfo):
        if auto_on:
            handle  = win32gui.GetForegroundWindow()
            control = basic_control.get(handle, None)
            if not control:
                print "auto turning on vortex for new window"
                self.vortex_on()


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
        global auto_on
        auto_on = True
        self.vortex_on()
        

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



## 
## Starting up and stopping our command grammar:
## 

def pre_action(keys):
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
