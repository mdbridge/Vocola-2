# vcl2py:  Convert Vocola voice command files to NatLink Python "grammar"
#          classes implementing those voice commands
#
# Usage: python vcl2py.py [<option>...] <inputFileOrFolder> <outputFolder>
# Where <option> can be:
#   -debug <n>             -- specify debugging level 
#                               (0 = no info, 1 = show statements, 
#                                2 = detailed info)
#   -extensions <filename> -- specify filename containing extension interface 
#                             information
#   -f                     -- force processing even if file(s) not out of date
#   -INI_file <filename>   -- specify filename of INI file to use
#   -log_file <filename>   -- specify filename to log to
#   -log_stdout            -- log to standard out instead of a file
#   -max_commands <n>      -- specify maximum number of commands per utterance
#   -numbers <s0>,<s1>,<s2>,...
#                          -- use spoken form <s0> instead of "0" in ranges,
#                             <s1> instead of "1" in ranges, etc.
#   -q                     -- ignore any INI file
#   -suffix <s>            -- use suffix <s> to distinguish Vocola generated 
#                             files (default is "_vcl")
#
#
# Copyright (c) 2000-2003, 2005, 2007, 2009-2012 by Rick Mohr.
# 
# Portions Copyright (c) 2012-15 by Hewlett-Packard Development Company, L.P.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# 12/26/2013  ml  Added new built-ins, If and When
#  4/23/2013  ml  Any series of one or more terms at least one of which
#                 is not optional or <_anything> can now be optional.
#  5/01/2012  ml  Ported to Python line by line, parser replaced with 
#                 lexer/traditional parser
#  5/14/2011  ml  Selected numbers in ranges can now be spelled out
# 11/28/2010  ml  Extensions can now be called
# 05/28/2010  ml  Print_* functions -> unparse_* to avoid compiler bug
# 05/08/2010  ml  Underscores now converted to spaces by VocolaUtils
# 03/31/2010  ml  Runtime errors now caught and passed to handle_error along 
#                 with filename and line number of error location
# 01/27/2010  ml  Actions now implemented via direct translation to
#                 Python, with no delay of Dragon calls, etc.
# 01/01/2010  ml  User functions are now implemented via unrolling
# 12/30/2009  ml  Eval is now implemented via transformation to EvalTemplate
# 12/28/2009  ml  New EvalTemplate built-in function
# 09/06/2009  ml  New $set directive replaces old non-working sequence directive
#                 binary Use Command Sequences replaced by n-ary MaximumCommands
# 01/19/2009  ml  Unimacro built-in added
# 12/06/2007  ml  Arguments to Dragon functions are now checked for proper 
#                 number and datatype
# 06/02/2007  ml  Output filenames are now mangled in an invertable fashion
# 05/17/2007  ml  Eval now works correctly on any action instead of just word
#                 and reference actions.
# 05/15/2007  ml  Variable substitution regularized
#                 Empty context statements now work
# 04/18/2007  ml  (Function) Names may now start with underscores
# 04/08/2007  ml  Quotation marks can be escaped by doubling
# 01/03/2005  rm  Commands can incorporate arbitrary dictation 
#                 Enable/disable command sequences via ini file
# 04/12/2003  rm  Case insensitive window title comparisons
#                 Output e.g. "emacs_vcl.py" (don't clobber existing NatLink 
#                 files)
# 11/24/2002  rm  Option to process a single file, or only changed files
# 10/12/2002  rm  Use <any>+ instead of exporting individual NatLink commands
# 10/05/2002  rm  Generalized indenting, emit()
# 09/29/2002  rm  Built-in function: Repeat() 
# 09/15/2002  rm  User-defined functions
# 08/17/2002  rm  Use recursive grammar for command sequences
# 07/14/2002  rm  Context statements can contain '|'
#                 Support environment variable references in include statements
# 07/06/2002  rm  Function arguments allow multiple actions
#                 Built-in function: Eval()!
# 07/05/2002  rm  New code generation using VocolaUtils.py
# 07/04/2002  rm  Improve generated code: use "elif" in menus
# 06/02/2002  rm  Command sequences!
# 05/19/2002  rm  Support "include" statement
# 05/03/2002  rm  Version 1.1
# 05/03/2002  rm  Handle application names containing '_'
# 05/03/2002  rm  Convert '\' to '\\' early to avoid quotewords bug
# 02/18/2002  rm  Version 0.9
# 12/08/2001  rm  convert e.g. "{Tab_2}" to "{Tab 2}"
#                 expand in-string references (e.g. "{Up $1}")
# 03/31/2001  rm  Detect and report unbalanced quotes
# 03/06/2001  rm  Improve error checking for complex menus
# 02/24/2001  rm  Change name to Vocola
# 02/18/2001  rm  Handle terms containing an apostrophe
# 02/06/2001  rm  Machine-specific command files
# 02/04/2001  rm  Error on undefined variable or reference out of range
# 08/22/2000  rm  First usable version

# Style notes:
#   Global variables are capitalized (e.g. Definitions)
#   Local variables are lowercase    (e.g. in_folder)

import re
import os
import sys

from vcl2py.ast  import *
from vcl2py.emit import output
from vcl2py.transform import transform


# ---------------------------------------------------------------------------
# Main control flow

VocolaVersion = "2.8.4"

def main():
    global Debug, Default_maximum_commands, Error_encountered, Force_processing, In_folder, Default_number_words, LOG

    # flush output after every print statement:
    #sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)    # <<<>>>

    # Debug states: 0 = no info, 1 = show statements, 2 = detailed info
    Debug                    = 0    
    Default_maximum_commands = 1
    Error_encountered        = False
    Force_processing         = False
    Default_number_words     = {}


    extensions_file          = ""
    ignore_INI_file          = False
    ini_file                 = ""
    log_file                 = ""
    log_to_stdout            = False
    suffix                   = "_vcl"

    argv = sys.argv[1:]
    while len(argv) > 0:
        option = argv[0]
        if not option[0:1] == "-": break
        argv.pop(0)

        if   option == "-f":          Force_processing = True; continue
        elif option == "-log_stdout": log_to_stdout    = True; continue
        elif option == "-q":          ignore_INI_file  = True; continue
        
        if len(argv) == 0:
            usage("missing argument for option " + option)
        argument = argv.pop(0)

        if   option == "-debug":        Debug                    = safe_int(argument, 1)
        elif option == "-extensions":   extensions_file          = argument
        elif option == "-INI_file":     ini_file                 = argument
        elif option == "-log_file":     log_file                 = argument
        elif option == "-max_commands": Default_maximum_commands = safe_int(argument, 1)
        elif option == "-numbers": 
            Default_number_words = {}
            numbers = re.split(r'\s*,\s*', argument.strip())
            i = 0
            for number in numbers: 
                if number != "":
                    Default_number_words[i] = number
                i = i + 1
        elif option == "-suffix":       suffix                   = argument
        else:
            usage("unknown option: " + option)

    if len(argv) == 2: 
        inputFileOrFolder = argv[0]
        out_folder        = argv[1]
    else: 
        usage()


    in_file = ""
    if os.path.isdir(inputFileOrFolder): 
        # inputFileOrFolder is an entire folder
        In_folder = inputFileOrFolder
    elif os.path.exists(inputFileOrFolder): 
        # inputFileOrFolder is a single file
        In_folder, filename = os.path.split(inputFileOrFolder)
        if In_folder == "": In_folder = "."
        in_file, extension  = os.path.splitext(filename)
        if not extension == ".vcl":
            fatal_error("Input file '" + inputFileOrFolder + "' must end in '.vcl'")
    else: 
        fatal_error("Nonexistent input filename '" + inputFileOrFolder + "'")
    if log_file == "": log_file = In_folder + os.sep + "vcl2py_log.txt"
    if ini_file == "": ini_file = In_folder + os.sep + "Vocola.INI"

    if log_to_stdout:
        LOG = sys.stdout
    else:
        try:
            LOG = open(log_file, "w")
        except IOError, e:
            fatal_error("Unable to open log file '" + log_file + "' for writing: " + str(e))


    if not ignore_INI_file:   read_ini_file(ini_file)
    if extensions_file != "": read_extensions_file(extensions_file)
    if Debug >= 1: 
        print >>LOG, ("default maximum commands per utterance = " + str(Default_maximum_commands))

    initialize_token_properties()
    convert_files(in_file, out_folder, suffix)
    
    LOG.close()
    if not Error_encountered: 
        if not log_to_stdout: os.remove(log_file)
        sys.exit(0)
    else:
        sys.exit(1)

