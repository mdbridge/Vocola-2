### 
### Test parsing of context_statement's
### 

: # empty
word:
word | word:
word |word | word:

   white  space   |   here   :

| empty:
empty|:
||:

multiple: per: line:
f::                      # parses as f: :

context: f() := 3;
context: <l> := menu;
context: $set numbers one;
context: command is here =;

at end:
