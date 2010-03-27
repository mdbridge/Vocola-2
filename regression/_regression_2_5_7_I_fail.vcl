### 
### Test code that checks how many arguments a function can have:
### 
###   These commands should all give compiler errors unless otherwise noted.
### 

# 
# Vocola built-ins:
# 
too few  Vocola arguments       = Repeat(1);
too many Vocola arguments       = Repeat(1,2,3);

# 
# Dragon procedures taking a fixed number of arguments:
# 
too few arguments               = MsgBoxConfirm(1,2);
too many arguments              = MsgBoxConfirm(1,2,3,4);

# 
# Dragon procedures taking a variable number of arguments:
# 
too few variable arguments      = WinHelp(1);
just right variable arguments   = WinHelp(1,2);          # not an error
just right variable arguments 2 = WinHelp(1,2,3);        # not an error
too many variable arguments     = WinHelp(1,2,3,4);

# 
# User functions:
# 
M() := 1;
too many user arguments         = M(1);
U(x) := $x;
D(y) := U($y,$y);                                        # error
