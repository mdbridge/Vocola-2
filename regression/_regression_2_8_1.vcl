### 
### Regression tests for Vocola 2.8.1
### 

## 
## Bug fix for list entries containing \'s with actions (produced
## invalid Python code).
## 

test back bug (now | '\'=wrong | '\n'=here) = $1;

<list> := (now | '\'=wrong | '\n'=here);

test backslash bug <list> = $1;


## 
## Bug fix for adjacent <_anything>'s in command sequences
## 

$set MaximumCommands 4;

  # test "Bob radical Bob Tom radical Tom George radical George":
<_anything> radical <_anything> = "<$1||$2>";
