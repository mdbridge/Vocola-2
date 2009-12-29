### 
### Voice commands for testing that known bugs in 2.6.1 have been fixed:
### 


## 
## Test handling of strings containing quotes, multiple times works:
## 

between ( single="'" | double='"' | triple="'''" | hex='"""') quotes =
	$1{ctrl+space}$1{ctrl+x}{ctrl+x};

