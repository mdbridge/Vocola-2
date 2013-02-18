# _vocola_main.py - NatLink support for Vocola
# -*- coding: latin-1 -*-
#
# Contains:
#    - "Built-in" voice commands
#    - Autoloading of changed command files
#
#
# Copyright (c) 2002-2012 by Rick Mohr.
#
# Portions Copyright (c) 2012-2013 by Hewlett-Packard Development Company, L.P.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import string
import sys
import os               # access to file information
import os.path          # to parse filenames
import time             # print time in messages
from stat import *      # file statistics
import re
import natlink
from natlinkutils import *


language = 'enx'
try:
    # The following files are only present if Scott's installer is being used:
    import RegistryDict
    import win32con
    installer = True
except ImportError:
    installer = False

    
# The Vocola translator is a perl program. By default we use the precompiled
# executable vcl2py.exe, which doesn't require installing perl.
# To instead use perl and vcl2py.pl, set the following variable to 1:
usePerl = 0

# C module "simpscrp" defines Exec(), which runs a program in a minimized
# window and waits for completion. Since such modules need to be compiled
# separately for each python version we need this careful import:

NatLinkFolder = os.path.split(
    sys.modules['natlinkmain'].__dict__['__file__'])[0]

NatLinkFolder = re.sub(r'\core$', "", NatLinkFolder)

pydFolder = os.path.normpath(os.path.join(NatLinkFolder, '..', 'Vocola', 'exec', sys.version[0:3]))
sys.path.append(pydFolder)
ExecFolder = os.path.normpath(os.path.join(NatLinkFolder, '..', 'Vocola','exec'))
sys.path.append(ExecFolder)
ExtensionsFolder = os.path.normpath(os.path.join(NatLinkFolder, '..', 'Vocola', 'extensions'))
sys.path.append(ExtensionsFolder)
NatLinkFolder = os.path.abspath(NatLinkFolder)


# 
# Run program with path executable and arguments arguments.  Waits for
# the program to finish.  Runs the program in a hidden window.
# 
def hidden_call(executable, arguments):
    args = [executable] + arguments
    try:
        import simpscrp2
        args = ['"' + str(x) + '"' for x in args]
        call = ' '.join(args)
        simpscrp.Exec(call, 1)
    except ImportError:
        try:
            import subprocess2
            si             = subprocess.STARTUPINFO()
            si.dwFlags     = subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            print repr(args)
            return subprocess.call(args, startupinfo=si)
        except ImportError:
            pid = os.spawnv(os.P_NOWAIT, executable, args)
            pid, exit_code = os.waitpid(pid, 0)
            exit_code = exit_code >> 8
            return exit_code


