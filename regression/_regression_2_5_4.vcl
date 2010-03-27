### 
### Voice commands for testing that known bugs in 2.5.4 have been fixed
### 


## 
## Test using repeat by itself as an argument to a user function:
## 

User(a, b, c) := <$c>;

test call 1..1 2..2 3..4 = User($1, x, Repeat($2, $3));

test twice call 1..9 1..9 = User(a, b, Repeat($1, Repeat($2, x y)));


## 
## Test using a menu body with multiple actions by itself as an
## argument to a user function:
## 

test menu (1 = 1 2 3) = User(a, b, $1);


## 
## Same tests using a Dragon function instead of a user function:
## 

test Dragon 1..10 = MsgBoxConfirm(Repeat($1, .), 64, "title");

test Dragon (menu = 1 + 2 + 3) = MsgBoxConfirm($1, 64, "title");


## 
## Same tests using eval instead of a user function:
## 

test eval 0..10 = Eval(Repeat($1, *));

test eval (menu = 1 + 2 + 3) = Eval($1);



## 
## These should give a correct error message rather than a nonsense string:
## 

  # no longer an error in 2.7 onwards:
call user with Dragon = User(a, b, Wait(0)); 

call dragon with Dragon = MsgBoxConfirm(Wait(0), 64, "title"); 

call eval with (Dragon=Wait(0)) = Eval( $1 );



## 
## Test calling user functions with arguments that produce nothing (not
## even the string ""):
## 

call user with nothing = User(a, b, Repeat(0, foobar));
again call user with (nothing= ) = User(a, b, $1);



## 
## Test calling eval with all types of arguments:
## 

F(x) := $x;
G(x,y) := Eval($x*$y+$x);

  # correct answer is 6_3_8_c_7_13_9_9_:
call fred (with=1) (stuff=2) =
	Eval(1+ 2+ 3) _            # word's
	Eval($1 + $2 * $1) _       # $1
	G(2,3) _                   # $x
	Eval(F(c)) _		   # user calls
	Eval(F(2)+ F(5)) _
	Eval(F(3)*$2+ F(7)) _
	Eval(Eval(3+4)+2) _	   # Vocola calls, nested eval	
	Eval(F(3) + Eval(F(6))) _
	;

call eval with direct Dragon = Eval(Wait(0));

## 
## Test calling eval with quotation marks:
## 

call unbalanced eval = Eval("' + "" + words[0] + '");



## 
## Test printing of Vocola values:
## 

  # This no longer works usefully in 2.7 onwards:
print value (empty = | key = "x{stop}y" 
	     | quoted = '"red"' ButtonClick(0,0)
             | Dragon = ButtonClick(1,1) 
	     | double Dragon = ButtonClick(1,2) ButtonClick(3,4)
	     | both = x z ButtonClick(7,8) y ButtonClick(1,2)
	     ) = User(a,b,$1);
