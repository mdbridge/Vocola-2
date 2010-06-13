### 
### Regression tests for Vocola 2.7, part VI
### 

## 
## Test that ShiftKeys works:
## 

please shift click           = ShiftKey(1)             ButtonClick(1, 1);

  # test by dragging a file in explorer holding mouse then say this:
please shift control click   = ShiftKey(1) ShiftKey(2) ButtonClick(1, 1);


please remember point        = RememberPoint();

  # test of these in an Explorer window; adding ctrl should copy not move:
please         drag to point =              DragToPoint(1);
please control drag to point = ShiftKey(2) DragToPoint(1);


  # This appears to have never worked, the Vocola documentation notwithstanding:
try shifting SendKeys        = ShiftKey(1) SendKeys(aaa);