class ThisGrammar(GrammarBase):

    gramSpec = """
        <NatLinkWindow>     exported = [Show] (NatLink|Vocola) Window;
        <edit>              exported = Edit [Voice] Commands;
        <editGlobal>        exported = Edit Global [Voice] Commands;
        <editMachine>       exported = Edit Machine [Voice] Commands;
        <editGlobalMachine> exported = Edit Global Machine [Voice] Commands;
        <loadAll>           exported = Load All [Voice] Commands;
        <loadCurrent>       exported = Load [Voice] Commands;
        <loadGlobal>        exported = Load Global [Voice] Commands;
        <loadExtensions>    exported = Load [Voice] Extensions;
        <discardOld>        exported = Discard Old [Voice] Commands;
    """

    if language == 'nld':
        gramSpec = """
<NatLinkWindow>     exported = Toon (NatLink|Vocola) venster;
<edit>              exported = (Eddit|Bewerk|Sjoo|Toon) [stem|vojs] (Commandoos|Commands);
<editGlobal>        exported = (Eddit|Bewerk|Sjoo|Toon) (Global|globale) [stem|vojs] (Commandoos|Commands);
<editMachine>       exported = (Eddit|Bewerk|Sjoo|Toon) Machine [stem|vojs] (Commandoos|Commands);
<editGlobalMachine> exported = (Eddit|Bewerk|Sjoo|Toon) (Global|globale) Machine [stem|vojs] (Commandoos|Commands);
<loadAll>           exported = (Laad|Lood) alle [stem|vojs] (Commandoos|Commands);
<loadCurrent>       exported = (Laad|Lood) [stem|vojs] (Commandoos|Commands);
<loadGlobal>        exported = (Laad|Lood) globale [stem|vojs] (Commandoos|Commands);
<loadExtensions>    exported = Laad [stem] extensies;
<discardOld>        exported = (Discard|Verwijder) (oude|oold) [stem|vojs] (Commandoos|Commands);
    """
    elif language == 'fra':
        gramSpec = """
<NatLinkWindow>     exported = [Afficher] Fenetre (NatLink|Vocola);
<edit>              exported = Editer Commandes [Vocales];
<editGlobal>        exported = Editer Commandes [Vocales] Globales;
<editMachine>       exported = Editer Commandes [Vocales] Machine;
<editGlobalMachine> exported = Editer Commandes [Vocales] Globales Machine;
<loadAll>           exported = Charger Toutes Les Commandes [Vocales];
<loadCurrent>       exported = Charger Commandes [Vocales];
<loadGlobal>        exported = Charger Commandes [Vocales] Globales;
<loadExtensions>    exported = Charger Extensions [Vocales];
<discardOld>        exported = Effacer Commandes [Vocales] Precedentes;
    """
    elif language == 'deu':
        gramSpec = """
<NatLinkWindow>     exported = [Zeige] (NatLink|Vocola) Fenster;
<edit>              exported = Bearbeite [Sprach] Befehle;
<editGlobal>        exported = Bearbeite globale [Sprach] Befehle;
<editMachine>       exported = Bearbeite Maschinen [Sprach] Befehle;
<editGlobalMachine> exported = Bearbeite globale Maschinen [Sprach] Befehle;
<loadAll>           exported = Lade alle [Sprach] Befehle;
<loadCurrent>       exported = Lade [Sprach] Befehle;
<loadGlobal>        exported = Lade globale [Sprach] Befehle;
<loadExtensions>    exported = Lade [Sprach] Extensions;
<discardOld>        exported = Verwerfe alte [Sprach] Befehle;
    """   
    elif language == 'ita':
        gramSpec = """
<NatLinkWindow>     exported = [Mostra] Finestra Di (NatLink|Vocola);
<edit>              exported = Modifica Comandi [Vocali];
<editGlobal>        exported = Modifica Comandi [Vocali] Globali;
<editMachine>       exported = Modifica Comandi [Vocali] [del] Computer;
<editGlobalMachine> exported = Modifica Comandi [Vocali] Globali [del] Computer;
<loadAll>           exported = Carica Tutti I Comandi [Vocali];
<loadCurrent>       exported = Carica I Comandi [Vocali];
<loadGlobal>        exported = Carica Comandi [Vocali] Gliobali;
<loadExtensions>    exported = Carica Estensioni [Vocali];
<discardOld>        exported = Annulla Vecchi Comandi [Vocali];
    """
    elif language == 'esp':
        gramSpec = """
<NatLinkWindow>     exported = [Mostrar] Ventana de (NatLink|Vocola) ;
<edit>              exported = (Modificar|Editar) Comandos [de voz];
<editGlobal>        exported = (Modificar|Editar) Comandos [de voz] Globales ;
<editMachine>       exported = (Modificar|Editar) Comandos [de voz] de (este ordenador|la Computadora);
<editGlobalMachine> exported = (Modificar|Editar) Comandos [de voz] Globales de (este ordenador|la Computadora);
<loadAll>           exported = (Recargar|Cargar) Todos Los Comandos [de voz];
<loadCurrent>       exported = (Recargar|Cargar) Comandos [de voz];
<loadGlobal>        exported = (Recargar|Cargar) Comandos [de voz] Globales;
<loadExtensions>    exported = (Recargar|Cargar) Extensiones [de voz];
<discardOld>        exported = Descartar Comandos [de voz] Viejos;
    """
    elif language != 'enx':
        print >> sys.stderr,  """\n\n
Vocola Warning: no language "%s" translations for the built-in Vocola
commands (e.g., commands to load voice commands) are currently
available; consider helping translate them -- inquire on
http://www.speechcomputing.com.  For now the English versions, like "Edit
Commands" and "Edit Global Commands" are activated.
""" % language


    def initialize(self):
        # remove previous Vocola/Python compilation output as it may be out
        # of date (e.g., new compiler, source file deleted, partially
        # written due to crash, new machine name, etc.):
        self.purgeOutput()

        self.compilerError   = 0  # has a compiler error occurred?
        self.setNames()

        self.load_extensions()
        self.loadAllFiles([])

        self.load(self.gramSpec)
        self.activateAll()
        # Don't set callback just yet or it will be clobbered
        self.needToSetCallback = 1
                    
                    
    def gotBegin(self,moduleInfo):
        self.currentModule = moduleInfo
        if self.needToSetCallback:
            # Replace NatLink's "begin" callback function with ours (see below)
            natlink.setBeginCallback(vocolaBeginCallback)
            self.needToSetCallback = 0

                                      
    # Set member variables -- important folders and computer name
    def setNames(self):
        self.VocolaFolder = os.path.normpath(os.path.join(NatLinkFolder, 
                                                          '..', 'Vocola'))
        if os.environ.has_key('COMPUTERNAME'):
            self.machine = string.lower(os.environ['COMPUTERNAME'])
        else: self.machine = 'local'

        self.commandFolder = None
        if installer:
            r = RegistryDict.RegistryDict(win32con.HKEY_CURRENT_USER,
                                          "Software\NatLink")             
            if r:                                                         
                userCommandFolder = r["VocolaUserDirectory"]              
                if os.path.isdir(userCommandFolder):                      
                    self.commandFolder = userCommandFolder
        if not self.commandFolder:
            systemCommandFolder = os.path.join(self.VocolaFolder, 'Commands')
            if os.path.isdir(systemCommandFolder):
                self.commandFolder = systemCommandFolder
        if not self.commandFolder:
            print >> sys.stderr, "Warning: no Vocola command folder found!"


    # Get app name by stripping folder and extension from currentModule name
    def getCurrentApplicationName(self):
        return string.lower(os.path.splitext(os.path.split(self.currentModule[0]) [1]) [0])

    def getSourceFilename(self, output_filename):
        m = re.match("^(.*)_vcl.pyc?$", output_filename)
        if not m: return None                    # Not a Vocola file
        name = m.group(1)
        if not self.commandFolder: return None

        marker = "e_s_c_a_p_e_d__"
        m = re.match("^(.*)" + marker + "(.*)$", name)  # rightmost marker!
        if m:
            name = m.group(1)
            tail = m.group(2)
            tail = re.sub("__a_t__", "@", tail)
            tail = re.sub("___", "_", tail)
            name += tail

        name = re.sub("_@", "@", name)
        return self.commandFolder + "\\" + name + ".vcl"

    def deleteOrphanFiles(self):
        print "checking for orphans..."
        for f in os.listdir(NatLinkFolder):
            if not re.search("_vcl.pyc?$", f): continue

            s = self.getSourceFilename(f)
            if s:
                if vocolaGetModTime(s)>0: continue

            f = os.path.join(NatLinkFolder, f)
            print "Deleting: " + f
            os.remove(f)

