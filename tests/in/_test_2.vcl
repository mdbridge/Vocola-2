<number> := (one = 1 | two | error=Eval(1/0));

test <number> [<number> [<number> [<number>]]] = $1/$2/$3/$4;

[please] offset [(1|2)] [(3|4)] [(5|6)] = $1$2$3;
