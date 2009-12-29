### 
### Voice commands for testing that known bugs in 2.5 have been fixed, part II
### 
###   This file should not convert; it exists to test error detection/handling.
### 


## 
## Test ban/detection of multiline quotations:
## 
##   Each statement containing the word "illegal" should produce an
##   unbalanced quotation error with an appropriate line number.
##
##   Note that because of repair, only the last three cause additional
##   statements to have errors. 
## 

this is illegal   = "simple;
  legal but annoying   = command; #";

this is illegal 1 =  simple";
  legal but annoying 1 = command; #";

this is illegal context command "simple "" # :
  legal but annoying 2 = command; #":

<illegal_list> := ( 1 = "one" |
	            2 =  two" |
		    3 = "three" );


this is illegal command = "simple ""
  legal but annoying 6 = command; #";

this is illegal 3 = "simple \
  legal but annoying 3 = command; #";

this is illegal 4 = 'simple \
  legal but annoying 4 = command; #';

this is illegal 5 = simple'
  legal but annoying 5 = command; #';
