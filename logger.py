import os
import io

import datetime


def write_log(msg, console=False, raiseexception=False, nlcr=True):
    if nlcr:
        msg += '\n'
    logfile.write(msg)
    logfile.flush()
    if console:
        print(msg)
    if raiseexception:
        raise Exception(msg)


dt = datetime.datetime.now()
log_filename = 'log_'+dt.strftime("%d-%m-%Y_%H-%M-%S")+'.txt'
log_filename = os.path.join(os.getcwd(), 'logs',log_filename)


if os.path.exists(log_filename):
    logfile = io.open(log_filename, mode='a', encoding='utf-8')
else:
    logfile = io.open(log_filename, mode='w', encoding='utf-8')

# logfile.close()
