range number is 0..99 = '$1 and $1';

two numbers 5..15 times 13..15 = '$1 x $2';

<indirect> := 5..15;
<double> := (1..3);
<triple> := ((2..4));

final <indirect> <double> <triple> = '$1 $2 $3';

last ((9..12)) = $1;

<normal> := 1 | 2 | 3;

normal <normal> ((1 | 2)) = '$1 $2';
