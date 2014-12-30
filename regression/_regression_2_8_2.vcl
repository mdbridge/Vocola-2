### 
### Regression tests for Vocola 2.8.2
### 

## 
## Recursive commands (one command in a grammar (indirectly) calls another) bug:
## 

  # should produce "called<#>"
test recursive 1..100 = 
     HeardWord(call, subroutine)
     $1;
call subroutine = "called";

  # call this, then say "call subroutine" then click "ok" -- should get waiting spoken
does processing stop 1..20 = MsgBoxConfirm(change,52,warning) TTSPlayString(Waiting $1);
