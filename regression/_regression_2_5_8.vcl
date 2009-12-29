### 
### Voice commands for testing that known bugs in 2.5.7 have been fixed,
### 


## 
## Test passing noncanonical numbers to Eval:
## 

<vv> := ( double = 00 | ten = 010 | plus = +2 | minus = -0010
        | double plus = ++3 | plus zero = +0 );

pass <vv> to eval = Eval(3*$1);