def usage(message=""):
    global VocolaVersion

    if message != "":
        print >>sys.stderr, "vcl2py.py: Error: " + message

    print >>sys.stderr, '''
Usage: python vcl2py.pl [<option>...] <inputFileOrFolder> <outputFolder>
  where <option> ::= -debug <n> | -extensions <filename> | -f
                  |-INI_file <filename> | -log_file <filename> | -log_stdout
                  | -max_commands <n> | -q | -suffix <s>

'''
    print >>sys.stderr, "Vocola 2 version: " + VocolaVersion
    sys.exit(99)

def fatal_error(message):
    print >>sys.stderr, "vcl2py.py: Error: " + message
    sys.exit(99)

def safe_int(text, default=0):
    try:
        return int(text)
    except ValueError:
        return default

def read_ini_file(ini_file):
    global Debug, Default_maximum_commands, LOG

    if Debug >= 1: print >>LOG, "INI file is '" + ini_file + "'"
    try:
        input = open(ini_file)
        for line in input:
            match = re.match(r'^(.*?)=(.*)$', line)
            if not match: continue
            keyword = match.group(1)
            value   = match.group(2)
            if keyword == "MaximumCommands": 
                Default_maximum_commands = safe_int(value, 1)
    except IOError, e:
        return

def read_extensions_file(extensions_filename):
    global Debug, Extension_functions, LOG
    if Debug >= 1: print >>LOG, "extensions file is '" + extensions_filename + "'"
    try:
        input = open(extensions_filename)
        for line in input:
            match = re.match(r'([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,\n\r]*)[\n\r]*$', line)
            if not match:
                continue

            extension_name    = match.group(1)
            minimum_arguments = safe_int(match.group(2), 1)
            maximum_arguments = safe_int(match.group(3), 1)
            needs_flushing    = safe_int(match.group(4), 1) != 0
            module_name       = match.group(5)
            function_name     = match.group(6)
            
            Extension_functions[extension_name] = [minimum_arguments, maximum_arguments, needs_flushing, module_name, function_name]

    except IOError, e:
        return

def convert_files(in_file, out_folder, suffix):
    global In_folder, LOG

    if in_file != "": 
        # Convert one file
        convert_file(in_file, out_folder, suffix)
    else: 
        # Convert each .vcl file in folder 
        machine = os.environ.get("COMPUTERNAME", "").lower()  
        try:
            for filename in os.listdir(In_folder):
                match = re.match(r'^(.+)\.vcl$', filename)
                if match:
                    in_file = match.group(1)
                    # skip machine-specific files for different machines
                    match = re.search(r'@(.+)', in_file)
                    if (match and match.group(1).lower() != machine): continue
                    convert_file(in_file, out_folder, suffix)
        except IOError, e:
            fatal_error("Couldn't open/list folder '" + In_folder + "': " + str(e))

# Convert one Vocola command file to a .py file

  # in_file is just the base name; actual pathname is
  # <In_folder>/<in_file>.vcl where / is the correct separator
def convert_file(in_file, out_folder, suffix):
    global Debug, Definitions, Error_count, Error_encountered, File_empty
    global Force_processing, Forward_references, Function_definitions, Functions
    global In_folder, Include_stack_file, Include_stack_line, Included_files
    global Input_name, Last_include_position, Module_name
    global Default_number_words, Number_words
    global Should_emit_dictation_support
    global Statement_count, Default_maximum_commands, Maximum_commands

    out_file = convert_filename(in_file)

    # The global Module_name is used below to implement application-specific 
    # commands in the output Python
    Module_name = out_file.lower()
    # The global Input_name is used below for error logging
    Input_name = in_file + ".vcl"

    out_file = out_folder + os.sep + out_file + suffix + ".py"

    in_path = In_folder + os.sep + Input_name
    if os.path.exists(in_path):
        in_time  = os.path.getmtime(in_path)
        out_time = 0
        if os.path.exists(out_file): out_time = os.path.getmtime(out_file)
        if in_time<out_time and not Force_processing:
            return

    
    Definitions                   = {}
    Functions                     = {}
    Function_definitions          = {}
    
    Forward_references            = []
    Included_files                = []
    Include_stack_file            = []
    Include_stack_line            = []
    Last_include_position         = None
    Error_count                   = 0
    File_empty                    = True
    Should_emit_dictation_support = False
    Statement_count               = 1
    
    if Debug>=1: print >>LOG, "\n=============================="

    statements = parse_file(Input_name)
    if Error_count == 0: 
        check_forward_references()
    
    # Prepend a "global" context statement if necessary
    if len(statements) == 0 or statements[0]["TYPE"] != "context": 
        context            = {}
        context["TYPE"]    = "context"
        context["STRINGS"] = [""]
        statements.insert(0, context)
    #print >>LOG, unparse_statements(statements),
    statements = transform(statements, Function_definitions, Statement_count)
    #print >>LOG, unparse_statements(statements),
    
    # Handle $set directives:
    Maximum_commands = Default_maximum_commands
    Number_words     = Default_number_words
    for statement in statements: 
        if statement["TYPE"] == "set": 
            key = statement["KEY"]
            if key == "MaximumCommands": 
                Maximum_commands = safe_int(statement["TEXT"], 1)
            elif key == "numbers": 
                Number_words = {}
                numbers = re.split(r'\s*,\s*', statement["TEXT"].strip())
                i = 0
                for number in numbers: 
                    if number != "":
                        Number_words[i] = number
                    i = i + 1

    if Error_count > 0: 
        if Error_count == 1:
            s = ""
        else:
            s = "s"
        print >>LOG, "  " + str(Error_count) + " error" + s + " -- file not converted."
        Error_encountered = True
        return
    if File_empty: 
        # Write empty output file, for modification time comparisons 
        try:
            OUT = open(out_file, "w")
            OUT.close()
        except IOError, e:
            print >> LOG, "Couldn't open output file '" + out_file + "' for writing"
        print >>LOG, "Converting " + Input_name
        print >>LOG, "  Warning: no commands in file."
        return

    from vcl2py.emit import output
    #emit_output(out_file, statements)
    output(out_file, statements,
           VocolaVersion,
           Should_emit_dictation_support,
           Module_name,
           Number_words, Definitions, Maximum_commands,
           Extension_functions)

