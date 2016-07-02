### 
### Regression tests for Vocola 2.8.6, part VI
### 

##
## <_anything> is now allowed in optional parts by itself
##

optional dog says [<_anything>] = "barking: $1";
	 cat says  <_anything>  = "meowing: $1";

optional elephant [[says] <_anything>] = "trumpeting: $1";
