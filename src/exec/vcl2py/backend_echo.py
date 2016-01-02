from vcl2py.ast import *


def output(out_file, statements, file_empty,
           _Should_emit_dictation_support,
           _Module_name,
           _Definitions,
           _Extension_functions,
           params):
    print unparse_statements(statements)
