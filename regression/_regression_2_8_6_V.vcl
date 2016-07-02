### 
### Regression tests for Vocola 2.8.6, part V
### 

##
## Test handling of contexts for global grammars
##

this is a global command = global;

fire:
  only with fire = fire;

water:
  only with water = water;
:

this is another global command = global;


##
## Also test with command sequences on
##
##  (cannot mix fire and water commands in the same sequence due to
##   limitation against mixing commands from different contexts in same
##   utterance)
##

#$set MaximumCommands 2;


##
## Also test with a specific application (Xterm?)
##