# 
# Warning: this code is very subtle and has a matching inverse function in 
# _vocola_main.py, getSourceFilename.
#
# Ensures:
#   maps [\w@]* to [\w]*, [-\w@]* to [-\w]*
#   is invertable
#   result starts with _ iff input did
#   does not change any text before the first @ or end of string, whichever 
#     comes first
# 
def convert_filename(in_file):
    name = in_file
    
    # ensure @ acts as a module name terminator for NatLink
    name = re.sub(r'(.)@', r'\1_@', name)
    
    marker = "e_s_c_a_p_e_d__"

    match = re.match(r'([^@]*?)((@(.*))?)$', name)
    module = match.group(1)
    suffix = match.group(2)
    
    if suffix == "" and name.find(marker) == -1: return name
    
    suffix = suffix.replace('_','___')
    suffix = suffix.replace('@','__a_t__')
    return module + marker + suffix


# ---------------------------------------------------------------------------
# Lexing routines
#
# A Vocola 2.8+ pseudo-token is defined be one of the following:
#
#     ( ) [ ] | , = ; := :
#
#     a quotation using "s or 's where the delimiter may be escaped by
#       doubling it; e.g., 'can''t' for can't
#  
#     an unterminated quotation: as above but with the final delimiter
#        replaced with a newline
#
#     a bare word: a sequence of one or more unquoted characters that
#       may not include the following characters or a colon at the
#       end:
#         ( ) [ ] | , = ' " # \s
#
#   The longest pseudo-token starting at a given location is always
# preferred (e.g., := over :).  Pseudo-tokens may be separated by
# whitespace (\s*) and #-to-end-of-line comments (#.*$).  Any program
# plus a newline can be divided up into a sequence of such
# pseudo-tokens.
#
#
#   Pseudo-tokens are converted into actual tokens by converting
# maximal subsequences of pseudo-tokens that do not contain the ;
# pseudo-token or contain the : pseudo-token except at the end into
# context statement tokens.  The text of the context statement token
# is the entire text (including any interleaving whitespace and
# comments!) from the start of the first pseudo-token of the
# subsequence to the end of the : pseudo-token.  Thus, for example,
# "foo; b ar:err:(dd)" tokenizes into foo, ;, b ar:err:, (, dd, and ),
# with "b ar:err:" being a single context statement token.  Finally,
# a EOF token is added at the end.
#
#   This handling of context statements is baroque to say the least,
# but is necessary to ensure sufficient backward compatibility with
# the original syntax, which treats whitespace in context statements
# (only) as significant.  We expect to depreciate context statements
# in the future in favor of more sane syntax.
#
#   Backward compatibility note: originally, the final : of a context
# statement had to be followed by whitespace (\s); this allowed bare
# words to end in a : so long as they were not followed by whitespace.
# We have chosen to remove this undesirable whitespace sensitivity by
# outlawing such bare words.  Instead, we treat such input as the end
# of a context statement.
#


## 
## Dividing up the input into tokens:
## 

Singles      = r'()\[\],|;='

  # characters not allowed anywhere in a bare word:
Excluded     = r'\s\#\'\"' + Singles

# 
# Every string ending with a newline can be divided into a continuous
# series of these, with each pseudo token being as greedy as possible.
#
# Exception: whitespace (including comments) at the end of the string
# doesn't match.
#
Pseudo_token = r'(?x) '                                                  + \
               r' \s* (?: \#.*\n \s* )* '                                + \
               r' ( [^:'+Excluded+r']+ (?: :+ [^:'+Excluded+r']+ )* '    + \
               r' | ['+Singles+r'] '                                     + \
               r' | \" [^\"\n]* (?: \"\" [^\"\n]* )* [\"\n] '            + \
               r' | \' [^\'\n]* (?: \'\' [^\'\n]* )* [\'\n] '            + \
               r' | := '                                                 + \
               r' | :+ [^:'+Excluded+r']+ (?: :+ [^:'+Excluded+r']+ )* ' + \
               r' | : '                                                  + \
               r' )'

Pseudo       = re.compile(Pseudo_token)


Token_properties = {}

  # token_properties should have definitions for:
  #   ( ) [ ] | , = ; := : ' " \n b EOF
  # where b denotes a bare word and \n an unterminated quotation
def initialize_tokenizer(token_properties):
    global Token_properties

    properties = token_properties
    for i in xrange(0,256):
        c = chr(i)
        token_properties[c + ':']  = token_properties[':']
        token_properties[c + '"']  = token_properties['"']
        token_properties[c + "'"]  = token_properties["'"]
        token_properties[c + "\n"] = token_properties["\n"]

    Token_properties = properties

  # requires: text ends in a newline
  # requires: initialize_tokenizer(-) has already been called
def tokenize(text):  # -> [[kind, token text, offset in text of token start]*]
    global Token_properties, Pseudo
    properties               = Token_properties
    token_bare_properties    = properties["b"]
    token_context_properties = properties[":"]
    pseudo                   = Pseudo

    tokens          = []
    start           = 0
    statement_start = 0
    while True:
        match = pseudo.match(text, start)
        if not match:
            tokens.append([properties["EOF"], "", len(text)])
            return tokens

        start = match.end(0)
        token = match.group(1)
        kind  = properties.get(token[-2:], token_bare_properties)
        tokens.append([kind, token, match.start(1)])

        if token == ";":
            statement_start = len(tokens)
        elif kind == token_context_properties:
            beginning = tokens[statement_start][2]
            token     = text[beginning:start]
            tokens[statement_start:] = [[kind, token, beginning]]
            statement_start = len(tokens)


## 
## Loading the tokens of a string for processing:
## 

  # (initial) tokenizer state:
Text          = ""
Tokens        = []
Offset        = -1  # uninitialized state for implementation error detection
Peeks         = 0
Scan_limit    = 0
Scan_newlines = 0


  # requires: initialize_token_properties(-) has already been called
def load_tokens(text):
    global Text, Offset, Peeks, Tokens, Scan_limit, Scan_newlines

    if text[-1:] != "\n": text += "\n"

    Text          = text
    Tokens        = tokenize(text)

    Offset        = 0
    Peeks         = 0
    Scan_limit    = 0
    Scan_newlines = 0


## 
## Moving through the list of tokens:
## 

def peek(kind):
    global Tokens, Offset, Peeks
    Peeks |= kind
    return Tokens[Offset][0] & kind

def eat(kind = -1):
    global Tokens, Offset, Peeks

    if not (Tokens[Offset][0] & kind):
        Peeks |= kind
        syntax_error(Peeks, Tokens[Offset][0], Tokens[Offset][1], 
                     get_current_position())

    Peeks   = 0
    Offset += 1
    return Tokens[Offset-1][1]

