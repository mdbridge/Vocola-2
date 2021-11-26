### 
### Module DragonProxy
### 
### Author:  Mark Lillibridge
### Version: 1.0
### 

import VocolaUtils

use_send_input = True
verbose = True


def do_nothing(keys, action):
    pass

callback = do_nothing


def proxy_playString(keys):
    callback(keys, None)

    if use_send_input:
        if verbose:
            print("playString->SI("+ repr(keys) + ")")
        import vocola_ext_keys
        vocola_ext_keys.send_input(keys)
    else:
        # Example of what you can do with this proxy:
        # # DNS 11.5 @ bug workaround (change @ to shift+2 including in {ctrl+@}):
        # # (DNS uses alt_numpad to send @s, but this doesn't work for ctrl+@, etc.)
        # keys = re.sub(r"""(?x) 
        #                   \{ ( (?: [a-zA-Z\x80-\xff]+ \+ )* )
        #                         @
        #                   ( (?: [ ] \d+)? ) \}""", r'{\1shift+2\2}', keys)
        # keys = re.sub(r"""@""", "{shift+2}", keys)

        if verbose:
            print("playString->SDK("+ repr(keys) + ")")
        VocolaUtils.direct_playString(keys)

def proxy_Dragon(function_name, argument_types, arguments):
    if function_name == "SendDragonKeys":
        callback(arguments[0], None)
    else:
        script = function_name
        callback(None, script)

    if verbose:
        print("Dragon: "+function_name+"("+repr(argument_types)+": "+repr(arguments)+")")
    VocolaUtils.direct_Dragon(function_name, argument_types, arguments)


# Vocola procedure: DragonProxy.SetVerbose
def set_verbose(verbose_on):
    global verbose
    if verbose_on == "true":
        verbose = True
    else:
        verbose = False

# Vocola procedure: DragonProxy.SetUseSendInput
def set_use_send_input(use_send_input_on):
    global use_send_input
    if use_send_input_on == "true":
        use_send_input = True
    else:
        use_send_input = False
