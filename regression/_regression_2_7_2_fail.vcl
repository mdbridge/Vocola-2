### 
### Regression tests for Vocola 2.7.2  (failing)
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
##   all but the first two of these are errors.
## 

<x>  := 0..9;
<xx> := (0..9);

<y>  := <x>;
<yy> := (<x>);

<z>  := <x> | <x>;
<q>  := (<x> | <x>);
<qq> := ((<x> | <x>));

<a> := <_anything>;

<r> := 1..2 | 3..4;
<r2> := (1..2 | 3..4);
<r3> := (1..2) | (3..4);
<r4> := ((1..2)) | ((3..4));

<ra> := ((1..2 = red));
<rb> := red | 0..2;
