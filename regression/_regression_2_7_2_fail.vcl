### 
### Regression tests for Vocola 2.7.2
### 


## 
## Check range syntax:
## 

valid range 1..2  = $1;

invalid range ..  = $1;   # error (nothing to reference as word not range)
invalid range ..2 = $1;   # error (nothing to reference as word not range)
invalid range 1.. = $1;   # error (nothing to reference as word not range)


## 
## Check menu verification:
## 

