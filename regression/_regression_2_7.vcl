### 
### Regression tests for Vocola 2.7
### 


## 
## Test new built-in, EvalTemplate(...):
## 

  # wrong number of arguments at compile time:
#too few arguments         = EvalTemplate();                  # FAILS to compile
one is okay                = EvalTemplate(2+2);
two is also fine           = EvalTemplate(-%i, +003);

  # wrong number of arguments at runtime:
promised an extra argument = EvalTemplate('%i+%i', 2);
provided an extra argument = EvalTemplate('%i+%i', 2, 3, 4);  # no error...

  # different kinds of descriptors:
all descriptor types       = EvalTemplate('%s[%i%%%a]', abc, 3, 2);
unknown descriptor         = EvalTemplate('%u');              # runtime error...

  # make sure ambiguous descriptor works correctly:
ambiguous descriptor       = EvalTemplate('%a[%a]', abc, 1);
ambiguous descriptor two   = EvalTemplate('%a[%a]', 012, 0);  # non-canonical...

  # test conversions; both are run-time errors...
bad argument               = EvalTemplate(%s, SendDragonKeys(Fred));
bad conversion             = EvalTemplate(%i, foo);

  # check for compilation errors due to reusing names...
ID(x) := $x;
  # = -10
nested evaluation          = EvalTemplate(-%i, ID(EvalTemplate(%i/2, 20)));

  # check Python eval errors (both runtime errors):
bad Python                 = EvalTemplate('nonsense 1 %i 3', 2);
bad Python two             = EvalTemplate(1 / 0);
