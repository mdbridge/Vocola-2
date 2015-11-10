# NatLink repository location:
NATLINK = /home/mdl/voice/NatLink/trunk


## 
## Building a distribution
## 

prepare:
	chmod -R u+w build
	rm -rf build/*
	mkdir build/Vocola
	#
	# top level:
	(cd build/Vocola; mkdir commands exec samples extensions)
	cp src/README.html      build/Vocola/
	cp src/Release*.txt     build/Vocola/
	#
	# commands:
	#
	# exec:
	cp src/dvc2vcl.exe        build/Vocola/exec
	cp src/dvc2vcl.pl         build/Vocola/exec
	cp src/vcl2py.py          build/Vocola/exec
	cp src/scan_extensions.py build/Vocola/exec
	cp src/_vocola_main.py    build/Vocola/exec
	cp src/VocolaUtils.py     build/Vocola/exec
	#
	# samples:
	cp samples/*.vc[hl]       build/Vocola/samples/
	#
	# extensions:
	#cp extensions/*.py        build/Vocola/extensions/
	#
	(cd build; zip -r Vocola Vocola) > /dev/null
	#
	# installer version:
	(cd build; cp -r Vocola installer-Vocola)
	sed 's/[0-9]\.[0-9]\(\.[0-9]\)*/&I/' src/README.html > build/installer-Vocola/README.html
	# HACK for now:  <<<>>>
	cp ${NATLINK}/MacroSystem/_vocola_main.py build/installer-Vocola/exec/

clean::
	chmod -R u+w build
	rm -rf build/*


## 
## Installing to the NatLink installer repository:
## 

short_compare_installer: prepare
	@echo "=========="
	@-diff --brief -b build/installer-Vocola/exec/_vocola_main.py \
                           ${NATLINK}/MacroSystem/
	@-diff --brief -b build/installer-Vocola/exec/VocolaUtils.py \
                           ${NATLINK}/MacroSystem/core/
	@-diff --brief -r -x .svn -b build/installer-Vocola ${NATLINK}/Vocola

compare_installer: prepare
	diff -r -x .svn -b build/installer-Vocola ${NATLINK}/Vocola | more

compare: prepare
	diff -b build/Vocola/exec/_vocola_main.py \
                ${NATLINK}/Vocola/exec/_vocola_main.py | more

install: prepare
	rm -f ${NATLINK}/Vocola/exec/_vocola_main.py
	rm -f ${NATLINK}/Vocola/exec/VocolaUtils.py
	(cd ${NATLINK}/Vocola/exec;ln -s ../../MacroSystem/_vocola_main.py .)
	(cd ${NATLINK}/Vocola/exec;ln -s ../../MacroSystem/core/VocolaUtils.py .)
	(cd build/installer-Vocola; find . -type f -exec cp {} ${NATLINK}/Vocola/{} \;)
	@echo
	@echo "***** Do not forget to update version number in natlinkInstaller/setupnatlinkwithinno.py"