### Miscellaneous commands

    # "Show NatLink Window" -- print to output window so it appears
    def gotResults_NatLinkWindow(self, words, fullResults):
        print "This is the NatLink/Vocola output window"

    # "Load Extensions" -- scan for new/changed extensions:
    def gotResults_loadExtensions(self, words, fullResults):
        self.load_extensions(True)
        for module in sys.modules.keys():
            if module.startswith("vocola_ext_"):
                del sys.modules[module]

    def load_extensions(self, verbose=False):
        #if sys.modules.has_key("scan_extensions"):
        #    del sys.modules["scan_extensions"]
        import scan_extensions
        arguments = ["scan_extensions", ExtensionsFolder]
        if verbose:
            arguments.insert(1, "-v")
        scan_extensions.main(arguments)

### Loading Vocola Commands

    # "Load All Commands" -- translate all Vocola files
    def gotResults_loadAll(self, words, fullResults):
        self.loadAllFiles(['-f'])

    # "Load Commands" -- translate Vocola files for current application
    def gotResults_loadCurrent(self, words, fullResults):
        self.loadSpecificFiles(self.getCurrentApplicationName())

    # "Load Global Commands" -- translate global Vocola files
    def gotResults_loadGlobal(self, words, fullResults):
        self.loadSpecificFiles('')

    # "Discard Old [Voice] Commands" -- purge output then translate all files
    def gotResults_discardOld(self, words, fullResults):
        self.purgeOutput()
        self.loadAllFiles(['-f'])

    # Unload all commands, including those of files no longer existing
    def purgeOutput(self):
        pattern = re.compile("_vcl\d*\.pyc?$")
        [os.remove(os.path.join(NatLinkFolder,f)) for f in os.listdir(NatLinkFolder) if pattern.search(f)]

    # Load all command files
    def loadAllFiles(self, options):
        if self.commandFolder:
            options = ["-suffix", "_vcl" ] + options
            self.runVocolaTranslator(self.commandFolder, options)

    # Load command files for specific application
    def loadSpecificFiles(self, module):
        special = re.compile(r'([][()^$.+*?{\\])')
        pattern = "^" + special.sub(r'\\\1', module)
        pattern += "(_[^@]*)?(@" + special.sub(r'\\\1', self.machine)
        pattern += ")?\.vcl$"
        p = re.compile(pattern)

        targets = []
        if self.commandFolder:
            targets += [os.path.join(self.commandFolder,f)
                        for f in os.listdir(self.commandFolder) if p.search(f)]
        options = ["-suffix", "_vcl" ]
        if len(targets) > 0:
            for target in targets:
                self.loadFile(target, options)
        else:
            print >> sys.stderr
            if module == "":
                print >> sys.stderr, "Found no Vocola global command files (for machine '" + self.machine + "')"
            else:
                print >> sys.stderr, "Found no Vocola command files for application '" + module + "' (for machine '" + self.machine + "')"

    # Load a specific command file, returning false if not present
    def loadFile(self, file, options):
        try:
            os.stat(file)
            self.runVocolaTranslator(file, options + ['-f'])
            return 1
        except OSError:
            return 0   # file not found

    # Run Vocola translator, converting command files from "inputFileOrFolder"
    # and writing output to NatLink/MacroSystem
    def runVocolaTranslator(self, inputFileOrFolder, options):
        if usePerl:
            executable = "perl"
            arguments  = [self.VocolaFolder + r'\exec\vcl2py.pl']
        else:
            executable = self.VocolaFolder + r'\exec\vcl2py.exe'
            arguments  = []
        #executable = r'c:\Python26\Python.exe'
        #arguments  = [self.VocolaFolder + r'\exec\vcl2py.py']

        arguments += ['-extensions', ExtensionsFolder + r'\extensions.csv']
        if language == "enx":
            arguments += ['-numbers', 
                          'zero,one,two,three,four,five,six,seven,eight,nine']

        arguments += options.strip().split(" ")

        arguments += [inputFileOrFolder, NatLinkFolder]
        hidden_call(executable, arguments)

        logName = self.commandFolder + r'\vcl2py_log.txt'
        if os.path.isfile(logName):
            try:
                log = open(logName, 'r')
                self.compilerError = 1
                print  >> sys.stderr, log.read()
                log.close()
                os.remove(logName)
            except IOError:  # no log file means no Vocola errors
                pass

