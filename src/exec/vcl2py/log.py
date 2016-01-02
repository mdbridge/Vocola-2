def set_log(target):
    global LOG, Error_count
    LOG = target
    Error_count = 0


def print_log(message, no_newline=False):
    if no_newline:
        print >>LOG, message,
    else:
        print >>LOG, message


def set_error_prologue(message):
    global Error_prologue, Error_count
    Error_prologue = message
    Error_count    = 0

def log_error(message, location="", no_newline=False):
    global Error_prologue, Error_count
    if Error_prologue:
        print_log(Error_prologue)
        Error_prologue = None
    print_log("  Error" + location + ":  " + message, no_newline)
    Error_count += 1

def log_warn(message, location="", no_newline=False):
    global Error_prologue
    if Error_prologue:
        print_log(Error_prologue)
        Error_prologue = None
    print_log("  Warning" + location + ":  " + message, no_newline)

def logged_errors():
    return Error_count


def close_log():
    global LOG
    LOG.close()
    LOG = None
