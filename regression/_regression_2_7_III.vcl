### 
### Regression tests for Vocola 2.7, part III
### 


## 
## Test most basic actions:
## 

test basic actions = "string" 'ulgy"' "ulgy\'" SendKeys({space}) flushed?;


## 
## Test references:
## 

inline (menu) = $1;
inline (menu two | menu three = SendKeys(3)) = $1;

<list> := ( no actions | never actions);
using a <list> list = $1;
<list2> := ( nop | action = one word);
using a <list2> list = x $1 y;
  # make sure references to a list do not flush:
<direction> := ( left | right );
single <direction> action = { $1 };

range 1..10 to 1..10 = $1x$2;

anything <_anything> can be said = $1;


## 
## Test calls:
## 

repeated actions          = Repeat(0,x) Repeat(-1,y) Repeat(1,z) Repeat(2,q);
nested repeats            = Repeat(1 Repeat(2,0), x);  # 100 x's
repeat and flushing       = { Repeat(1, up) };
again repeat and flushing = { Repeat(1, up} SendKeys({right}) {down) };


no arguments Dragon  = Beep();
two arguments Dragon = ButtonClick(2, 1);
Dragon flushes       = { Beep() up};

weird Dragon strings = MsgBoxConfirm(x '"' z "'" '\' Eval('chr(10)') y
                                     Eval('chr(13)') x\, 0, 0);
Dragon type conversion (number=1 | string=foo) = ButtonClick(1, $1);
Dragon NatLink error = ButtonClick(99, 3);


eval template does not flush = { EvalTemplate('"up"') };


Unimacro does flush = { Unimacro('"up"') };


## 
## Test procedural calls not permitted in functional contexts:
## 

top-level okay = Beep();

inline (menu = Beep())     ok = $1;
inline (menu = Beep()) not ok = Wait($1);

<lists> := (one = Beep());

<lists>     ok = $1;
<lists> not ok = Wait($1);

arguments not okay one   = EvalTemplate(Beep());
arguments not okay two   = Unimacro(Beep());
arguments not okay three = Repeat(Beep(), x);
repeat is special        = Repeat(9, Beep());

the (Unimacro = Unimacro(foo) | Dragon = Beep() | Eval = Eval(2+2)
    | Repeat = Repeat(2,1)) call is functional = SendKeys($1);


## 
## Test semantics of nested calls:
## 

nested calls = MsgBoxConfirm(x Eval(2+2) EvalTemplate(%i*2,3) Repeat(2,z) q, 
                             0, 0);

nested eval = Eval(Eval(2) + Eval(3) - Eval(Eval(1)));