### Editing Vocola Command Files

    # "Edit Commands" -- open command file for current application
    def gotResults_edit(self, words, fullResults):
        app = self.getCurrentApplicationName()
        file = app + '.vcl'
        comment = 'Voice commands for ' + app
        self.openCommandFile(file, comment)

    # "Edit Machine Commands" -- open command file for current app & machine
    def gotResults_editMachine(self, words, fullResults):
        app = self.getCurrentApplicationName()
        file = app + '@' + self.machine + '.vcl'
        comment = 'Voice commands for ' + app + ' on ' + self.machine
        self.openCommandFile(file, comment)

    # "Edit Global Commands" -- open global command file
    def gotResults_editGlobal(self, words, fullResults):
        file = '_vocola.vcl'
        comment = 'Global voice commands'
        self.openCommandFile(file, comment)

    # "Edit Global Machine Commands" -- open global command file for machine
    def gotResults_editGlobalMachine(self, words, fullResults):
        file = '_vocola@' + self.machine + '.vcl'
        comment = 'Global voice commands on ' + self.machine
        self.openCommandFile(file, comment)

    
    def FindExistingCommandFile(self, file):
        if self.commandFolder:
            f = self.commandFolder + '\\' + file
            if os.path.isfile(f): return f

        return ""
    
    # Open a Vocola command file (using the application associated with ".vcl")
    def openCommandFile(self, file, comment):
        if not self.commandFolder:
            print >> sys.stderr, "Error: Unable to create command file because no Vocola command folder found."
            return

        path = self.FindExistingCommandFile(file)
        if not path:
            path = self.commandFolder + '\\' + file
        
            new = open(path, 'w')
            new.write('# ' + comment + '\n\n')
            new.close()

        #
        # NatLink/DNS bug causes os.startfile or wpi32api.ShellExecute
        # to crash DNS if allResults is on in *any* grammer (e.g., Unimacro)
        #
        # Accordingly, use AppBringUp instead:
        #

        #try:
        #    os.startfile(path)
        #except WindowsError, e: 
        #    print
        #    print "Unable to open voice command file with associated editor: " + str(e)
        #    print "Trying to open it with notepad instead."
        #    prog = os.path.join(os.getenv('WINDIR'), 'notepad.exe')
        #    os.spawnv(os.P_NOWAIT, prog, [prog, path])
        natlink.execScript("AppBringUp \"" + path + "\", \"" + path + "\"")



