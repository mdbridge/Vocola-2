# Vocola function:
# ERROR above: no name 

### 
### Regression tests for scan_extensions.py
### 
### Note: for ease of checking resulting extensions.csv file,
### extension name ends with {p|f}<range> and routine name with <actual arg #>
### 

# below ignored:
# Vocola crazy:
def x():
    pass

# ERROR below:
# Vocola function: no_dot_in_name

# below *is* valid:
# Vocola function:          name.dof1            
def          name1       (          arguments        )

# ERROR below: no def line:
# Vocola procedure:named.here.me

# ERROR below: no def line:
#Vocola function: do.1,  2  ,3
def name



## 
## Test argument number handling:
## 

#Vocola procedure: default.herep0
def default0()

#Vocola procedure: default.herep1
def default1(x)

#Vocola procedure: default.herep2
def default2(x,y)


# Vocola function: simple.heref1,1
def simple2(x,y)

# Vocola function: range.heref12-88,12-88
def range0()

# Vocola function: infinite.heref0-,0-
def infinite3(xray, _shgfer, shfg)

# Vocola procedure: spaces.herep1-3,  1  -   3  , foobar
def spaces0():

# Vocola Function: open.heref4,4
def open4(x, y,
          z, w):
