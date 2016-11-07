### 
### Determining what kind of statement we have is tricky because it
### can take several tokens to decide.  Here are some of the cases
### that require lookahead.
### 

this is a context:

<list>  :=  1=1 | 2=2;
<list1> := (3 | 4=5);

Foo()           := no arguments;
Bar(x)          := one argument;
Baz(x,y3)       := two arguments;

include "empty.vcl";
include empty.vcl;

$set a b;
$set "err" 'see';
$set 'x' "z";


[optional] word = action;
(body)          = action;
word            = action;
"quoted"        = action;
'single'        = action;
2..99           = action;
<list>          = action;

first [optional] word = action;
first (body)          = action;
first word            = action;
first "quoted"        = action;
first 'single'        = action;
first 2..99           = action;
first <list>          = action;

first second [optional] word = action;
first second (body)          = action;
first second word            = action;
first second "quoted"        = action;
first second 'single'        = action;
first second 2..99           = action;
first second <list>          = action;
first second                 = action;

first second third [optional] word = action;
first second third (body)          = action;
first second third word            = action;
first second third "quoted"        = action;
first second third 'single'        = action;
first second third 2..99           = action;
first second third <list>          = action;
first second third                 = action;

first "second" [optional] word = action;
first "second" (body)          = action;
first "second" word            = action;
first "second" "quoted"        = action;
first "second" 'single'        = action;
first "second" 2..99           = action;
first "second" <list>          = action;
first "second"                 = action;

first second "third" [optional] word = action;
first second "third" (body)          = action;
first second "third" word            = action;
first second "third" "quoted"        = action;
first second "third" 'single'        = action;
first second "third" 2..99           = action;
first second "third" <list>          = action;
first second "third"                 = action;

menu( [optional] word ) = action;
menu( (body)          ) = action;
menu( word            ) = action;
menu( "quoted"        ) = action;
menu( 'single'        ) = action;
menu( 2..99           ) = action;
menu( <list>          ) = action;

menu( first [optional] word ) = action;
menu( first (body)          ) = action;
menu( first word            ) = action;
menu( first "quoted"        ) = action;
menu( first 'single'        ) = action;
menu( first 2..99           ) = action;
menu( first <list>          ) = action;
menu( first | second        ) = action;
menu( first = action        ) = action;

menu(word) [optional] = action;
menu(word) (body)     = action;
menu(word) word       = action;
menu(word) "quoted"   = action;
menu(word) 'single'   = action;
menu(word) 2..99      = action;
menu(word) <list>     = action;
