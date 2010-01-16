### 
### Regression tests for Vocola 2.7
### 


## 
## Test new built-in, EvalF(...):
## 

  # wrong number of arguments at compile time:
#too few arguments         = EvalF();                         # FAILS to compile
one is okay                = EvalF(2+2);
two is also fine           = EvalF(-%i, +003);

  # wrong number of arguments at runtime:
promised an extra argument = EvalF('%i+%i', 2);
provided an extra argument = EvalF('%i+%i', 2, 3, 4);         # no error...

  # different kinds of descriptors:
all descriptor types       = EvalF('%s[%i%%%a]', abc, 3, 2);
unknown descriptor         = EvalF('%u');                     # runtime error...

  # make sure ambiguous descriptor works correctly:
ambiguous descriptor       = EvalF('%a[%a]', abc, 1);
ambiguous descriptor two   = EvalF('%a[%a]', 012, 0);         # non-canonical...

  # test conversions:
bad argument               = EvalF(%s, SendDragonKeys(Fred)); # runtime error...
bad conversion             = EvalF(%i, foo);                  # runtime error...

  # check for compilation errors due to reusing names...
ID(x) := $x;
nested evaluation          = EvalF(-%i, ID(EvalF(%i/2, 20))); # = -10

  # check Python eval errors:
bad Python                 = EvalF('nonsense 1 %i 3', 2);     # runtime error...
bad Python two             = EvalF(1 / 0);                    # runtime error...
