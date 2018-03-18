### 
### Module clipboard:
### 

import string, time, random

import win32clipboard 
import win32con

from vocola_ext_variables import *


##
## Code for retrying clipboard access function failures:
##

# Opening the clipboard can fail if it is in use, so be prepared to retry:
def open_clipboard():
    retries = 0
    while retries < 300:
        try:
            win32clipboard.OpenClipboard()
            return
        except:
            print "retrying opening clipboard... " + str(retries)
            time.sleep( 0.050 )
            retries = retries + 1
    win32clipboard.OpenClipboard()

# GetClipboardData sometimes fails as well; unsure if retrying helps
def get_clipboard_data(format):
    retries = 0
    while retries < 10:
        try:
            return win32clipboard.GetClipboardData(format)
        except:
            print "retrying getting clipboard data... " + str(retries)
            time.sleep( 0.100 )
            retries = retries + 1
    return win32clipboard.GetClipboardData(format)


## 
## Getting and setting the contents of the Windows clipboard as TEXT
## 
##   Returns "" (or default if provided) when attempting to retrieve
##   from a clipboard which does not contain format(s) convertible to
##   CF_TEXT.
## 
##   Note that Windows text uses \r\n instead of \n.
## 

# Vocola function: Clipboard.Get,0-1
def clipboard_get(default=""):
    open_clipboard()
    result = default
    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
       result = get_clipboard_data(win32con.CF_TEXT)
    win32clipboard.CloseClipboard() 
    null = string.find(result, chr(0))
    if null>0:
        result = result[0:null]
    return result

# Vocola procedure: Clipboard.Set
def clipboard_set(aString):
    open_clipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_TEXT, aString) 
    win32clipboard.CloseClipboard() 


## 
## Same, but instead of using format CF_TEXT, uses format CF_UNICODETEXT
## 
##   Encodes Unicode as UTF-8.  UTF-8 (or Unicode) cannot be entered
## directly in Vocola 2 source code or sent as keyboard input (e.g.,
## directly or via SendDragonKeys or SendSystemKeys); Dragon
## NaturallySpeaking and hence Vocola 2 only supports Windows-1252,
## the default Windows character set.
## 
##   You can, however, use Eval to create UTF-8.  For example, given the
## following Vocola 2 function:
## 
##     UTF8(text) := EvalTemplate('u"$text".encode("UTF-8")');
## 
## You can write:
## 
##     paste Greek Delta    = Clipboard.SetUTF8(UTF8(\u03b4)) {ctrl+v};
##     paste Greek sentence = Clipboard.SetUTF8(UTF8("A lowercase Greek delta is written \u03b4 and an uppercase one is written \u0394.")) {ctrl+v};
## 
##   The input text to UTF8 is in Windows-1252 supplemented with Unicode
## character specifications of the form \uffff or \Uffffffff where the
## f's are hexadecimal digits specifying the code point of a Unicode character.
## 

# Vocola function: Clipboard.GetUTF8
def clipboard_get_UTF8():
    open_clipboard()
    result = ""
    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
       result = get_clipboard_data(win32con.CF_UNICODETEXT)
    win32clipboard.CloseClipboard() 
    null = string.find(result, chr(0))
    if null>0:
        result = result[0:null]
    result = result.encode('utf-8')
    return result

# Vocola procedure: Clipboard.SetUTF8
def clipboard_set_UTF8(aUTF8String):
    open_clipboard()
    win32clipboard.EmptyClipboard()
    aString = aUTF8String.decode('utf-8')  # throws UnicodeDecodeError
    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, aString) 
    win32clipboard.CloseClipboard() 


## 
## [Convenience procedures]
## 
## Saving and restoring the clipboard (as Unicode encoded as UTF-8)
## 
##     If the current clipboard contents do not support the Unicode
## format, then calling Save then Restore will store "" in the
## clipboard.
## 
## Optional name can be used to save and restore multiple clipboard values.
## 

# Vocola procedure: Clipboard.Save,0-1
def clipboard_save(name="save"):
    variable_set("clipboard:" + name, clipboard_get_UTF8())

# Vocola procedure: Clipboard.Restore,0-1
def clipboard_restore(name="save"):
    clipboard_set_UTF8(variable_get("clipboard:" + name))


## 
## Waiting for the clipboard contents to change
## 
##     Useful for slow applications (e.g., due to a high latency
## connection to a remote application).  Typical usage pattern is:
## 
##   Clipboard.Set(<unlikely>)
##   {ctrl+c}
##   Clipboard.WaitForNew(<unlikely>)
##   ...
##   ...Clipboard.Get()...
## 
## where <unlikely> is unlikely to be the new contents of the clipboard.
## 

class Timeout(Exception):
    pass

# Vocola procedure: Clipboard.WaitForNew,0-2
def clipboard_wait_for_new(old="", timeout=20):  # timeout in seconds
    try:
        timeout = int(timeout)
    except ValueError:
        raise ValueError("unable to convert '" + timeout.replace("'", "''") +
                         "' into an integer")
    delay = 0.1
    while timeout > 0:
        if clipboard_get(old + "!") != old:
            return
        time.sleep(delay)
        timeout -= delay
    raise Timeout("A timeout occurred while waiting for the clipboard contents to change")
