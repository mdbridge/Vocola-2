### 
### Regression tests for Vocola 2.8.5, part I
### 


#
# Make sure includes are relative to file they occur in, duplicate
# include file detector is not fooled by alternate paths to same file.
#

include  subdirectory\_regression_2_8_5_II.vch;
include  subdirectory\..\subdirectory\_regression_2_8_5_II.vch;

# ideally, an absolute filename:
#include  /home/mdl/voice/Vocola_development/Vocola_2/regression/subdirectory/_regression_2_8_5_II.vch;
