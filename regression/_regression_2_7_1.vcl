### 
### Regression tests for Vocola 2.7.1
### 


## 
## Test that call names may now contain dots, but not function definitions:
## 

Ok1()         := 1;
Bad.one()     := 2;         # error
.another()    := 3;         # error
trailing.()   := 4;         # error
more.then.1() := 5;         # error

  # these should be unknown function errors, not syntax errors:
unknown function one   = Bad.one(2);
unknown function two   = .another();
unknown function three = trailing.();
unknown function four  = more.then.1();

