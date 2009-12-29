### 
### Voice commands for testing that known bugs in 2.5.1 have been fixed,
### part II
### 


## 
## Verify that illegal variable names are complained about:
## 

<illegal-list> := (1|2|3);
use <illegal-list> = red;


## 
## Verify that <_anything> is not allowed to be redefined:
## 

<_anything> := (red | blue);
