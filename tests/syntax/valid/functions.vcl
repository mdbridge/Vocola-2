### 
### Test parsing of <function>
### 
###   Tests valid functionName's,  both in function declaration and call
###   Tests valid (formal) name's, both in function declaration and use
### 

no_actions()              :=;
name()                    := action;
under_score(single)       := action actions;
with_digits10(a, b)       := name() "word" 'word' $a $b; 
_leading(a10, b_c, _d)    := action under_score($b_c) $_d $a10;
UPPER(UP)                 := _leading(with_digits10($UP, $UP), 1, 2);
x()                       := UPPER(10);
use(a, a10, b_c, _d, UPP) := "$a$a10$b_c$_d$UPP";
last()                    := x();

# backup tokenization tests:
name1 ( ):=action last ( ) ;


command in file = ;
