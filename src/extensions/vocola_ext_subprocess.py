### 
### Subprocess module:
### 

from vocola_ext_variables import *

import os
import os.path

class SubprocessError(Exception):
    pass


# 
# Spawns an instance of the executable at path executable in the background
# 
# * executable must be a .exe file
# * does not wait for it to finish or the current window to change
# * arguments is a list of arguments; first argument must be the name
#   of the executable (not a path)
# * If the executable writes to standard out, a black console window will be 
#   created 
#   * this can be avoided by using P_DETACH instead of P_NOWAIT below
# 

# Vocola procedure: Subprocess.Async,2-
def subprocess_async(executable, *arguments):
    pid = os.spawnv(os.P_NOWAIT, executable, arguments)


# 
# Same as above, but waits for process to finish before returning.
# 
# * P_DETACH cannot be used here.
# 
# * Sets the variable exit_code to the process's exit code when it returns.
# 
# * Raises an error if a nonzero exit code is received.
#   * Exception: if executable ends with "-", doesn't do this (strips
#                executable of the - before using)
#

# Vocola procedure: Subprocess.Sync,2-
def subprocess_sync(executable, *arguments):
    require_clean_exit = True
    if executable[-1]=='-':
        require_clean_exit = False
        executable = executable[0:-1]

    pid = os.spawnv(os.P_NOWAIT, executable, arguments)
    pid, exit_code = os.waitpid(pid, 0)
    exit_code = exit_code >> 8
    variable_set("exit_code", str(exit_code))
    
    if exit_code != 0 and require_clean_exit:
        m = "subprocess '%s' returned non-zero exit code %s" % (executable, 
                                                                str(exit_code))
        raise SubprocessError, m


# 
# [Convenience] Wrapper for [A]Sync that takes care of extracting the
# executable name and separating the arguments.
# 
# Behavior depends on end of executable path; by default, calls async.
# If ends with '!', calls sync and requires a clean exit; end with
# '-!' to call sync and not require clean exit
# 

# Vocola procedure: Subprocess.Run,1-3
def subprocess_run(executable, arguments="", separator=" "):
    executable_name = os.path.basename(executable)
    if executable_name.endswith("!"): executable_name = executable_name[:-1]
    if executable_name.endswith("-"): executable_name = executable_name[:-1]

    if arguments != "":
        separated_arguments = arguments.split(separator)
    else:
        separated_arguments = []

    if executable.endswith("!"):
        executable = executable[: -1]
        #print repr([executable, executable_name] + separated_arguments)
        subprocess_sync(executable, executable_name, *separated_arguments)
    else:
        #print repr([executable, executable_name] + separated_arguments)
        subprocess_async(executable, executable_name, *separated_arguments)



## 
## Experiments:
## 

# Vocola procedure: Subprocess.System,1
def subprocess_system(command, require_clean_exit=True):
    exit_code = os.system(command)
    if exit_code != 0 and require_clean_exit:
        m = "Subprocess.System(%s) returned non-zero exit code %s" % \
            (command, str(exit_code))
        raise SubprocessError, m
    return ""
