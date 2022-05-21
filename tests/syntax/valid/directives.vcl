### 
### Test parsing of <directive>
### 
###   Assumes environment variables set as follows:
### 
###     a    = test
###     UU   = _
###     a10  = include
###     _l   = _
###     a_b  = file
### 

include empty.vcl;
include "empty.vcl";
include 'empty.vcl';
include $a$UU$a10$_l$a_b.vch;
include "$a$UU$a10$_l$a_b.vch";


$set numbers "";
$set numbers zero;
$set numbers "zero,one";


command in file = ;
