### 
### Voice commands for testing that known bugs in 2.5.3 have been fixed,
### part II
### 


## 
## Test whether backslashes are doubled in include statements:
## 

include one\only;


## 
## Test escaping of dollar signs in include statements:
## 

include \$no\$%\$ref\$;
include \$valid\$%\$ref\$$COMPUTERNAME;
include \$before$COMPUTERNAME\$middle$COMPUTERNAME\$after;


## 
## Verify substitution done only once:
## 

include \$$COMPUTERNAME;


## 
## Verify references in include statements have the same validity rules as
## references in actions:
## 

include $123;
include $12ee;  # = 12
include $_e_3;