def get_current_position():
    global Text, Offset, Tokens
    if Offset == -1: 
        implementation_error("get_current_position() called before open_text")
    return [Text, Offset, Tokens[Offset][2]]

def get_last_position():
    global Text, Offset, Tokens
    if Offset < 1:
        implementation_error("get_last_position() called before open_text/eat")
    return [Text, Offset-1, Tokens[Offset-1][2]]

def adjust_position(position, amount):
    text, tokens_offset, text_offset = position
    return [text, tokens_offset, text_offset+amount]

  # requires: load_tokens(-) has not been called since this position was captured
def rewind(position):
    global Offset
    Offset = position[1]
    Peeks  = 0


## 
## Getting information about positions:
## 

def get_line_number(position):
    global Text, Scan_limit, Scan_newlines

    text, dummy, text_offset = position

    if text is Text:                  # compare by pointer values
        if text_offset < Scan_limit:
            Scan_limit = Scan_newlines = 0
        Scan_newlines += text[Scan_limit:text_offset].count("\n")
        Scan_limit = text_offset
        return Scan_newlines + 1

    return text[:text_offset].count("\n")+ 1

def get_column_number(position):
    text, dummy, text_offset = position

    last_newline = text.rfind("\n", 0, text_offset)
    line_start = last_newline + 1

    return text_offset - line_start

  # returns line without it's terminating newline:
def get_line(position):
    text, dummy, text_offset = position

    last_newline = text.rfind("\n", 0, text_offset)
    line_start = last_newline + 1

    line_end = text.find("\n", line_start)

    return text[line_start:line_end]

def point_to_position(position):
    line   = get_line(position)
    column = get_column_number(position)

    line   = line.replace("\t", " ")
    before = line[0:column]

    line   = make_visible(line)
    before = make_visible(before)

    limit = 65
    post  = 15
    if len(line) > limit:
        fringe = "..."
        if len(before)+1 > limit-post:
            while len(before)+len(fringe)+1 > limit-post:
                line   = line[1:]
                before = before[1:]
            line   = fringe + line
            before = fringe + before
        if len(line) > limit:
            line = line[:limit-len(fringe)] + "..."

    result  = line + "\n"
    #result += before + "^\n"
    result += " "*len(before) + "^\n"

    return result

def make_visible(text):
    result = ""
    for char in text:
        c = ord(char)
        if c<32:
            result += "^" + chr(ord('@')+c)
        else:
            result += char
    return result

## 
## Decorating tokens with properties:
## 

TOKEN_BARE_WORD    = 0x1
TOKEN_DOUBLE_WORD  = 0x2
TOKEN_SINGLE_WORD  = 0x4
TOKEN_LPAREN       = 0x8
TOKEN_RPAREN       = 0x10
TOKEN_LBRACKET     = 0x20
TOKEN_RBRACKET     = 0x40
TOKEN_BAR          = 0x80
TOKEN_COMMA        = 0x100
TOKEN_SEMICOLON    = 0x200
TOKEN_EQUALS       = 0x400
TOKEN_COLON_EQUALS = 0x800
TOKEN_CONTEXT      = 0x1000
TOKEN_ILLEGAL_WORD = 0x2000
TOKEN_EOF          = 0x4000

TOKEN_TERM         = 0x10000
TOKEN_ACTION       = 0x20000
TOKEN_WORD         = 0x40000


def initialize_token_properties():
    properties = {}

    properties["("]   = TOKEN_LPAREN       |TOKEN_TERM
    properties[")"]   = TOKEN_RPAREN

    properties["["]   = TOKEN_LBRACKET     |TOKEN_TERM
    properties["]"]   = TOKEN_RBRACKET

    properties["|"]   = TOKEN_BAR
    properties[","]   = TOKEN_COMMA
    properties[";"]   = TOKEN_SEMICOLON
    properties["="]   = TOKEN_EQUALS
    properties[":="]  = TOKEN_COLON_EQUALS

    properties[":"]   = TOKEN_CONTEXT
    properties["b"]   = TOKEN_BARE_WORD    |TOKEN_TERM |TOKEN_ACTION |TOKEN_WORD
    properties['"']   = TOKEN_DOUBLE_WORD  |TOKEN_TERM |TOKEN_ACTION |TOKEN_WORD
    properties["'"]   = TOKEN_SINGLE_WORD  |TOKEN_TERM |TOKEN_ACTION |TOKEN_WORD
    properties["\n"]  = TOKEN_ILLEGAL_WORD
    properties["EOF"] = TOKEN_EOF

    initialize_tokenizer(properties)

def decode_token_kinds(kind):
    result = []

    if kind & TOKEN_ACTION:       result.append("an action")
    if kind & TOKEN_TERM:         result.append("a term")
    if kind & TOKEN_WORD:         result.append("a word")

    if kind & TOKEN_LPAREN:       result.append("'('")
    if kind & TOKEN_RPAREN:       result.append("')'")

    if kind & TOKEN_LBRACKET:     result.append("'['")
    if kind & TOKEN_RBRACKET:     result.append("']'")

    if kind & TOKEN_BAR:          result.append("'|'")
    if kind & TOKEN_COMMA:        result.append("','")
    if kind & TOKEN_SEMICOLON:    result.append("';'")
    if kind & TOKEN_EQUALS:       result.append("'='")
    if kind & TOKEN_COLON_EQUALS: result.append("':='")

    if kind & TOKEN_CONTEXT:      result.append("a context statement")

    if kind & TOKEN_BARE_WORD:    result.append("an unquoted word")
    if kind & TOKEN_DOUBLE_WORD:  result.append("a double quoted word")
    if kind & TOKEN_SINGLE_WORD:  result.append("a single quoted word")

    if kind & TOKEN_ILLEGAL_WORD: result.append("an unterminated quotation")
    if kind & TOKEN_EOF:          result.append("end of file")

    if len(result) <= 2:
        return " or ".join(result)
    else:
        return (", ".join(result[:-1])) + ", or " + result[-1]


## 
## Handling syntax errors:
## 

def syntax_error(wanted, found, found_text, position):
    if found == TOKEN_ILLEGAL_WORD:
        log_error("Unterminated quotation: " + found_text[:-1], 
                  get_current_position())
        raise SyntaxError, "Unterminated quotation: " + found_text[:-1]

    advice = ""
    if (wanted&TOKEN_RPAREN):
        advice += "    Did you forget a ')' or have an extra'('?\n"
    if (wanted&TOKEN_ACTION):
        advice += "    Did you forget a ';' at the end of your (last) statement?\n"
        if (wanted&TOKEN_BAR):
            advice += "    Did you forget a '|' at the end of your (last) alternative?\n"

    if wanted & TOKEN_TERM:
        wanted &= ~(TOKEN_LPAREN|TOKEN_LBRACKET|TOKEN_BARE_WORD|
                    TOKEN_DOUBLE_WORD|TOKEN_SINGLE_WORD)
    if wanted & TOKEN_ACTION:
        wanted &= ~(TOKEN_BARE_WORD|TOKEN_DOUBLE_WORD|TOKEN_SINGLE_WORD)
    if wanted & TOKEN_WORD:
        wanted &= ~(TOKEN_BARE_WORD|TOKEN_DOUBLE_WORD|TOKEN_SINGLE_WORD)

    found &= ~(TOKEN_TERM | TOKEN_ACTION | TOKEN_WORD)

    message = "Wanted " + decode_token_kinds(wanted) + \
        " but found "+ decode_token_kinds(found)

    log_error(message, position, advice)
    raise SyntaxError, message


