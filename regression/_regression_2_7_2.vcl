### 
### Regression tests for Vocola 2.7.2 (non-failing)
### 


## 
## Test <_anything> bug fix:
## 

  # comment all but it most one of the below at a time:

#$set numbers "";
#$set numbers "zero";
#$set numbers "zero,one";
#$set numbers "zero, one, two";
#$set numbers "plus zero";


full 0..20                = $1;

rabbit 1..30              = $1;
hat ((3..40))             = $1;

not range (1 | 2 | three) = $1;
