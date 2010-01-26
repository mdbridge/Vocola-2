### 
### Regression tests for Vocola 2.7, Part I
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



## 
## Test transform of Eval into EvalTemplate:
## 

no arguments eval               = Eval(2+2);
eval add 0..9 0..9              = Eval($1 + $2);


repeated eval add 0..9 0..9     = Eval('($1 + $2) * $1');

  # = -5
all sorts of (arguments=3) 1..1 = 
	Eval(2 + $1 - $2 + Eval(3*3) - ID(12) - EvalTemplate(%i*2, 3));

more eval arguments = Eval(1 + Repeat(3, 1));                       # = 112
eval with Dragon    = Eval(SendDragonKeys(Fred));		    # error

F(x) := Eval($x - 2);
eval in a function  = F(7);                                         # = 5


Unrolling(x,y) := $x + $y;
eval with unrolling = Eval(Unrolling(2,3));                         # = 2+3


test string (Argument)          = Eval('$1.lower()');
test ambiguous arguments <case> = Eval($1-2);

  # works: number, minus, zero
<case> := (string    | number = 13      | plus = +14        | minus = -3 
          | zero = 0 | double zero = 00 | leading zero = 03
	  ); 

  # = 1-14450
eval (everywhere=Eval(1)) = $1 F(1) Repeat(Eval(3-1), Eval(2+2)) 
	                    Eval(Eval(2+3)) SendDragonKeys(Eval(2-2));

test templates with percent (sign=2) = Eval(4 % $1) Eval("'%a %i %s %x %%'");
