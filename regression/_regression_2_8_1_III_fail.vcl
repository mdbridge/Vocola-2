### 
### Regression tests for Vocola 2.8.1, part III
### 


## 
## Attempts to redefine existing built-ins should now generate errors:
## 

Eval(x) := error;
allow = panic;

Repeat(x) := error;
allow 2 = panic;

EvalTemplate(x) := error;
allow 3 = panic;

Unimacro(x) := error;
allow 4 = panic;


## 
## New built-in function, If:
## 

too few if arguments  = If();
too many if arguments = If(a,b,c,d);

If(a,b,c) :=  attempt to redefine a built-in;
allow 5 = panic;


## 
## New built-in function, When:
## 

too few when arguments  = When();
too many when arguments = When(a,b,c,d);

When(a,b,c) :=  attempt to redefine a built-in;
