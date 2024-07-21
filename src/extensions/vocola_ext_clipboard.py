# coding: Windows-1252
### 
### Module clipboard:
### 
### Author:  Mark Lillibridge
### Version: 2.1
### 

from __future__ import print_function

import random, re, sys, time

import win32clipboard 
import win32con

from vocola_ext_variables import *


##
## Converting between string kinds
##
##  "text"    is text encoded as Windows-1252 (bytes)
##  "unitext" is unicode
##

if sys.version_info[0] < 3:
    def _text_to_str(aText):
        return aText
    def _str_to_text(aStr):
        return aStr
    def _unitext_to_str(aUnitext):
        return aUnitext.encode('UTF-8')
    def _str_to_unitext(aStr):
        return aStr.decode('UTF-8')
else:
    def _text_to_str(aText):
        return aText.decode('Windows-1252', errors='replace').replace(u'\ufffd', '?')
    def _str_to_text(aStr):
        return aStr.encode('Windows-1252')
    def _unitext_to_str(aUnitext):
        return aUnitext
    def _str_to_unitext(aStr):
        return aStr

    
##
## Wrapping error handling around underlying clipboard access functions:
##

class BadClipboardFormat(LookupError):
    pass

def open_clipboard():
    # Opening the clipboard can fail if it is in use, so be prepared to retry:
    retries = 0
    while retries < 10:
        try:
            win32clipboard.OpenClipboard()
            return
        except:
            print("retrying opening clipboard... ")
            time.sleep(0.050)  # 50 ms
            retries = retries + 1
    try:
        win32clipboard.OpenClipboard()
    except Exception as e:
        print("Error opening clipboard: " + type(e).__name__ + ": " + str(e), 
              file=sys.stderr)
        raise

def get_clipboard_text():  # -> bytes
    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
        try:
            result = win32clipboard.GetClipboardData(win32con.CF_TEXT)
            null = result.find(b'\x00')
            if null>0:
                result = result[0:null]
            return result
        except Exception as e:
            if not win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                raise
    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
        try:
            result = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            return result.encode('Windows-1252')
        except UnicodeEncodeError:
            raise BadClipboardFormat("clipboard format is not translatable to Windows-1252")
    raise BadClipboardFormat("clipboard format is not CF_TEXT or CF_UNICODETEXT")

def get_clipboard_unitext():  # -> unicode
    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
        return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
    raise BadClipboardFormat("clipboard format is not CF_UNICODETEXT")

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
#   from a clipboard that does not contain format(s) convertible to
#   Windows-1252.  On clipboard error, throws unless default is
#   provided, which case it returns default.
# 

# Vocola function: Clipboard.Get,0-1
def clipboard_get(default=None):
    try:
        open_clipboard()
        try:
            return _text_to_str(get_clipboard_text())
        finally:
            close_clipboard() 
    except BadClipboardFormat:
        if default is None:
            return ""
    except:
        if default is None:
            raise
    return default

# Vocola procedure: Clipboard.Set
def clipboard_set(aString):
    open_clipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_TEXT, _str_to_text(aString))
    finally:
        close_clipboard() 


## 
## Same, but instead of using format CF_TEXT, uses format
## CF_UNICODETEXT and can handle arbitrary Unicode.
## 
##   Internally Vocola 2 usually uses the Windows-1252 character set,
## the default Windows character set.  This is because Dragon
## NaturallySpeaking only supports Windows-1252.  Only that character
## set is supported for Vocola 2 source code or for sending as
## keyboard input (e.g., directly or via SendDragonKeys or
## SendSystemKeys).
## 
##   In order for this extension to support full Unicode, it either
## encodes Unicode as UTF-8 (Python 2 case) or uses a wider range of
## Unicode characters than Vocola 2 supports for many operations
## (Python 3 case).  Thus, SetUnicode is not convenient for setting
## the clipboard to a constant Unicode string and the results of
## processing Unicode obtained via GetUnicode is usually sent to
## applications via pasting.
## 
##   If you want to copy a Unicode literal to the clipboard, use
## instead SetUnicodeLiteral(-).  It takes a Unicode string
## representation per Python's u'...' syntax.  For example, you can
## write:
## 
##     paste Greek Delta    = Clipboard.SetUnicodeLiteral(\u03b4)) {ctrl+v};
##     paste Greek sentence = Clipboard.SetUnicodeLiteral("A lowercase Greek delta is written \u03b4 and an uppercase one is written \u0394.")) {ctrl+v};
## 
##   The input text to SetUnicodeLiteral is supplemented with Unicode
## character specifications of the form \uffff or \Uffffffff where the
## f's are hexadecimal digits specifying the code point of a Unicode
## character.
## 
##   GetUnicodeLiteral will convert the Unicode clipboard to such a
## suitable representation.
## 

