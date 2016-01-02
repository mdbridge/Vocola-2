#
# Main control flow module
#

import os
import re
import sys

from vcl2py.emit      import output
from vcl2py.lex       import initialize_token_properties
from vcl2py.log       import *
from vcl2py.parse     import parse_input, check_forward_references
from vcl2py.transform import transform


VocolaVersion = "2.8.5ALPHA"


# ---------------------------------------------------------------------------
# Messages to standard error

def fatal_error(message):
    print >>sys.stderr, "vcl2py.py: Error: " + message
    sys.exit(99)


def usage(message=""):
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



# ---------------------------------------------------------------------------
# Parsing parameters

def default_parameters():
    params = {}

    # debug states: 0 = no info, 1 = show statements, 2 = detailed info
    params["debug"]            = 0

    params["extensions_file"]  = None
    params["ignore_INI_file"]  = False
    params["INI_file"]         = None
    params["log_file"]         = None
    params["log_to_stdout"]    = False

    params["force_processing"] = False
    params["suffix"]           = "_vcl"

    params["maximum_commands"] = 1
    params["number_words"]     = {}

    return params


def parse_command_arguments(argv, default_params):
    p = default_params
    while len(argv) > 0:
        option = argv[0]
        if not option[0:1] == "-": 
            break

        argv.pop(0)
        if   option == "-f":          p["force_processing"] = True; continue
        elif option == "-log_stdout": p["log_to_stdout"]    = True; continue
        elif option == "-q":          p["ignore_INI_file"]  = True; continue

        if len(argv) == 0:
            usage("missing argument for option " + option)

        argument = argv.pop(0)
        if   option == "-debug":      p["debug"]           = safe_int(argument, 1)
        elif option == "-extensions": p["extensions_file"] = argument
        elif option == "-INI_file":   p["INI_file"]        = argument
        elif option == "-log_file":   p["log_file"]        = argument
        elif option == "-max_commands":
            p["maximum_commands"] = safe_int(argument, 1)
        elif option == "-numbers":
            p["number_words"] = parse_number_words(argument)
        elif option == "-suffix":     p["suffix"]          = argument
        else:
            usage("unknown option: " + option)

    if len(argv) == 2:
        inputFileOrFolder = argv[0]
        out_folder        = argv[1]
    else:
        usage()

    return p, inputFileOrFolder, out_folder


def read_INI_file(ini_file, default_params):
    params = default_params
    try:
        input = open(ini_file)
        for line in input:
            match = re.match(r'^(.*?)=(.*)$', line)
            if not match: continue
            keyword = match.group(1)
            value   = match.group(2)
            if keyword == "MaximumCommands":
                params["maximum_commands"] = safe_int(value, 1)
    except IOError, e:
        pass
    return params


def safe_int(text, default=0):
    try:
        return int(text)
    except ValueError:
        return default

def parse_number_words(text):
    number_words = {}
    numbers = re.split(r'\s*,\s*', text.strip())
    i = 0
    for number in numbers:
        if number != "":
            number_words[i] = number
        i = i + 1
    return number_words


def get_parameters():
    params, inputFileOrFolder, out_folder \
        = parse_command_arguments(sys.argv[1:], default_parameters())

    if os.path.isdir(inputFileOrFolder):
        # inputFileOrFolder is an entire folder
        in_folder = inputFileOrFolder
        in_file   = None
    elif os.path.exists(inputFileOrFolder):
        # inputFileOrFolder is a single file
        in_folder, filename = os.path.split(inputFileOrFolder)
        if in_folder == "": in_folder = "."
        in_file, extension  = os.path.splitext(filename)
        if not extension == ".vcl":
            fatal_error("Input file '" + inputFileOrFolder +
                        "' must end in '.vcl'")
    else:
        fatal_error("Nonexistent input filename '" + inputFileOrFolder + "'")

    if not params["log_file"]:
        params["log_file"] = in_folder + os.sep + "vcl2py_log.txt"
    if not params["INI_file"]:
        params["INI_file"] = in_folder + os.sep + "Vocola.INI"

    if not params["ignore_INI_file"]:
        params = read_INI_file(params["INI_file"], params)

    return params, in_folder, in_file, out_folder



# ---------------------------------------------------------------------------
# Main control flow

