prepare:
	chmod -R u+w build
	rm -rf build/*
	mkdir build/Vocola
	#
	# top level:
	(cd build/Vocola; mkdir commands exec samples simpscrp)
	cp src/README.html      build/Vocola/
	cp src/Release*.txt     build/Vocola/
	#
	# commands:
	#
	# exec:
	cp src/dvc2vcl.{exe,pl} build/Vocola/exec
	cp src/vcl2py.{exe,pl}  build/Vocola/exec
	cp src/_vocola_main.py  build/Vocola/exec
	cp src/VocolaUtils.py   build/Vocola/exec
	cp -r bin/2*            build/Vocola/exec
	#
	# samples:
	cp samples/*.vc[hl]     build/Vocola/samples/
	#
	# simpscrp
	cp -r src/simpscrp	build/Vocola/
	#
	(cd build/Vocola; find . -name '.svn' -print | xargs rm -rf)
	(cd build; zip -r Vocola Vocola) > /dev/null

clean::
	chmod -R u+w build
	rm -rf build/*


compare_installer: prepare
	diff -r -b build/Vocola ~/voice/NatLink/trunk/Vocola  | more

