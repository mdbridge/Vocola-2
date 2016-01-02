def set_log(target):
    global LOG
    LOG = target


def print_log(message, no_newline=False):
    if no_newline:
        print >>LOG, message,
    else:
        print >>LOG, message


def set_error_prologue(message):
    global Error_prologue
    Error_prologue = message

def log_error(message, location="", no_newline=False):
    global Error_prologue
    if Error_prologue:
        print_log(Error_prologue)
        Error_prologue = None
    print_log("  Error" + location + ":  " + message, no_newline)


def close_log():
    global LOG
    LOG.close()
    LOG = None
