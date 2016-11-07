normal command = {enter};

[please] optional word = Beep();
[[long] ways] here = Beep();
#  [1..10] [<foo>] = red;

#  empty [] case = foo;

panic = here;

#all [[optional]] = here;
#all [<_anything>] = here;

test [(foo = Eval(2+2))] = r;

<lisT> := (bar = Eval(3));

a [b] c [d] e = wrong;
a [b] 1..9 [d] e = wrong;
here [1..10] [<lisT>] = $1.$2;
