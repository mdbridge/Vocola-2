<list> := (
normal |
#[all] [optiona] |
[some] optional |
[a] [b] c [d] |

word |
word word |
#<foo> red |
#red <foo> |
#<_anything>  |
#<_anything> fred |
#1..10 |
#1..10 vo |

[word] end |
[word word] end |
#[<foo> red] end |
#[red <foo>] end |
#[<_anything> ] end |
#[<_anything> fred] end |
#[1..10] end |
#[1..10 vo] end |




last);
