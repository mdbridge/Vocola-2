### 
### Voice commands for testing new Unimacro built-in
### 

## 
## Verify that Unimacro built-in is recognized; also check that it
## works correctly when Unimacro is absent/disabled/enabled:
## 
run Unimacro = Unimacro(foobar);


## 
## Check handling of Unimacro's argument:
## 
## OK: string, number, eval, empty, quote
## 
## (more recent versions of Unimacro give an error when presented with ")
## 

<argument> := (string        = "Fred"                                    | 
               Dragon        = ButtonClick(1)                            | 
               number        = 13                                        | 
               Unimacro      = Unimacro('x"y')                           |
               mixture one   = ButtonClick(2) y ButtonClick(3)           |
               mixture two   = ButtonClick(2) y Unimacro(3)              |
               mixture three = ButtonClick(1) ButtonClick(2) Unimacro(3) |
               eval          = Eval("2+2")                               |
               empty         = Repeat(0, 0)                              |
               quote         = '"');

call Unimacro with <argument> = Unimacro($1);


## 
## Check that cannot convert an Unimacro call to a string or integer:
## 

convert to string  = MsgBoxConfirm(Unimacro("foo"), 0, "title");
convert to integer = MsgBoxConfirm("foo", Unimacro(0), "title");


## 
## Check sequencing of multiple calls:
## 

check sequencing = a Unimacro(b) c Unimacro(d) Unimacro(e) f
	           HeardWord(golf) HeardWord(hotel)
	           Unimacro(i) Unimacro(j) k;


## 
## Make sure examples in documentation work:
## 

paste Greek Delta = Unimacro("U Delta");

  # from Unimacro.vch:
WINKEY(t) := Unimacro("USCWINKEY $t USC");

open explorer = WINKEY(e);