## 
## Saving and restoring the token state:
## 

Token_state_stack = []

  # requires: initialize_token_properties(-) has already been called
def open_text(text):
    global Token_state_stack, Text, Tokens, Offset, Peeks, Scan_limit, Scan_newlines
    token_state = [Text, Tokens, Offset, Peeks, Scan_limit, Scan_newlines]
    Token_state_stack.append(token_state)

    load_tokens(text)

def close_text():
    global Token_state_stack, Text, Tokens, Offset, Peeks, Scan_limit, Scan_newlines
    token_status = Token_state_stack.pop()
    Text, Tokens, Offset, Peeks, Scan_limit, Scan_newlines = token_status


# ---------------------------------------------------------------------------
# Parsing routines
#
#   The following grammar defines the Vocola 2 language:
# (note that a "menu" is called an "alternative set" in the documentation)
#
#     <statements> ::= <statement>*
#      <statement> ::= context_statement | <definition> | <function> 
#                    | <directive> | <top_command>
#
#     <definition> ::= variable    ':=' <menu_body> ';'
#       <function> ::= <prototype> ':=' <action>*   ';'
#    <top_command> ::= <terms>      '=' <action>*   ';'
#      <directive> ::= bare_word [<word> [<word>]]  ';'
#
#          <terms> ::= <term>+
#           <term> ::= <word> | variable | range | <menu> | '[' <terms> ']'
#           <word> ::= quoted_word | bare_word
#
#         <action> ::= <word> | <call>
#           <call> ::= callName '(' <arguments> ')'
#      <arguments> ::= [<action>* (',' <action>*)*]
#
#           <menu> ::= '(' <menuBody> ')'
#       <menuBody> ::= <command> ('|' <command>)*
#        <command> ::= <terms> ['=' <action>*]
#
#      <prototype> ::= functionName '(' <formals> ')'
#        <formals> ::= [name (',' name)*]
#
# The terminals variable, range, callName, name, and functionName are
# simply synonyms for bare_word as far as the parser is concerned.
# Note that unterminated quotations do not occur in the above; this is
# because they are not legal Vocola 2.
#
#
#   The logically separate (integrated in practice) type checking pass
# enforces additional constraints including:
#
#            variable == <\w+>
#               range == \d+\.\.\d+
#                name == [a-zA-Z_]\w*
#        functionName == [a-zA-Z_]\w*
#            callName == [a-zA-Z_][\w.]*
#
#   context_statements may not contain normal '='s (e.g., not in a
#     quotation or a comment).
#
# The actual currently allowable directives are:
#
#      <directive> ::= ('include' word | '$set' word word) ';'
#
# There additional limitations on the complexity of menus; <<<>>>

# ---------------------------------------------------------------------------
# Built in Vocola functions with (minimum number of arguments, maximum
# number of arguments):

Vocola_functions = {
                     "Eval"         : [1,1],
                     "EvalTemplate" : [1,-1],
                     "If"           : [2,3],
                     "Repeat"       : [2,2],
                     "Unimacro"     : [1,1],
                     "When"         : [2,3],
                   }

# Vocola extensions with (extension_name, minimum_arguments, maximum_arguments,
# needs_flushing, module_name, function_name); initialized by 
# read_extensions_file():

Extension_functions = {}

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

# parse_file returns a parse tree (list of statements), which includes in-line
# any statements from include files. Since parse_file is called recursively
# for include files, all code applying to the parse tree as a whole is
# executed in this routine.

def parse_file(in_file):    # returns a list of statements
    global In_folder, Include_stack_file, Included_files
    
    Included_files.append(in_file)
    in_path = in_file
    if not re.match(re.escape(os.sep), in_path):
        in_path = In_folder + os.sep + in_path

    text = read_file(in_path)
    open_text(text)
    try:
        Include_stack_file.append(in_file)
        statements = parse_statements()
    finally:
        close_text()
        Include_stack_file.pop()

    return statements

def read_file(in_file):     
    global Last_include_position
    try:
        return open(in_file).read()
    except (IOError, OSError), e:
        log_error("Unable to open or read '" + in_file + "'", # + ": " + str(e),
                  Last_include_position)
        return ""

# This is the main parsing loop.

def parse_statements():    # statements = (context | top_command | definition)*
    global Definitions, Formals, Include_stack_line, Last_include_position
    global Statement_count, Variable_terms

    statements = []
    while not peek(TOKEN_EOF):
        Variable_terms    = []  # used in error-checking
        Formals           = []  # None => any ref ok (environment variables)
        starting_position = get_current_position()
        try:
            statement = parse_statement()
        except (SyntaxError, RuntimeError), e:
            # panic until after next ";":
            while not peek(TOKEN_EOF) and not peek(TOKEN_SEMICOLON):
                eat()
            if peek(TOKEN_SEMICOLON):
                eat(TOKEN_SEMICOLON)
            continue

        if statement["TYPE"] == "definition": 
            name = statement["NAME"]
            if Definitions.has_key(name):
                log_error("Redefinition of <"+name+">", starting_position)
            Definitions[name] = statement
        elif statement["TYPE"] == "command": 
            statement["NAME"] = str(Statement_count)
            Statement_count += 1

        #print unparse_statements([statement]),
        if statement["TYPE"] != "include": 
            statements.append(statement)
        else: 
            # Handle include file
            include_file = expand_variables(statement["ACTIONS"])
            if not already_included(include_file):
                # Save context, get statements from include file, restore 
                Last_include_position = starting_position
                Include_stack_line.append(get_line_number(starting_position))
                #print "--> " + include_file
                statements.extend(parse_file(include_file))
                #print "<--"
                Include_stack_line.pop()

    return statements

def parse_statement():
    if peek(TOKEN_CONTEXT):
        return parse_context()
    if peek(TOKEN_LBRACKET|TOKEN_LPAREN|TOKEN_SINGLE_WORD|TOKEN_DOUBLE_WORD):
        return parse_top_command()


    start = get_current_position()
    peek(TOKEN_TERM)
    eat(TOKEN_BARE_WORD)

    # b ^ :=
    if peek(TOKEN_COLON_EQUALS):
        rewind(start); return parse_variable_definition()

    # b ^ w{0,2} ;  or  b ^ w{2} <term>  or b ^ w{0,2} =
    directive_arguments = 0
    while peek(TOKEN_WORD):
        eat()
        directive_arguments += 1
        if directive_arguments > 2:
            rewind(start); return parse_top_command()
    if peek(TOKEN_SEMICOLON):
        rewind(start); return parse_directive()
    if directive_arguments > 0:
        if not peek(TOKEN_LBRACKET|TOKEN_LPAREN):
            peek(TOKEN_TERM)
            eat(TOKEN_EQUALS)
        rewind(start); return parse_top_command()

    # b ^ <term> in unambiguous case  or  b ^ =
    if peek(TOKEN_LBRACKET|TOKEN_SINGLE_WORD|TOKEN_DOUBLE_WORD|TOKEN_EQUALS):
        rewind(start); return parse_top_command()


    peek(TOKEN_TERM)
    eat(TOKEN_LPAREN)
    # b( ^ <term>  or  b( ^ )  or  b( ^ b)  or  b( ^ b,  or  b( ^ b) :=
    if peek(TOKEN_RPAREN):
        rewind(start); return parse_function_definition()
    if peek(TOKEN_LBRACKET|TOKEN_SINGLE_WORD|TOKEN_DOUBLE_WORD|TOKEN_LPAREN):
        rewind(start); return parse_top_command()


    peek(TOKEN_TERM)
    eat(TOKEN_BARE_WORD)
    # b(b ^ <term>  or  b(b ^ |  or b(b ^ =  or  b(b ^ )  or  b(b ^ ,
    if peek(TOKEN_TERM|TOKEN_BAR|TOKEN_EQUALS):
        rewind(start); return parse_top_command()
    if peek(TOKEN_COMMA):
        rewind(start); return parse_function_definition()
    
    eat(TOKEN_RPAREN)
    # b(b) ^ <term>  or  b(b) ^ =  or b(b) ^ :=
    if peek(TOKEN_TERM|TOKEN_EQUALS):
        rewind(start); return parse_top_command()


    eat(TOKEN_COLON_EQUALS)
    rewind(start); return parse_function_definition()

