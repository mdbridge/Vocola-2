### 
### Regression testing for Vocola 2.6.4, part I
### 


## 
## Voice commands for testing <_anything> handling:
## 
## Note: it is important to test these using multiple words for <_anything>!
## 


handle prefix <_anything> = $1;
<_anything> handle tail = $1;

handle middle <_anything> tail = $1;

handle double <_anything> and <_anything> = $1/$2;

handle bracketed <_anything> and <_anything> face = $1/$2;


optional [word] <_anything> = $1;
[word] optional <_anything> = $1;


[front] <_anything> train = $1;
train <_anything> [back] = $1;


## 
## Added as part of 2.7:
## 

bad case <_anything> <_anything> = $1/$2;

repeated use <_anything> = $1/$1;
