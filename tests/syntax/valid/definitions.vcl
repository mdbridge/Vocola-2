### 
### Test parsing of <definition>
### 
###   Tests valid variable names, both in definition and use
### 

  # reference before use:
<x> <0> <_> <lower> <UPPER> =;
<d09> <d09>                 = $1;
<_leading> <a_b>            = $1;

<x>        := item;
<0>        := command | command;
<_>        := command | command | command;
<lower>    := term = action;
<UPPER>    := term = action | term term = ;
<d09>      := item;
<_leading> := Word = Eval(2 + 2);
<a_b>      := item;


# Multiple alternatives:

<test> :=
    alternative |
    word [word] |
    [word]word[word] |
    "alternative" |
    (menu) |
    (word | word word) |
    ([word]word) |
#
    alternative        = action|
    word [word]        = action|
    [word]word[word]   = action|
    "alternative"      = action|
    (menu)             = action|
    (word | word word) = action|
    ([word]word)       = action
;

<test_2> := (
    alternative |
    word [word] |
    [word]word[word] |
    "alternative" |
    (menu) |
    (word | word word) |
    ([word]word) |
#
    alternative        = action|
    word [word]        = action|
    [word]word[word]   = action|
    "alternative"      = action|
    (menu)             = action|
    (word | word word) = action|
    ([word]word)       = action
);


# Single alternatives:

<single_1> := 1..10;


## Vocola 2.8.1+:

<test_plus> :=
    [word word] word |
    [[word] word] word |
    (word [word] | word [[word word] word]) |
#
    [word word] word                        = action|
    [[word] word] word                      = action|
    (word [word] | word [[word word] word]) = action
;

<test_plus_2> := (
    [word word] word |
    [[word] word] word |
    (word [word] | word [[word word] word]) |
#
    [word word] word                        = action|
    [[word] word] word                      = action|
    (word [word] | word [[word word] word]) = action
);
