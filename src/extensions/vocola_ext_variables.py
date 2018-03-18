### 
### Variable module:
### 

class UndefinedVariable(LookupError):
    pass


variables = {}


# Vocola procedure: Variable.Set
def variable_set(name, value):
    variables[name] = value


# Vocola procedure: Variable.Unset
def variable_unset(name):
    del variables[name]


# Vocola function: Variable.Get,1-2
def variable_get(name, if_undefined=None):
    try:
        return variables[name]
    except KeyError:
        if if_undefined!=None:
            return if_undefined
        else:
            raise UndefinedVariable( 
                "Variable.Get: variable '" + name + "' is currently undefined")


# 
# [advanced]
# 
# Like Variable.Set, but functional, returning "".  Intended for use
# in user functions that can return string values and need to avoid
# reevaluating arguments.
# 

# Vocola function: Variable.Let
def variable_let(name, value):
    variables[name] = value
    return ""
