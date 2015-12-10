CD /d "%~dp0"

mkdir C:\NatLink\NatLink\Vocola
copy README.html	   C:\NatLink\NatLink\Vocola
copy Release-2-6-notes.txt C:\NatLink\NatLink\Vocola
copy Release-2-7-notes.txt C:\NatLink\NatLink\Vocola
copy Release-2-8-notes.txt C:\NatLink\NatLink\Vocola

mkdir C:\NatLink\NatLink\Vocola\exec\vcl2py
copy exec\*.exe	      C:\NatLink\NatLink\Vocola\exec
copy exec\*.pl	      C:\NatLink\NatLink\Vocola\exec
copy exec\*.py	      C:\NatLink\NatLink\Vocola\exec
copy exec\vcl2py\*.py C:\NatLink\NatLink\Vocola\exec\vcl2py

mkdir C:\NatLink\NatLink\Vocola\extensions
copy extensions\*.* C:\NatLink\NatLink\Vocola\extensions

mkdir C:\NatLink\NatLink\Vocola\samples
copy samples\*.* C:\NatLink\NatLink\Vocola\samples

copy to_MacroSystem\*.py C:\NatLink\NatLink\MacroSystem
copy to_core\*.py	 C:\NatLink\NatLink\MacroSystem\core

pause
