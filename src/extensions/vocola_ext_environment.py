### 
### Module Env (environment):
### 

import os

class UndefinedEnvironmentVar(LookupError):
    pass



# Vocola function: Env.Get,1-2
def get(name, if_undefined=None):
    try:
        return os.environ[name]
    except KeyError:
        if if_undefined!=None:
            return if_undefined
        else:
            raise UndefinedEnvironmentVar("Environment variable '" +
                                          name + "' is undefined")
