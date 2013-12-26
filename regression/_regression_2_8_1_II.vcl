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
