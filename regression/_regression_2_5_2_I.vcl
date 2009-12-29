### 
### Voice commands for testing that known bugs in 2.5.1 have been fixed,
### part I
### 
### *:  In 2.5.8, answer was (incorrectly) 10.
###


## 
## Test passing octal numbers:
## 

pass octal to Dragon = MsgBoxConfirm("0010", 64, 
                                     "below is a four digit string");

  User(string) := $string;
pass octal to user function = User("0010");   # should produce 0010


pass octal to eval = Eval(0010 + 2);          # should produce 10

  User2(string) := Eval($string);
pass octal to eval via user = User2(0010);    # should produce 0010  [*]

  User3(string) := Eval($string + 1);
pass minus = User3(-1);		              # should produce 0


## 
## Test that names starting with underscores are now legal:
## 

_Function(_formal) := $_formal "<$_formal>";
<_list> := (red | blue);
<_list> names with underscores = _Function($1);

followed by anything <_anything> = "'$1'";


## 
## Test that a list of formals may have leading or trailing whitespace:
## 

Legal ( one , two ) := $one;