def main_routine():
    global Debug

    # flush output after every print statement:
    #sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)    # <<<>>>

    params, in_folder, in_file, out_folder = get_parameters()
    Debug    = params["debug"]
    log_file = params["log_file"]

    if params["log_to_stdout"]:
        set_log(sys.stdout)
    else:
        try:
            set_log(open(log_file, "w"))
        except IOError, e:
            fatal_error("Unable to open log file '" + log_file +
                        "' for writing: " + str(e))

    if Debug >= 1: print_log("INI file is '" + params["INI_file"] + "'")

    extension_functions = {}
    extensions_filename = params["extensions_file"]
    if extensions_filename:
        if Debug >= 1: print_log("extensions file is '" + extensions_filename + "'")
        extension_functions = read_extensions_file(extensions_filename)

    if Debug >= 1:
        print_log("default maximum commands per utterance = " +
                  str(params["maximum_commands"]))

    initialize_token_properties()
    error_count = 0
    files = expand_in_file(in_file, in_folder)
    for in_file in files:
        error_count += convert_file(in_folder, in_file, out_folder, extension_functions, params)

    close_log()
    if error_count == 0:
        if not params["log_to_stdout"]: os.remove(log_file)
        sys.exit(0)
    else:
        sys.exit(1)


def read_extensions_file(extensions_filename):
    extension_functions = {}
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

            extension_functions[extension_name] = [minimum_arguments, maximum_arguments, needs_flushing, module_name, function_name]
    except IOError, e:
        pass
    return extension_functions


def expand_in_file(in_file, in_folder):
    if in_file:
        # just one file
        return [in_file]

    # each .vcl file in folder:
    result = []
    machine = os.environ.get("COMPUTERNAME", "").lower()
    try:
        for filename in os.listdir(in_folder):
            match = re.match(r'^(.+)\.vcl$', filename)
            if match:
                in_file = match.group(1)
                # skip machine-specific files for different machines
                match = re.search(r'@(.+)', in_file)
                if not (match and match.group(1).lower() != machine):
                    result += [in_file]
        return result
    except IOError, e:
        fatal_error("Couldn't open/list folder '" + in_folder + "': " + str(e))



# ---------------------------------------------------------------------------
# Converting one Vocola command file to a .py file

  # in_file is just the base name; actual pathname is
  # <in_folder>/<in_file>.vcl where / is the correct separator
def convert_file(in_folder, in_file, out_folder, extension_functions, params):
    out_file = convert_filename(in_file)

    # module_name is used below to implement application-specific
    # commands in the output Python
    module_name = out_file.lower()
    input_name  = in_file + ".vcl"

    out_file = out_folder + os.sep + out_file + params["suffix"] + ".py"

    in_path = in_folder + os.sep + input_name
    if os.path.exists(in_path):
        in_time  = os.path.getmtime(in_path)
        out_time = 0
        if os.path.exists(out_file): out_time = os.path.getmtime(out_file)
        if in_time<out_time and not params["force_processing"]:
            return 0


    if Debug>=1: print_log("\n==============================")

    statements, definitions, function_definitions, statement_count, \
        error_count, should_emit_dictation_support, file_empty \
        = parse_input(input_name, in_folder, extension_functions, Debug)
    if error_count == 0:
        check_forward_references()

    # Prepend a "global" context statement if necessary
    if len(statements) == 0 or statements[0]["TYPE"] != "context":
        context            = {}
        context["TYPE"]    = "context"
        context["STRINGS"] = [""]
        statements.insert(0, context)
    #print_log(unparse_statements(statements), True)
    statements = transform(statements, function_definitions, statement_count)
    #print_log(unparse_statements(statements), True)

    # Handle $set directives:
    params_per_file = params.copy()
    for statement in statements:
        if statement["TYPE"] == "set":
            key = statement["KEY"]
            if key == "MaximumCommands":
                params_per_file["maximum_commands"] \
                    = safe_int(statement["TEXT"], 1)
            elif key == "numbers":
                params_per_file["number_words"] \
                    = parse_number_words(statement["TEXT"].strip())

    if error_count > 0:
        if error_count == 1:
            s = ""
        else:
            s = "s"
        print_log("  " + str(error_count) + " error" + s + " -- file not converted.")
        return error_count
    if file_empty:
        # Write empty output file, for modification time comparisons
        try:
            OUT = open(out_file, "w")
            OUT.close()
        except IOError, e:
            print_log("Couldn't open output file '" + out_file + "' for writing")
            error_count += 1
        print_log("Converting " + input_name)
        print_log("  Warning: no commands in file.")
        return error_count

    from vcl2py.emit import output
    #emit_output(out_file, statements)
    output(out_file, statements,
           VocolaVersion,
           should_emit_dictation_support,
           module_name, definitions,
           extension_functions, params_per_file)

    return 0


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

    suffix = suffix.replace('_', '___')
    suffix = suffix.replace('@', '__a_t__')
    return module + marker + suffix
