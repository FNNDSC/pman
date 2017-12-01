#!/usr/bin/env python3

# Single entry point / dispatcher for simplified running of 'pman'

import  os
from    argparse            import RawTextHelpFormatter
from    argparse            import ArgumentParser

str_desc = """

 NAME

    docker-entrypoint.py

 SYNOPSIS

    docker-entrypoint.py    [optional cmd args for pman]


 DESCRIPTION

    'docker-entrypoint.py' is the main entrypoint for running the pman container.

"""


def pman_do(args, unknown):

    str_otherArgs   = ' '.join(unknown)

    str_CMD = "/usr/local/bin/pman %s" % (str_otherArgs)
    # str_CMD = "/usr/local/pman/bin/pman %s" % (str_otherArgs)
    return str_CMD

parser  = ArgumentParser(description = str_desc, formatter_class = RawTextHelpFormatter)
parser.add_argument(
    '--msg',
    action  = 'store',
    dest    = 'msg',
    default = '',
    help    = 'JSON msg payload'
)

args, unknown   = parser.parse_known_args()

if __name__ == '__main__':
    try:
        fname   = 'pman_do(args, unknown)'
        str_cmd = eval(fname)
        print(str_cmd)
        os.system(str_cmd)
    except:
        print("Misunderstood container app... exiting.")