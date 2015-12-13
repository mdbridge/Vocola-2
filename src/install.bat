REM  Install version of Vocola in same directory as this script
REM  to C:\NatLink\NatLink\Vocola


SETLOCAL
SET target=C:\NatLink\NatLink


CD /d "%~dp0"

mkdir %target%\Vocola
copy README.html	   %target%\Vocola
copy Release-2-6-notes.txt %target%\Vocola
copy Release-2-7-notes.txt %target%\Vocola
copy Release-2-8-notes.txt %target%\Vocola

mkdir %target%\Vocola\commands

mkdir %target%\Vocola\exec\vcl2py
copy exec\*.exe	      %target%\Vocola\exec
copy exec\*.pl	      %target%\Vocola\exec
copy exec\*.py	      %target%\Vocola\exec
del                   %target%\Vocola\exec\*.pyc
copy exec\vcl2py\*.py %target%\Vocola\exec\vcl2py
del                   %target%\Vocola\exec\vcl2py\*.pyc

mkdir %target%\Vocola\extensions
copy extensions\*.* %target%\Vocola\extensions
del                 %target%\Vocola\extensions\*.pyc

mkdir %target%\Vocola\samples
copy samples\*.* %target%\Vocola\samples

copy to_MacroSystem\*.py %target%\MacroSystem
del                      %target%\MacroSystem\*.pyc
copy to_core\*.py	 %target%\MacroSystem\core
del                    	 %target%\MacroSystem\core\*.pyc

REM pause
