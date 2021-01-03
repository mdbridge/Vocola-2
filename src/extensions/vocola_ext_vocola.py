### 
### Vocola module:
### 

from __future__ import print_function

import sys

from VocolaUtils import VocolaRuntimeError
from VocolaUtils import VocolaRuntimeAbort  # version 2.8.5+


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