# Vocola function: Clipboard.GetUnicode,0-1
def clipboard_get_unicode(default=None):
    try:
        open_clipboard()
        try:
            return _unitext_to_str(get_clipboard_unitext())
        finally:
            close_clipboard() 
    except BadClipboardFormat:
        if default is None:
            return ""
    except:
        if default is None:
            raise
    return default

# Vocola procedure: Clipboard.SetUnicode
def clipboard_set_unicode(aStr):
    open_clipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, _str_to_unitext(aStr))
    finally:
        close_clipboard() 

# Vocola procedure: Clipboard.SetUnicodeLiteral
def clipboard_set_unicode_literal(aStr):
     expression = "u'" + aStr + "'"
     unicode = eval(expression)
     clipboard_set_unicode(_unitext_to_str(unicode))

# Vocola function: Clipboard.GetUnicodeLiteral,0-1
def clipboard_get_unicode_literal(default=None):
    u = _str_to_unitext(clipboard_get_unicode(default))
    if sys.version_info[0] < 3:
        # deal w/ narrow Python 2 build, which splits \U00010000 into 2 characters:
        pattern = re.compile(u'(?:[\ud800-\udbff][\udc00-\udfff])|.', re.DOTALL)
        chars = pattern.findall(u)
    else:
        chars = list(u)
    result = b''
    for c in chars:
        try:
            result += c.encode('Windows-1252')
        except:
            result += c.encode('unicode-escape')
    return _text_to_str(result)



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
    variable_set("clipboard:" + name, clipboard_get_unicode(""))

# Vocola procedure: Clipboard.Restore,0-1
def clipboard_restore(name="save"):
    clipboard_set_unicode(variable_get("clipboard:" + name))


## 
## Wait for the clipboard contents to change to something different
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


## 
## Wait for the clipboard contents to become something specific
## 
##     Useful for synchronizing with slow applications (e.g., due to a
## high latency connection to a remote application).  Typical usage
## pattern is:
## 
##   <set of keyboard commands to the application>
##   <keyboard command to the application to set the clipboard to "foo">
##   Clipboard.WaitForValue("foo")
## 

# Vocola procedure: Clipboard.WaitForValue,0-2
def clipboard_wait_for_value(value, timeout=20):  # timeout in seconds
    try:
        timeout = int(timeout)
    except ValueError:
        raise ValueError("unable to convert '" + timeout.replace("'", "''") +
                         "' into an integer")
    delay = 0.1
    while timeout > 0:
        if clipboard_get(value + "!") == value:
            return
        time.sleep(delay)
        timeout -= delay
    raise Timeout("A timeout occurred while waiting for the clipboard contents to become " 
                  + repr(value))



##
## Test code
##

if __name__ == "__main__":
    print("Python version: ", sys.version_info[0])

    def try_read():
        normal = "<threw>"
        try:
            normal = clipboard_get()
            print("  normal: ", repr(normal), type(normal))
        except:
            print ("  normal threw")
            import traceback
            traceback.print_exc()
        normal_with_default = clipboard_get('DEFAULT')
        if normal != normal_with_default:
            print("  Normal with default: " + repr(normal_with_default))
        u = "<threw>"
        try:
            u = clipboard_get_unicode()
            print("  Unicode: " + repr(u), type(u))
        except:
            print("  Unicode threw")
            import traceback
            traceback.print_exc()
        ud = clipboard_get_unicode('DEFAULT')
        if u != ud:
            print("  Unicode with default: " + repr(ud))
        l = clipboard_get_unicode_literal('DEFAULT')
        print("  Literal: ", repr(l))

    def try_setter(target, setter_name, setter):
        print("set", setter_name, repr(target))
        try:
            setter(target)
        except:
            print("  setter threw")
            import traceback
            traceback.print_exc()
            return
        try_read()
        

    print("Starting clipboard:")
    try_read()

    try_setter("fo€o naïve", "text", clipboard_set)
    try_setter(u'\u03b4', "text", clipboard_set)

    target = u'Naïve.  A lowercase Greek delta is written \u03b4 and an uppercase one is written \u0394.'
    try_setter(_unitext_to_str(target), "Unicode", clipboard_set_unicode)
    target = u'euro €, rocket: \U0001f680, Na\xefve'
    try_setter(_unitext_to_str(target), "Unicode", clipboard_set_unicode)

    target = r'Naïve.  A lowercase Greek delta is written \u03b4 and an uppercase one is written \u0394.'
    try_setter(target, "Unicode literal", clipboard_set_unicode_literal)
    target = r't \x34 \x81 \u20ac \u2000 \U0001f680'
    try_setter(target, "Unicode literal", clipboard_set_unicode_literal)

    print()
