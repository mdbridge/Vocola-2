### 
### Regression testing for Vocola 2.6.4, part II
### 

## 
## Test syntax parsing of new $set statement:
## 

$set;
$set ;
$set 14;
$set x 3;          # only non-syntax error
$set y 3 5;

sequence yes;      # check old sequence command is gone
