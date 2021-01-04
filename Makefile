# NatLink repository location:
NATLINK = /home/mdl/voice/NatLink/trunk


## 
## Building a distribution
## 

prepare:
	rm -rf build
	mkdir -p build/Vocola
	#
	# top level:
	(cd build/Vocola; mkdir commands exec extensions samples to_core to_MacroSystem)
	cp src/install.bat	     build/Vocola/
	cp src/install-user-dir.bat  build/Vocola/
	cp src/README.html	     build/Vocola/
	cp src/Release*.txt	     build/Vocola/
	#
	# commands:
	#
	# exec:
	cp src/exec/*.exe	     build/Vocola/exec/
	cp src/exec/*.pl	     build/Vocola/exec/
	cp src/exec/*.py	     build/Vocola/exec/
	mkdir build/Vocola/exec/vcl2py
	cp src/exec/vcl2py/*.py	     build/Vocola/exec/vcl2py/
	#
	# extensions:
	cp src/extensions/README.txt build/Vocola/extensions/
	cp src/extensions/*.py       build/Vocola/extensions/
	#
	# samples:
	cp src/samples/*.vc[hl]      build/Vocola/samples/
	#
	# to_core:
	cp src/to_core/*.py	     build/Vocola/to_core/
	#
	# to_MacroSystem:
	cp src/to_MacroSystem/*.py   build/Vocola/to_MacroSystem/
	#
	(cd build; zip -r Vocola Vocola) > /dev/null
	#
	#
	cp -r build/Vocola build/Vocola_for_NatLink
	rm     build/Vocola_for_NatLink/install.bat
	rm -rf build/Vocola_for_NatLink/to_MacroSystem
	rm -rf build/Vocola_for_NatLink/to_core

clean::
	rm -rf build
	rm -f src/exec/vcl2py/*.pyc


## 
## Installing to the NatLink installer repository:
## 

short_compare: prepare
	@echo "=========="
	@-diff --brief -b build/Vocola/to_MacroSystem/_vocola_main.py \
                           ${NATLINK}/MacroSystem/
	@-diff --brief -b build/Vocola/to_core/VocolaUtils.py \
                           ${NATLINK}/MacroSystem/core/
	@-diff --brief -r -x .svn -b build/Vocola_for_NatLink ${NATLINK}/Vocola
	@grep "including Vocola" ${NATLINK}/natlinkInstaller/setupnatlinkwithinno.py

compare: prepare
	@echo "=========="
	-diff -r -x .svn -b build/Vocola_for_NatLink ${NATLINK}/Vocola 
	@echo "=========="
	-diff -b build/Vocola/to_core/VocolaUtils.py \
                ${NATLINK}/MacroSystem/core/
	@echo "=========="
	-diff -b build/Vocola/to_MacroSystem/_vocola_main.py \
                ${NATLINK}/MacroSystem/_vocola_main.py
	grep "including Vocola" ${NATLINK}/natlinkInstaller/setupnatlinkwithinno.py


install: prepare
	(cd build/Vocola_for_NatLink; find . -type f -exec cp {} ${NATLINK}/Vocola/{} \;)
	cp build/Vocola/to_MacroSystem/_vocola_main.py \
                           ${NATLINK}/MacroSystem/
	cp build/Vocola/to_core/VocolaUtils.py \
                           ${NATLINK}/MacroSystem/core/
	@echo
	@echo "***** Do not forget to update version number in natlinkInstaller/setupnatlinkwithinno.py"
