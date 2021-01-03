### 
### Date module:
### 

from datetime import datetime       # requires Python 2.3 or later


# information on format can be found at:
#    http://docs.python.org/library/time.html#time.strftime

# Vocola function: Date.Now,0-1
def now(format="%B %d, %Y"):
    return datetime.now().strftime(format)
