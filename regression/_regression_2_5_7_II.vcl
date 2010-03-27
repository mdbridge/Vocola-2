### 
### Test coercion of Dragon call arguments to integer or string
### 

## 
## First, test the conversion code itself:
## 

<value> := ( 0 | 1 | minus one = -1 | plus one = +1 | double zero = 00 |
	     ten = 010 |
	     string = xxx | alpha = x10 | digits = 10x |
	     empty = Repeat(0, "fred") | dragon = 10 Wait(0) 3 );

  # note that negative numbers should correctly produce an illegal
  # argument error:
convert <value> to integer = Wait($1);

convert <value> to string  = MsgBoxConfirm($1,0,$1);


## 
## Test Dragon cases requiring quoted numbers:
## 

test HeardWord = HeardWord(left, 5);



## 
## Make sure WaitForWindow works:
## 

  # note default timeout is 10 seconds
test wait for window = WaitForWindow("*Messages*") {ctrl+home};
