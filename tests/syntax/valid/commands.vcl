### 
### Test parsing of <top_command>
### 


Word = ;
"word" 'word' = action;
word word word = action actions;

<x> := list;

word <x> <_anything> 1..10 (menu) [word] ['word'] = action;
0..10 00..02 10..0 100..200 3..7 = ranges;

(word = action) (word2 = action | word3) ((word)|(word|word)) = ;



## Vocola 2.8.1+:

non-optional [word 'word'] [<x>] [non-optional <_anything>] [1..10] 
  [non-optional [word]] [(menu)] = $1 $2 $3 $4 action;

non-optional [word <x> <_anything> 1..10 (menu) [word] ['word']] = 
    $1 $2 $3 $4 action;

non-optional [foo [word <x> <_anything> 1..10 (menu) [word] ['word']]] = 
    $1 $2 $3 $4 action;

