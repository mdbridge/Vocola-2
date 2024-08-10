### 
### Vocola module:
### 

from __future__ import print_function

import sys

from VocolaUtils import VocolaRuntimeAbort  # version 2.8.5+
from VocolaUtils import VocolaRuntimeError
from VocolaUtils import to_long


#
# abort utterance without error
#
# Vocola procedure: Vocola.Abort
def vocola_abort():
    raise VocolaRuntimeAbort

# Vocola function: Vocola.Error
def vocola_error(message):
    raise VocolaRuntimeError(message)


# Vocola procedure: Vocola.Alert
def vocola_alert(message):
    print(message, file=sys.stderr)

# Vocola procedure: Vocola.Print
def vocola_print(message):
    print(message)


# Vocola procedure: Vocola.SetRuntimeVerbosity
def vocola_set_runtime_verbosity(level):
    from vocola_common_runtime import set_vocola_verbosity    # Vocola version 2.9+ only
    set_vocola_verbosity(to_long(level))
