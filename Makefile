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
	cp src/README.html	     build/Vocola/
	cp src/Release*.txt	     build/Vocola/
	#
	# commands:
	#
	# exec:
	cp src/exec/*.exe	     build/Vocola/exec/
	cp src/exec/*.pl	     build/Vocola/exec/
	cp src/exec/*.py	     build/Vocola/exec/
	#
	# extensions:
	cp src/extensions/README.txt build/Vocola/extensions/
	#cp src/extensions/*.py      build/Vocola/extensions/
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

clean::
	rm -rf build


## 
## Installing to the NatLink installer repository:
## 

short_compare: prepare
	@echo "=========="
	@-diff --brief -b build/Vocola/to_MacroSystem/_vocola_main.py \
                           ${NATLINK}/MacroSystem/
	@-diff --brief -b build/Vocola/to_core/VocolaUtils.py \
                           ${NATLINK}/MacroSystem/core/
	@-diff --brief -r -x .svn -b build/Vocola ${NATLINK}/Vocola

compare: prepare
	@echo "=========="
	diff -r -x .svn -b build/Vocola ${NATLINK}/Vocola 
	diff build/Vocola/to_core/VocolaUtils.py \
                ${NATLINK}/MacroSystem/core/
	diff build/Vocola/to_MacroSystem/_vocola_main.py \
                ${NATLINK}/MacroSystem/_vocola_main.py


install: prepare
	(cd build/Vocola; find . -type f -exec cp {} ${NATLINK}/Vocola/{} \;)
	cp build/Vocola/to_MacroSystem/_vocola_main.py \
                           ${NATLINK}/MacroSystem/
	cp build/Vocola/to_core/VocolaUtils.py \
                           ${NATLINK}/MacroSystem/core/
	@echo
	@echo "***** Do not forget to update version number in natlinkInstaller/setupnatlinkwithinno.py"
