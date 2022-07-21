### 
### Regression tests for Vocola 2.8.8
### 

# check for top level command with no concrete or inlineable terms:

<_anything>		= "just dictation is not allowed";
<_anything> <_anything> = "just dictation is not allowed";

<x> := (one | two);

[<x>] <_anything>    = die;
[no <x>] <_anything> = die;


# not an issue

1..9 <_anything>  = ok;
<_anything> <x>	  = ok;
<_anything> word  = ok;

<_anything> (x|y) = ok;