def parse_context():    # context = chars* ('|' chars*)* ':'
    global Debug, LOG

    raw = eat(TOKEN_CONTEXT)[:-1]
    match = re.match(r'(?:[^=#]|#.*\n)*=', raw)
    if match:
        equal_position = adjust_position(get_last_position(),
                                         match.end(0) - 1)
        error("Context statements may not contain '='s", equal_position,
              "    Did you forget a ';' at the end of this statement?\n" +
              "    Did you forget to quote a word ending with ':'?\n")

    processed = ""
    for piece in re.findall(r'[^#]+|#.*\n', raw):
        if piece[:1] != "#": processed += piece.lower()
    strings = re.split(r'\s*\|\s*', processed.strip())
    if len(strings)== 0:
        strings = [""]

    statement            = {}
    statement["TYPE"]    = "context"
    statement["STRINGS"] = strings
    if Debug>=1: print >>LOG, unparse_directive (statement),
    return statement

def parse_variable_definition():    # definition = variable ':=' menu_body ';'
    global Debug, LOG
    position = get_current_position()
    name = eat(TOKEN_BARE_WORD)
    if not re.match(r'<.*>$', name):
        error("Illegal variable '" + name + 
              "': variables must start with '<' and end with '>'", position)
    name = name[1:-1]
    check_variable_name(name, position)
    if name == "_anything":
        error("Built-in list <_anything> is not redefinable", position)

    statement = {}
    statement["TYPE"] = "definition"
    statement["NAME"] = name
    eat(TOKEN_COLON_EQUALS)
    menu = parse_menu_body(TOKEN_SEMICOLON)
    eat(TOKEN_SEMICOLON)
    verify_referenced_menu(menu)
    statement["MENU"] = menu
    if Debug>=1: print >>LOG, unparse_definition (statement),
    return statement

def check_variable_name(name, position):
    if not re.match(r'\w+$', name):
        error("Illegal variable name: <" + name + ">", position)

def parse_function_definition():   # function = prototype ':=' action* ';'
                                   # prototype = functionName '(' formals ')'
    global Debug, Formals, Function_definitions, Functions, LOG
    position = get_current_position()
    functionName = eat(TOKEN_BARE_WORD)
    if Debug>=2: print >>LOG, "Found user function:  " + functionName + "()"
    if not re.match(r'[a-zA-Z_]\w*$', functionName):
        error("Illegal user function name: " + functionName, position)

    eat(TOKEN_LPAREN)
    formals = parse_formals()
    eat(TOKEN_RPAREN)
    
    statement            = {}
    statement["TYPE"]    = "function"
    statement["NAME"]    = functionName
    statement["FORMALS"] = formals
    Formals              = formals # Used below in parse_formal_reference

    eat(TOKEN_COLON_EQUALS)
    statement["ACTIONS"] = parse_actions(TOKEN_SEMICOLON)
    eat(TOKEN_SEMICOLON)

    if Functions.has_key(functionName):
        error("Redefinition of " + functionName + "()", position)
    if Vocola_functions.has_key(functionName):
        error("Attempted redefinition of built-in function: " + functionName, position)
    Functions[functionName] = len(formals)  # remember number of formals
    Function_definitions[functionName] = statement
    if Debug>=1: print >>LOG, unparse_function_definition (statement),
    return statement

def parse_formals():    # formals = [name (',' name)*]
    global Debug, LOG
    safe_formals = []
    if not peek(TOKEN_RPAREN):
        while True:
            formal = eat(TOKEN_BARE_WORD)
            if not re.match(r'[a-zA-Z_]\w*$', formal):
                error("Illegal formal name: '" + formal + "'", get_last_position())
            if Debug>=2: print >>LOG, "Found formal:  " + formal
            safe_formals.append("_" + formal)
            if peek(TOKEN_COMMA): 
                eat(TOKEN_COMMA)
            else:
                break
    return safe_formals

def parse_top_command():    # top_command = terms '=' action* ';'
    global Debug, File_empty, LOG
    statement = parse_command(TOKEN_SEMICOLON, True)
    eat(TOKEN_SEMICOLON)
    File_empty = False
    if Debug>=1: print >>LOG, unparse_command (statement, True)
    return statement

def parse_directive():    # directive = ('include' word | '$set' word word) ';'
    global Debug, LOG, Formals, Variable_terms

    starting_position = get_current_position()
    directive         = eat(TOKEN_BARE_WORD)

    word_nodes = []
    while len(word_nodes) < 2 and not peek(TOKEN_SEMICOLON):
        peek(TOKEN_WORD)
        word_nodes.append(parse_word())
    before_semicolon = get_last_position();
    eat(TOKEN_SEMICOLON)

    statement = {}
    if directive == "include":
        if len(word_nodes) != 1:
            position = before_semicolon
            if len(word_nodes) == 0:
                position = get_last_position()
            error("Include directive requires one word: include filename;", 
                  position)
        statement["TYPE"]    = "include"
        statement["TEXT"]    = word_nodes[0]["TEXT"]
        Variable_terms = []    # no # references are valid
        Formals        = None  # turn off formal reference checking
        statement["ACTIONS"] = split_out_references(word_nodes[0])
    elif directive == "$set":
        if len(word_nodes) != 2:
            error("$set directive requires 2 words: $set parameter value;",
                  get_last_position())
        statement["TYPE"] = "set"
        statement["KEY"]  = word_nodes[0]["TEXT"]
        statement["TEXT"] = word_nodes[1]["TEXT"]
    else:
        error("Unknown directive '" + directive + "'", starting_position)

    if Debug>=1: print >>LOG, unparse_directive (statement),
    return statement

