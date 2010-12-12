### 
### scan_extensions.py - Code used to build extensions.csv file from
###                      present ext_*.py files.
###
### This file is copyright (c) 2010 by Rick Mohr.  It may be redistributed 
### in any way as long as this copyright notice remains.
### 

import os
import sys
import re


def process_extension(extension):
    global functions, procedures

    log_verbose("  scanning %s.py..." % extension)

    functions = procedures = 0

    last_line   = ""
    line_number = 0
    with open(extension + ".py", "r") as f:
        for line in f:
            scan(last_line, line, extension, line_number)
            line_number += 1
            last_line = line

    log_verbose("    found %d function(s), %d procedures(s)" % \
                    (functions, procedures))


def scan(first_line, second_line, extension, line_number):
    global functions, procedures, output

    m = re.search(r'^\s*\#\s*Vocola\s+(function|procedure):\s*(.*)', first_line,
                  re.I)
    if m == None:
        return
    kind      = m.group(1)
    arguments = split_arguments(m.group(2))

    if len(arguments)<1:
        log("%s.py:%d: Error: Vocola extension %s name not specified" % \
            (extension, line_number, kind))
        return
    name = arguments[0]
    if name.find(".") == -1:
        log(("%s.py:%d: Error: Vocola extension %s name does not " + \
                   "contain a '.'") % (extension, line_number, kind))
        return


    m = re.search(r'^\s*def\s+([^(]+)\(([^)]*)', second_line)
    if m == None:
        log(("%s.py:%d: Error: Vocola extension specification line " + \
                   "not followed by a def name(... line") % \
                   (extension, line_number))
        return
    function_name      = m.group(1)
    function_arguments = split_arguments(m.group(2))

    m = None
    if len(arguments) > 1:
        m = re.search(r'^(\d+)\s*(-\s*(\d+)?)?', arguments[1])
    if m:
        min = max = int(m.group(1))
        if m.group(2):
            max = -1               
        if m.group(3):
            max = int(m.group(3))
    else:
        min = max = len(function_arguments)


    if kind.lower() == "function":
        is_procedure = 0
        functions  += 1   
    else:
        is_procedure = 1
        procedures += 1   

    definition = "%s,%d,%d,%s,%s,%s.%s\n" % (name, min, max, is_procedure, 
                                             extension, extension, function_name)
    output.write(definition)


def split_arguments(arguments):
    arguments = arguments.strip()
    # special case because of Python bug in split() resulting in [""] for "":
    if arguments == "":
        return []
    else: 
        return [x.strip() for x in arguments.split(",")]


def log(message):
    global log_file
    if log_file:
        log_file.write(message + "\n")
    else:
        print message

def log_verbose(message):
    global verbose
    if verbose:
        log(message)



## 
## Main routine:
## 

program  = sys.argv.pop(0)

verbose = False
if len(sys.argv)>0 and sys.argv[0]=="-v":
    sys.argv.pop(0)
    verbose = True

if len(sys.argv)<1 or len(sys.argv)>2:
    print "%s: usage: %s [-v] <extensions_folder> [<logfile>]" %(program,program)
    sys.exit(1)
extensions_folder = sys.argv[0]
log_file          = None
if len(sys.argv)>=2:
    log_file = open(sys.argv[1], "w")


log_verbose("Scanning for Vocola extensions...")

os.chdir(extensions_folder)
output = open(os.path.normpath(os.path.join(extensions_folder,"extensions.csv")),
              "w")
for file in os.listdir(extensions_folder):
    if  file.startswith("ext_") and file.endswith(".py"):
        process_extension(file[0:-3])
output.close()
