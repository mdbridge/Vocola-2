### 
### Voice commands for testing that known bugs in 2.5.3 have been fixed,
### part I
### 


## 
## Test that empty alternatives in lists work:
## 

<l> := (red = | blue = 2);
the empty alternative is <l> = $1;


## 
## Test passing quotes, newlines, and carriage returns to Dragon functions:
## 
##   Note: passing newlines and carriage returns should now work.
## 

regression pass ( quotes = " ''' " ' """ \" \n\' 
                | newline = Eval('"\n"') 
		| return = Eval('"\r"') ) = 
     MsgBoxConfirm("We got <$1>!", 64, "Passing to Dragon functions test");


## 
## Test new escaping of $'s rule:
## 

  # these should produce no backslashes:
test escaping 1..1 = $ \$ \$a \$_ \$1 \$% $1;
test escaping 2..2 = x$ x\$ x\$a x\$_ x\$1 x\$% x$1;

  # three backslashes, four dollar signs:
test escaping 3..3 = $$%$$1\%\\$1\;


## 
## Test that context alternatives containing balanced quotes, backslashes, and
## newlines don't produce illegal Python code.
## 

contains
a
newline | contains "" ' -1/0 ' quotations | \ :

command in context = 1;


## 
## Test that the empty context removes all context restrictions:
## 

:
this command still works = 1;
