### 
### Module clipboard:
### 
### Author:  Mark Lillibridge
### Version: 1.0
### 

from __future__ import print_function

import string, time, random, sys

import win32clipboard 
import win32con

from vocola_ext_variables import *


##
## Wrapping error handling around underlying clipboard access functions:
##

def open_clipboard():
    # Opening the clipboard can fail if it is in use, so be prepared to retry:
    retries = 0
    while retries < 10:
        try:
            win32clipboard.OpenClipboard()
            return
        except:
            print("retrying opening clipboard... ")
            time.sleep(0.050)
            retries = retries + 1
    try:
        win32clipboard.OpenClipboard()
    except Exception as e:
        print("Error opening clipboard: " + type(e).__name__ + ": " + str(e), 
              file=sys.stderr)
        raise

def get_clipboard_data(format):  # -> result, error
    if not win32clipboard.IsClipboardFormatAvailable(format):
        return None, False
    try:
        result = win32clipboard.GetClipboardData(format)
        null = string.find(result, chr(0))
        if null>0:
            result = result[0:null]
        return result, False
    except Exception as e:
        print("Error getting data with format %d from clipboard: %s: %s" 
              % (format, type(e).__name__, e),
              file=sys.stderr)
        return None, True

def close_clipboard():
    try:
        win32clipboard.CloseClipboard() 
    except Exception as e:
        print("Error closing clipboard: " + type(e).__name__ + ": " + str(e), 
              file=sys.stderr)


## 
## Getting and setting the contents of the Windows clipboard as
## Windows-1252 text.
## 
##   Note that Windows text uses \r\n instead of \n.
## 

# 
# Getting:
# 
#   First tries format CF_TEXT; if that is unavailable or gives an
#   error, falls back to trying to use format CF_UNICODETEXT.  
# 
#   Returns "" (or default if provided) when attempting to retrieve
#   from a clipboard which does not contain format(s) convertible to
#   Windows-1252.  On clipboard error, throws unless default is
#   provided, which case it returns default.
# 

# Vocola function: Clipboard.Get,0-1
def clipboard_get(default=None):
    if default is None:
        default_value = ""
    else:
        default_value = default
    try:
        open_clipboard()
        try:
            result, error1 = get_clipboard_data(win32con.CF_TEXT)
            if result is not None:
                return result
            result, error2 = get_clipboard_data(win32con.CF_UNICODETEXT)
            if result is not None:
                try:
                    return result.encode('windows-1252')
                except:
                    print("Warning: clipboard contains Unicode text but "
                          "it is not convertible to Windows-1252", 
                          file=sys.stderr)
                    return default_value
            if error1 or error2:
                raise RuntimeError("unable to retrieve text from clipboard")
        finally:
            close_clipboard() 
    except:
        if default is None:
            raise
    return default_value


# Vocola procedure: Clipboard.Set
def clipboard_set(aString):
    open_clipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_TEXT, aString) 
    close_clipboard() 


## 
## Same, but instead of using format CF_TEXT, uses format
## CF_UNICODETEXT and can handle arbitrary Unicode.
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

# Vocola function: Clipboard.GetUTF8,0-1
def clipboard_get_UTF8(default=None):
    if default is None:
        default_value = ""
    else:
        default_value = default
    try:
        open_clipboard()
        try:
            result, error = get_clipboard_data(win32con.CF_UNICODETEXT)
            if result is not None:
                return result.encode('utf-8')
            if error:
                raise RuntimeError("unable to retrieve text from clipboard")
        finally:
            close_clipboard() 
    except:
        if default is None:
            raise
    return default_value

# Vocola procedure: Clipboard.SetUTF8
def clipboard_set_UTF8(aUTF8String):
    open_clipboard()
    win32clipboard.EmptyClipboard()
    aString = aUTF8String.decode('utf-8')  # throws UnicodeDecodeError
    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, aString) 
    close_clipboard() 


## 
## [Convenience procedures]
## 
## Saving and restoring the clipboard (as Unicode encoded as UTF-8)
## 
##     If the current clipboard contents do not support the Unicode
## format or reading the clipboard gives an error, then calling Save
## then Restore will store "" in the clipboard.
## 
## Optional name can be used to save and restore multiple clipboard values.
## 

# Vocola procedure: Clipboard.Save,0-1
def clipboard_save(name="save"):
    variable_set("clipboard:" + name, clipboard_get_UTF8(""))

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