def parse_command(separators, needs_actions=False): # command = terms ['=' action*]
    global Include_stack_file, Variable_terms
    if needs_actions:
        terms = parse_terms(TOKEN_EQUALS)
    else:
        terms = parse_terms(separators | TOKEN_EQUALS)
    
    command          = {}
    command["TYPE"]  = "command"
    command["FILE"]  = Include_stack_file[-1]
    command["TERMS"] = terms
    
    # Count variable terms for range checking in parse_reference
    Variable_terms = get_variable_terms(terms)
    
    if needs_actions or peek(TOKEN_EQUALS):
        eat(TOKEN_EQUALS)
        command["ACTIONS"] = parse_actions(separators)

    command["LINE"] = get_line_number(get_current_position()) # line number is *last* line of command # <<<>>>
    return command

def parse_terms(separators):    # <terms> ::= (<term> | '[' <terms> ']')+
    starting_position = get_current_position()
    terms = []
    seen_non_optional = False
    while True:
        if peek(TOKEN_LBRACKET):
            optional = True
            optional_starting_position = get_current_position()
            eat(TOKEN_LBRACKET)
            optional_terms = parse_terms(TOKEN_RBRACKET)
            eat(TOKEN_RBRACKET)
            term             = {}
            term["TYPE"]     = "optionalterms"
            term["TERMS"]    = optional_terms
            term["POSITION"] = optional_starting_position
            if Debug>=2: 
                print >>LOG, "Found optional term group:  " + unparse_term(term, True)
        else:
            optional = False
            term = parse_term()

        term["OPTIONAL"] = optional
        if (not optional and term["TYPE"] != "dictation"): seen_non_optional = True
        terms.append(term)

        if peek(separators): 
            break

    if not seen_non_optional: 
        error("At least one term must not be optional or <_anything>", 
              starting_position)
    else: 
        return combine_terms(terms)

def parse_term():         # <term> ::= <word> | variable | range | <menu>
    global Debug, Definitions, LOG

    starting_position = get_current_position()
    peek(TOKEN_TERM)
    if peek(TOKEN_LPAREN):         
        eat(TOKEN_LPAREN)
        term = parse_menu_body(TOKEN_RPAREN)
        term["POSITION"] = starting_position
        eat(TOKEN_RPAREN)
        if Debug>=2: 
            print >>LOG, "Found menu:  " + unparse_menu(term, True)
        return term
    elif not peek(TOKEN_BARE_WORD):
        return parse_word()

    word  = eat(TOKEN_BARE_WORD)
    match = re.match(r'<(.*?)>$|(\d+)\.\.(\d+)$', word)
    if not match:
        term = parse_word1(word, starting_position)
    elif match.group(2):
        term = {}
        term["TYPE"] = "range"
        term["FROM"] = int(match.group(2))
        term["TO"]   = int(match.group(3))
        if Debug>=2: 
            print >>LOG, "Found range:  " + match.group(2) + ".." + match.group(3)
    else:
        name = match.group(1)
        check_variable_name(name, starting_position)
        if name == "_anything": 
            if Debug>=2: print >>LOG, "Found <_anything>"
            term = create_dictation_node()
        else: 
            if Debug>=2: print >>LOG, "Found variable:  <" + name + ">"
            if not Definitions.has_key(name): 
                add_forward_reference(name, starting_position)
            term = create_variable_node(name)
    
    term["POSITION"] = starting_position
    return term

def create_dictation_node():
    global Should_emit_dictation_support
    Should_emit_dictation_support = True
    term = {}
    term["TYPE"] = "dictation"
    return term

def parse_menu_body(separators):    # menuBody = command ('|' command)*
    commands = []
    while True: 
        if peek(separators | TOKEN_BAR):
            error("Empty alternative (set)", get_current_position())
        commands.append(parse_command(separators | TOKEN_BAR))
        if peek(TOKEN_BAR):
            eat(TOKEN_BAR)
        else:
            break

    menu = {}
    menu["TYPE"]     = "menu"
    menu["COMMANDS"] = commands
    return menu

def parse_actions(separators):    # action = word | call
    actions = []
    while not peek(separators):
        kind = peek(TOKEN_ACTION|TOKEN_DOUBLE_WORD|TOKEN_SINGLE_WORD)
        if peek(TOKEN_BARE_WORD):
            word = eat(TOKEN_BARE_WORD)
            if peek(TOKEN_LPAREN):
                actions.append(parse_call(word))
                continue
            else:
                word_node = parse_word1(word, get_last_position())
        else:
            word_node = parse_word()
        actions += split_out_references(word_node)
    return actions

# expand in-string references (e.g. "{Up $1}") and unquote 
# $'s (e.g., \$ -> $).
# returns a non-empty list of actions
def split_out_references(word_node):
    word              = word_node["TEXT"]
    starting_position = word_node["POSITION"]
    quote_char        = word_node["QUOTE_CHAR"]

    if word == "": 
        return [word_node]

    raw     = quote_char  # raw word text seen so far
    actions = []

    # reference = '$' (number | name)
    for match in re.finditer(r'(.*?)(\Z|(?<!\\)\$(?:(\d+)|([a-zA-Z_]\w*)))',
                             word):
        normal = match.group(1)
        if normal != "":
            unescaped = normal.replace(r'\$','$')  # convert \$ to $
            position  = adjust_position(starting_position, len(raw))
            actions.append(create_word_node(unescaped, quote_char, position))
            raw += normal.replace(quote_char, quote_char+quote_char)
        if match.group(2) !=  None:
            position  = adjust_position(starting_position, len(raw))
            if match.group(3) != None:
                actions.append(create_reference_node(match.group(3),
                                                     position))
            elif match.group(4)!= None:
                actions.append(create_formal_reference_node(match.group(4),
                                                     position))
            raw += match.group(2)

    return actions

def create_reference_node(n, position):
    global Debug, Variable_terms, LOG
    if int(n) > len(Variable_terms): 
        error("Reference '$" + n + "' out of range", position)
    term = Variable_terms[int(n) - 1]
    if term["TYPE"] == "menu": verify_referenced_menu(term)
    if Debug>=2: print >>LOG, "Found reference:  $" + n
    action = {}
    action["TYPE"] = "reference"
    action["TEXT"] = n
    return action

def create_formal_reference_node(name, position):
    global Debug, Formals, LOG
    formal = "_" + name
    if Formals!=None and formal not in Formals:
        error("Reference to unknown formal '$" + name + "'", position)
    if Debug>=2: print >>LOG, "Found formal reference:  $" + name
    action = {}
    action["TYPE"]     = "formalref"
    action["TEXT"]     = formal
    action["POSITION"] = position
    return action

