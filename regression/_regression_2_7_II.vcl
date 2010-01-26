### 
### Regression tests for Vocola 2.7, Part II
### 


## 
## Test unrolling of user functions:
## 

#F() := $undefined;      # FAILS to compile

ID(x) := $x;

Mono(argument1) := a $argument1 ID($argument1) ID(ID($argument1)) c '|';

  # = abbbc|
test mono = Mono(b);


Binary(x,y) := $x ID($x) ID($y) $y SendDragonKeys($x) Eval($y) '|';

  # = 112212|334434|
test binary = Binary(1, 2) Binary(ID(3), ID(ID(4)));


test non-unrolled 0..9 = $1 ID($1) Repeat(ID(2), ID(3)) Unimacro("3")
     		         EvalTemplate(%i+1, $1) Eval($1);

Minus(x) := -$x;
 # = a-3-3-3c|-a444c|
test scope = Mono(Minus(3)) Minus(Mono(4));


  # = 1a222c|2+22+22+22+32-2
unrolling (everywhere=ID(1)) = $1 Mono(2) Repeat(ID(3), ID(2+2)) 
	                    ID(ID(2+3)) SendDragonKeys(ID(2-2));

Evil(x,x) := $x;
  # = 2
double arguments = Evil(1,2);       

Discard(x) := empty;
discarding an argument = Discard(3);
#discarding an error = Discard(Discard(2,3));    # FAILS to compile

passing instructions = ID( SendDragonKeys(Fred) );
