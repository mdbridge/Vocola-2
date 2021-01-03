### 
### Module Keys
### 

import vocola_ExtendedSendDragonKeys
import vocola_SendInput



# Vocola procedure: Keys.SendInput
def send_input(specification):
    vocola_SendInput.send_input(
        vocola_ExtendedSendDragonKeys.senddragonkeys_to_events(specification))
