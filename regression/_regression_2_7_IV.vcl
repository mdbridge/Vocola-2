### 
### Regression tests for Vocola 2.7, part IV
### 


## 
## Test runtime errors:
## 

test Eval   bad conversion = EvalTemplate(%i, bar);
test Repeat bad conversion = Repeat(foo, bar);
test Dragon bad conversion = Wait("foo'bar");


(test=x) (Python=2) (bindings=3) = Eval($3 * $1 plus $2);

test bad Dragon = Wait(-1);

try Unimacro unavailable = Unimacro(x);
try bad Unimacro         = Unimacro('"');



$set MaximumCommands 3;

  #try "test Dragon bad conversion continue":
continue = "Didn't stop!";

  # try "this ok this not ok this ok":
this (ok=1|not ok) = Repeat($1, x);


## 
## Test reported error location:
## 

what line is this = Eval(0/0);

what
about
this
line 
=
Eval(0/0)
;  # this line number is reported

include ".\.\regression_2_7_IV_ugly'name.vch";



## 
## Test reported command specification:
## 

<x> := ( 1 );

yell <x> 1..9 ( 2 | 3) = Wait(foo);

"don't" yell           = Wait(foo);
  # "yell open quote":
yell '"'               = Wait(bar);

  # this doesn't appear to be recognizable, but can check compiler output:
yell "\"               = Wait(foo);


yell (1 = Wait(foo) | 2 = Wait(bar)) = $1;
