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
	#
	# installer version:
	(cd build; cp -r Vocola installer-Vocola)
	sed 's/[0-9]\.[0-9]\(\.[0-9]\)*/&I/' src/README.html > build/installer-Vocola/README.html
	# HACK for now:  <<<>>>
	cp ${NATLINK}/MacroSystem/_vocola_main.py build/installer-Vocola/to_MacroSystem/

clean::
	rm -rf build


## 
## Installing to the NatLink installer repository:
## 

short_compare_installer: prepare
	@echo "=========="
	@-diff --brief -b build/installer-Vocola/to_MacroSystem/_vocola_main.py \
                           ${NATLINK}/MacroSystem/
	@-diff --brief -b build/installer-Vocola/to_core/VocolaUtils.py \
                           ${NATLINK}/MacroSystem/core/
	@-diff --brief -r -x .svn -b build/installer-Vocola ${NATLINK}/Vocola

compare_installer: prepare
	diff -r -x .svn -b build/installer-Vocola ${NATLINK}/Vocola | more

compare: prepare
	diff -b build/Vocola/to_MacroSystem/_vocola_main.py \
                ${NATLINK}/MacroSystem/_vocola_main.py | more

install: prepare
	(cd build/installer-Vocola; find . -type f -exec cp {} ${NATLINK}/Vocola/{} \;)
	cp build/installer-Vocola/to_MacroSystem/_vocola_main.py \
                           ${NATLINK}/MacroSystem/
	cp build/installer-Vocola/to_core/VocolaUtils.py \
                           ${NATLINK}/MacroSystem/core/
	@echo
	@echo "***** Do not forget to update version number in natlinkInstaller/setupnatlinkwithinno.py"
