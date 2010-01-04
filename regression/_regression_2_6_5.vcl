### 
### Regression testing for Vocola 2.6.5
### 


## 
## Verify bug with formal references containing digits in quoted
## strings is gone:
## 

Digits(x14) := "<$x14>";

test digits in formal reference = Digits(74);


## 
## Check that SendDragonKeys call is working again:
## 

  # sends "{left}+a+":
test SendDragonKeys = {left SendDragonKeys(}) SendDragonKeys(+a{NumKey+});

test combos         = ButtonClick(1,1) SendDragonKeys(Fred) Beep();


## 
## Check sadly that SendKeys is equivalent to SendDragonKeys for
## recent versions of DNS:
## 

test SendKeys = SendKeys(+a);      # ideally would produce A
