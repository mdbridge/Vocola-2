# -*- coding: iso-latin-1 -*-
### 
### Regression tests for Vocola 2.7, part V
### 


## 
## Test that underscore not converted to a space outside of keystrokes:
## 

"don't" convert    = Fred_George _ {space}_{space} {{} _ };

partial keystrokes = tab_3} {tab_2;


## 
## Test conversion in valid keystrokes:
## 

underscore keystroke = {_} {__3} "|{_ 3}" '|' {shift+__2} 
                       '|' {leftshift+__1} {shift+shift+__2}
		       '|' {shift+_};

brace keystroke = {shift+{_2} '|' {leftshift+shift+{};

symbol keystrokes = {NumKey/_2} {NumKey*_2} {NumKey-_2} {NumKey+_2} {NumKey._2};

function keystrokes = {f1_2} {f12_2};

large count = {*_40};

(with=a) (references=3) = {$1_2} {b_$2} {$1_$2};

separated keystrokes = { a _ 3 };

(totally='{') (evil='}') (here='_') = $1x$3 3$2;


# The following are valid keystrokes for foreign versions of DNS:
accented names  = {Entrée_3} {PavéNum-_3};
other spellings = {LinksAlt+LinksStrg+S-Abf_9};



## 
## Test that flushing breaks up keystrokes:
## 

pause in middle = {a Wait(0) _2};


## 
## Some testing of invalid keystrokes:
## 

bad names = {red%_2} {bl.ue+__3};

no count = {a_} {tab_};

nested keystrokes = {a {b_3} {{{_3};