def parse_call(callName):    # call = callName '(' arguments ')'
    global Debug, Dragon_functions, Extension_functions, Functions, Vocola_functions, LOG

    call_position = get_last_position()
    if Debug>=2: print >>LOG, "Found call:  " + callName + "()"
    if not re.match(r'[\w.]+$', callName):
        error("Illegal function call name: '" + callName + "'", call_position)

    action = {}
    action["TYPE"] = "call"
    action["TEXT"] = callName
    eat(TOKEN_LPAREN)
    action["ARGUMENTS"] = parse_arguments()
    eat(TOKEN_RPAREN)
    
    nActuals = len(action["ARGUMENTS"])
    if callName.find(".") != -1:
        if Extension_functions.has_key(callName): 
            callFormals = Extension_functions[callName]
            lFormals = callFormals[0]
            uFormals = callFormals[1]
            action["CALLTYPE"] = "extension"
        else: 
            error("Call to unknown extension '" + callName + "'", call_position)
    elif Dragon_functions.has_key(callName):
        callFormals = Dragon_functions[callName]
        lFormals =     callFormals[0]
        uFormals = len(callFormals[1])
        action["CALLTYPE"] = "dragon"
        action["ARGTYPES"] = callFormals[1]
    elif Vocola_functions.has_key(callName):
        callFormals = Vocola_functions[callName]
        lFormals = callFormals[0]
        uFormals = callFormals[1]
        action["CALLTYPE"] = "vocola"
    elif Functions.has_key(callName): 
        lFormals = uFormals = Functions[callName]
        action["CALLTYPE"] = "user"
    else: 
        error("Call to unknown function '" + callName + "'", call_position)

    if lFormals != -1 and nActuals < lFormals: 
        error("Too few arguments passed to '" + callName + 
              "' (minimum of " + str(lFormals) + " required)", call_position)
    if uFormals != -1 and nActuals > uFormals: 
        error("Too many arguments passed to '" + callName + 
              "' (maximum of " + str(uFormals) + " allowed)", call_position)

    return action

def parse_arguments():    # arguments = [action* (',' action*)*]
    arguments = []
    if not peek(TOKEN_RPAREN):
        while True:
            arguments.append(parse_actions(TOKEN_COMMA|TOKEN_RPAREN))
            if peek(TOKEN_COMMA): 
                eat(TOKEN_COMMA)
            else:
                break

    return arguments

def parse_word():    
    global Debug, LOG
    if peek(TOKEN_DOUBLE_WORD):
        quote_char ='"'
        word = eat(TOKEN_DOUBLE_WORD)[1:-1].replace('""', '"')
    elif peek(TOKEN_SINGLE_WORD):
        quote_char = "'"
        word = eat(TOKEN_SINGLE_WORD)[1:-1].replace("''", "'")
    else:
        quote_char = ""
        word = eat(TOKEN_BARE_WORD)
    if Debug>=2: print >>LOG, "Found word:  '" + word + "'"
    node = create_word_node(word, quote_char, get_last_position())
    return node

def parse_word1(bare_word, position):    
    global Debug, LOG
    if Debug>=2: print >>LOG, "Found word:  '" + bare_word + "'"
    node = create_word_node(bare_word, "", position)
    node["POSITION"] = position
    return node


def implementation_error(error):
    log_error(error)
    raise RuntimeError, error    # <<<>>>

def error(message, position, advice=""):
    log_error(message, position, advice)
    raise RuntimeError, message    # <<<>>>

def log_error(message, position=None, advice=""):
    global Error_count, Input_name, LOG
    if Error_count==0: print >>LOG, "Converting " + Input_name
    print >>LOG, format_error_message(message, position, advice),
    Error_count += 1

def format_error_message(message, position=None, advice=""):
    global Include_stack_file, Include_stack_line

    if message[-1] == "\n":
        message = message[:-1]

    at_line = ""
    if position != None:
        at_line = " at line " + str(get_line_number(position))
    of_file = ""
    if len(Include_stack_file) > 1:
        of_file = " of " + Include_stack_file[-1]
    message = "  Error" + at_line + of_file + ":  " + message + "\n"

    indent = ""
    i = len(Include_stack_file)-2
    while i >= 0:
        file = Include_stack_file[i]
        line_number = Include_stack_line[i]
        indent  += "  "
        message += indent + "  (Included at line " + str(line_number) + " of " \
            + file + ")\n"
        i -= 1

    if position != None:
        message += point_to_position(position)

    if advice != "":
        message += advice + "\n"

    return message   

def already_included(filename):
    global Included_files
    # Return TRUE if filename was already included in the current file
    return filename in Included_files

def expand_variables(actions):
    result = ""
    for action in actions:
        type = action["TYPE"]
        if type == "word":
            result += action["TEXT"]
        elif type == "formalref":
            variable = action["TEXT"][1:]
            value = os.environ.get(variable)
            if not value:
                # Should be a warning not an error.
                log_error("Reference to unknown environment variable '" 
                          + variable + "'", action["POSITION"])
            else:
                result += value
        else:
            implementation_error("unsupported action type in include actions")
    return result

# ---------------------------------------------------------------------------
# Parse-time error checking of references

def verify_referenced_menu(menu, parent_has_actions=False, parent_has_alternatives=False):
    commands         = menu["COMMANDS"]
    has_alternatives = parent_has_alternatives or (len(commands) != 1)

    for command in commands: 
        has_actions = parent_has_actions
        if command.has_key("ACTIONS"): 
            has_actions = True
            if parent_has_actions: 
                error("Nested in-line lists with associated actions may not themselves contain actions",
                      menu["POSITION"])

        terms = command["TERMS"]
        verify_menu_terms(terms, has_actions, has_alternatives, False)

def verify_menu_terms(terms, has_actions, has_alternatives, other_terms):
    if len(terms) != 1: other_terms = True
    for term in terms:
        type = term["TYPE"]
        if   type == "word" and term["OPTIONAL"]:
            #error("Alternative cannot contain an optional word",
            #      term["POSITION"])
            implementation_error("Alternative cannot contain an optional word")
        elif type == "optionalterms": 
            verify_menu_terms(term["TERMS"], has_actions, has_alternatives, 
                              other_terms)
        elif type == "variable" or type == "dictation": 
            error("Alternative cannot contain a variable", term["POSITION"])
        elif type == "menu": 
            if other_terms:
                error("An inline list cannot be combined with anything else to make up an alternative",
                      term["POSITION"])
            verify_referenced_menu(term, has_actions, has_alternatives)
        elif type == "range": 
            # allow a single range with no actions if it is the only
            # alternative in the (nested) set:
            if other_terms:
                error("A range cannot be combined with anything else to make up an alternative",
                      term["POSITION"])
            if has_actions:
                error("A range alternative may not have associated actions",
                      term["POSITION"])
            if has_alternatives:
                error("A range alternative must be the only alternative in an alternative set",
                      term["POSITION"])

def add_forward_reference(variable, position):
    global Forward_references, Include_stack_file, Include_stack_line
    forward_reference = {}
    forward_reference["VARIABLE"]   = variable
    forward_reference["POSITION"]   = position
    forward_reference["STACK_FILE"] = Include_stack_file[:]
    forward_reference["STACK_LINE"] = Include_stack_line[:]
    Forward_references.append(forward_reference)

def check_forward_references():
    global Definitions, Error_count, Forward_references, Input_name, LOG
    global Include_stack_file, Include_stack_line
    for forward_reference in Forward_references: 
        variable = forward_reference["VARIABLE"]
        if not Definitions.has_key(variable):
            stack_file = Include_stack_file
            stack_line = Include_stack_line

            position           = forward_reference["POSITION"]
            Include_stack_file = forward_reference["STACK_FILE"]
            Include_stack_line = forward_reference["STACK_LINE"]
            log_error("Reference to undefined variable '<" + variable + ">'",
                      position)

            Include_stack_file = stack_file
            Include_stack_line = stack_line

# ---------------------------------------------------------------------------
# Okay, let's run!

main();
#import profile
#profile.run('main()')
