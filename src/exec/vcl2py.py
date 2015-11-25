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
from vcl2py.lex import initialize_token_properties
from vcl2py.log import *
from vcl2py.parse import parse_input, check_forward_references



# ---------------------------------------------------------------------------
# Main control flow

VocolaVersion = "2.8.4"

def main():
    global Debug, Default_maximum_commands, Error_encountered, Force_processing, In_folder, Default_number_words
    global Extension_functions

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
        set_log(sys.stdout)
    else:
        try:
            set_log(open(log_file, "w"))
        except IOError, e:
            fatal_error("Unable to open log file '" + log_file + "' for writing: " + str(e))


    if not ignore_INI_file:   read_ini_file(ini_file)
    Extension_functions = {}
    if extensions_file != "": read_extensions_file(extensions_file)
    if Debug >= 1: 
        print_log("default maximum commands per utterance = " + str(Default_maximum_commands))

    initialize_token_properties()
    convert_files(in_file, out_folder, suffix)
    
    close_log()
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
    global Debug, Default_maximum_commands

    if Debug >= 1: print_log("INI file is '" + ini_file + "'")
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
    global Debug, Extension_functions
    if Debug >= 1: print_log("extensions file is '" + extensions_filename + "'")
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
    global In_folder

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
    global Debug, Error_encountered, File_empty
    global Force_processing
    global In_folder
    global Input_name, Module_name
    global Default_number_words, Number_words
    global Default_maximum_commands, Maximum_commands

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

    
    if Debug>=1: print_log("\n==============================")

    statements, Definitions, Function_definitions, statement_count, error_count, should_emit_dictation_support, file_empty = parse_input(Input_name, In_folder, 
                                                   Extension_functions, Debug)
    if error_count == 0: 
        check_forward_references()
    
    # Prepend a "global" context statement if necessary
    if len(statements) == 0 or statements[0]["TYPE"] != "context": 
        context            = {}
        context["TYPE"]    = "context"
        context["STRINGS"] = [""]
        statements.insert(0, context)
    #print_log(unparse_statements(statements), True)
    statements = transform(statements, Function_definitions, statement_count)
    #print_log(unparse_statements(statements), True)
    
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

    if error_count > 0: 
        if error_count == 1:
            s = ""
        else:
            s = "s"
        print_log("  " + str(error_count) + " error" + s + " -- file not converted.")
        Error_encountered = True
        return
    if file_empty: 
        # Write empty output file, for modification time comparisons 
        try:
            OUT = open(out_file, "w")
            OUT.close()
        except IOError, e:
            print_log("Couldn't open output file '" + out_file + "' for writing")
        print_log("Converting " + Input_name)
        print_log("  Warning: no commands in file.")
        return

    from vcl2py.emit import output
    #emit_output(out_file, statements)
    output(out_file, statements,
           VocolaVersion,
           should_emit_dictation_support,
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
# Okay, let's run!

main();
#import profile
#profile.run('main()')
