REM  Install version of Vocola in same directory as this script
REM  to C:\NatLink\NatLink\Vocola


SETLOCAL
SET target=C:\NatLink\NatLink\Vocola


CD /d "%~dp0"

mkdir %target%
copy README.html	   %target%
copy Release-2-6-notes.txt %target%
copy Release-2-7-notes.txt %target%
copy Release-2-8-notes.txt %target%

mkdir %target%\commands

mkdir %target%\exec\vcl2py
copy exec\*.exe	      %target%\exec
copy exec\*.pl	      %target%\exec
copy exec\*.py	      %target%\exec
copy exec\vcl2py\*.py %target%\exec\vcl2py

mkdir %target%\extensions
copy extensions\*.* %target%\extensions

mkdir %target%\samples
copy samples\*.* %target%\samples

copy to_MacroSystem\*.py C:\NatLink\NatLink\MacroSystem
copy to_core\*.py	 C:\NatLink\NatLink\MacroSystem\core

REM pause
