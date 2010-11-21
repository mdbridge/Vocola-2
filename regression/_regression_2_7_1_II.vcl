### 
### Regression tests for Vocola 2.7.1, part II
### 


## 
## Test basic extension functionality:
## 

<v> := (first | second | third);

         set  <v> value 1..10 = Variable.Set($1, $2);
         show <v> value       =  "$1 = " Variable.Get($1, UNDEFINED) "!{enter}";
unsafely show <v> value       =  "$1 = " Variable.Get($1)            "!{enter}";


## 
## Make sure function extension calls act like Eval and function
## procedure calls act like Dragon calls in terms of flushing:
## 

bad  eval template argument = EvalTemplate(%s, Variable.Set(first, -1)); # bad
good eval template argument = EvalTemplate(%s, Variable.Get(first));

bad  eval argument          = Eval(Variable.Set(first, -1));             # bad
good eval argument          = Eval(Variable.Get(first));

this does     flush = {enter Variable.Set(x, 1) };
this does not flush = { Variable.Get(unknown, enter) };


## 
## Make sure extension calls interact with unrolling properly:
## 

Double(x) := "(" $x "!" $x ")";

try unrolling = Double(Double( 
                   Variable.Set(x, Eval(Variable.Get(x, 0) + 1))
		   Variable.Get(x)
                ));

try unrolling again = Variable.Get(unknown, Double(*));
