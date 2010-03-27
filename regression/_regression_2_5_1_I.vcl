### 
### Voice commands for testing that known bugs in 2.5 have been fixed, part I
### 


## 
## Test passing quotes, newlines, and carriage returns to user functions:
## 

user_again(x)          := $x;        
user(x)                := user_again($x);
regression user quotes  = user(< ' " """ \ \n '  " ' ''' \" 
			       % Eval('"\n"') %
			       Eval('"\r"') % >);


## 
## Test passing quotes, newlines, and carriage returns to Dragon functions:
## 

regression pass ( quotes = " ''' " ' """ \" \n\' 
                | newline = Eval('"\n"') 
		| return = Eval('"\r"') ) = 
     MsgBoxConfirm("We got <$1>!", 64, "Passing to Dragon functions test");



## 
## Test including quotations by doubling them:
## 

regression doubling = "1 double: "" 2 single: ''; "
		      '2 double: "" 1 single: '''
		      "; 2 double: """"";


## 
## Test quotations not preceded by whitespace:
## 

regression embedded quotations = cow"ran north"fast;



## 
## Test handling of quotations in comments:
## 

strange        = red # green's luck
	         blue;

stranger still = red # green"s luck
	         yellow # "" ''
		 blue;
