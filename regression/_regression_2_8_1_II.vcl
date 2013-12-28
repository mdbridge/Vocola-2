### 
### Regression tests for Vocola 2.8.1, part II
### 

## 
## New built-in function, If:
## 

<values> := (true|big true="True"|upper true="TRUE"|false|empty=""|garbage|0|1);

  # What triggers condition (instruction should produce an error
  # message, all trues should cause if-part):
test if with <values> = 
    If($1, if-part, else-part) " " If($1,if-part2) {enter};

  # instructions work:
test if instructions <values> = If($1,TTSPlayString("If part"),
                                      TTSPlayString("Else part"));

test nested if <values> = If(true, If($1,inner-if, inner-else));

test if fitness (0|1)     = If(Eval("$1==0"),yes,no);
test if fitness (foo|bar) = If(Eval("$1=='foo'"),yes,no);

test if short-circuits = If(true, yes, Eval(1/0)) If(false, Eval(1/0), yes) 
    If(false, Eval(1/0));


## 
## New built-in function, When:
## 

  # What triggers condition (instruction should produce an error message):
test when (empty=""|true|false|0|1|blank=" "|instruction=Beep()) = 
    When($1, when-part, else-part) " " When($1,when-part2) {enter};

  # instructions work:
test when instructions (empty=""|full) = When($1,TTSPlayString("When part"),
                                                 TTSPlayString("Else part"));

test nested when (empty=""|full) = When(true, When($1,inner-when, inner-else));

test when short-circuits = When(true, yes, Eval(1/0)) When("", Eval(1/0), yes) 
    When("", Eval(1/0));

test when fitness [(ready)] = When($1,READY,not_ready);



## 
## Optional grammar elements:
## 

# optional words:

test optional [individual] word                 = works;
test optional ["quoted words"] quoted           = qworks;
test optional [two words]                       = 2works;
test optional [three words can] work            = 3works;
test optional ["three quoted" "words"] can work = 3qworks;

<test> := (optional ["three quoted" "words"]);

test list <test> = $1;
test inline (optional ["three quoted" "words"]) = $1;


# repeated words (old implementation had trouble with these):

test repeated dummy [dummy] [dummy] dummy 1..9 = $1;
test repeated again [dummy] [dummy] 1..9       = $1;
test repeated again [dummy] [dummy] not 1..9   = $1;


# various combinations:

<list> := (list=LIST);

omit [1..9] range      = $1;
omit [<list>] list     = $1;
omit [(inline)] inline = $1;

omit combo one [word word <list> 1..9 (inline=I)] = $1/$2/$3;
omit nested [1..9 [1..9 [1..9]]]                  = $1/$2/$3;
omit nested backwards [[[1..9] 1..9] 1..9]        = $1/$2/$3;
omit orthogonal [1..2] [3..4] [5..6]              = $1/$2/$3;
omit mixture 1..9 [<list>] (outline) [(inline)]   = $1/$2/$3/$4;


# removing references:

F(x) := $x;

removing 1..9 [10..20] 1..9            = $1$1/ F($2)$2/$3 $3;
removing 1..9 30..40 [10..20]          = $1$1/ F($2)$2/$3 $3;
removing [10..20 50..60] 1..9 1..9 red = $1$1/ F($2)$2/$3 $3/$4;


# test where default "" can be inserted:

test insert [1..9]    into text = "got $1!";
test insert [(hello)] into Eval = Eval('len($1)');
