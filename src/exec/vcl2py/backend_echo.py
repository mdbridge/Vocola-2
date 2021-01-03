from __future__ import print_function

from vcl2py.ast import *


def output(out_file, module_name, statements, definitions,
           file_empty, should_emit_dictation_support,
           extension_functions, params):
    print(unparse_statements(statements))
