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


## 
## Optional grammar elements:
## 

<list> := (list);

empty [] terms = parsing error;

  # at least one term must be non-optional:
[everything optional]   = error;
[separately] [optional] = error;
[0..1] [<list>]         = error;
[[doubly]]              = error;
([all] | there)         = error;
<foo> := (bar | <_anything> [there] | foo);  # error now (2.8.6) due to Alternative cannot contain a variable instead
done panicking = true;
nesting [there [error ([<list>])]] = error;


  # test verify_reference_menu still works for non-optional terms:
(reference in menu 1..9) is            = $1;
(list in menu list <list>) is          = $1;
(anything in menu list <_anything>) is = $1;
(other (menu))                         = $1;
(other 1..9)                           = $1;
(1..9 other)                           = $1;
(1..9=1)                               = $1;
(1..9 | other)                         = $1;

  # test still works when introduce optional terms:
(reference in menu [1..9]) is            = $1;
(list in menu list [<list>]) is          = $1;
(anything in menu [list <_anything>]) is = $1;
(other [(menu)])                         = $1;
(foo [other 1..9])                       = $1;
([1..9] other)                           = $1;
([1..9] | other)                         = $1;