# Returns the modification time of a file or 0 if the file does not exist
def vocolaGetModTime(file):
    try: return os.stat(file)[ST_MTIME]
    except OSError: return 0        # file not found

# Returns the newest modified time of any Vocola command folder file or
# 0 if none:
def getLastVocolaFileModTime():
    last = 0
    if thisGrammar.commandFolder:
        last = max([last] +
                   [vocolaGetModTime(os.path.join(thisGrammar.commandFolder,f))
                    for f in os.listdir(thisGrammar.commandFolder)])
    return last


# When speech is heard this function will be called before any others.
#   - Compile any changed Vocola command files
##   - Remove any vocola output files without corresponding source files
#   - Make sure NatLink sees any new output files
#   - Invoke the standard NatLink callback

from natlinkmain import beginCallback
from natlinkmain import findAndLoadFiles
from natlinkmain import loadModSpecific

lastNatLinkModTime    = 0
lastCommandFolderTime = 0
lastVocolaFileTime    = 0

def vocolaBeginCallback(moduleInfo):
    global lastNatLinkModTime, lastCommandFolderTime, lastVocolaFileTime

    current = getLastVocolaFileModTime()
    if current > lastVocolaFileTime:
        thisGrammar.compilerError = 0	   
        thisGrammar.loadAllFiles([])
	if not thisGrammar.compilerError:
            lastVocolaFileTime =  current

#    source_changed = 0
#    if thisGrammar.commandFolder:
#        if vocolaGetModTime(thisGrammar.commandFolder) > lastCommandFolderTime:
#            lastCommandFolderTime = vocolaGetModTime(thisGrammar.commandFolder)
#            source_changed = 1
#    if source_changed:
#        thisGrammar.deleteOrphanFiles()

    if getCallbackDepth() < 2:
        current = vocolaGetModTime(NatLinkFolder)
        if current > lastNatLinkModTime:
            lastNatLinkModTime = current
            # make sure NatLink sees any new .py files:
            findAndLoadFiles()
            loadModSpecific(moduleInfo)

    beginCallback(moduleInfo)



thisGrammar = ThisGrammar()
thisGrammar.initialize()


def unload():
    global thisGrammar
    natlink.setBeginCallback(beginCallback)
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None
