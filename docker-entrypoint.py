#!/usr/bin/env python3

# Single entry point / dispatcher for simplified running of
#
## pman
## pfioh
## purl
#

import  argparse
import  os

str_desc = """

 NAME

    docker-entrypoint.py

 SYNOPSIS

    docker-entrypoint.py    pman || pfioh || purl
                            [optional cmd args for each]


 DESCRIPTION

    'docker-entrypoint.py' is the main entrypoint for running one of three applications
    contained within the fnndsc/pman docker container.

    Two of these, 'pman' and 'pfioh' are services, while the third 'purl' is a CLI app to
    communicate with these services.

"""

def http_construct(args, unknown):
    """
    Construct the --http <arg> from the args/unknown space -- relevant only for 'purl'.

    :param args:
    :param unknown:
    :return:
    """

    str_http    = ''
    b_httpSpecd = False

    if '--http' in unknown:
        try:
            str_httpArg = unknown[unknown.index('--http')+1]
            unknown.remove('--http')
            unknown.remove(str_httpArg)
        except:
            str_httpArg = ""
        str_http    = '--http %s' % str_httpArg
        b_httpSpecd = True

    if not b_httpSpecd:
        str_serverIP  = "172.17.0.2"
        str_serverPort  = '5010'
        try:
            if args.b_pman:
                str_serverIP    = os.environ['PMAN_PORT_5010_TCP_ADDR']
                str_serverPort  = os.environ['PMAN_PORT_5010_TCP_PORT']
            if args.b_pfioh:
                str_serverIP    = os.environ['PFIOH_PORT_5055_TCP_ADDR']
                str_serverPort  = os.environ['PFIOH_PORT_5055_TCP_PORT']
        except:
            pass
        str_http    = '--http %s:%s/api/v1/cmd/' % (str_serverIP, str_serverPort)

    return str_http

def pman_do(args, unknown):

    str_otherArgs   = ' '.join(unknown)

    str_CMD = "/usr/local/bin/pman %s" % (str_otherArgs)
    return str_CMD

def pfioh_do(args, unknown):

    str_otherArgs   = ' '.join(unknown)

    str_CMD = "/usr/local/bin/pfioh %s" % (str_otherArgs)
    return str_CMD

def purl_do(args, unknown):

    str_http        = http_construct(args, unknown)
    str_otherArgs   = ' '.join(unknown)

    str_raw = ''
    if args.b_raw: str_raw = "--raw"

    str_CMD = "/usr/local/bin/purl --verb %s %s %s --jsonwrapper '%s' --msg '%s' %s" % (args.verb, str_raw, str_http, args.jsonwrapper, args.msg, str_otherArgs)
    return str_CMD

def bash_do(args, unknown):

    str_http        = http_construct(args, unknown)
    str_otherArgs   = ' '.join(unknown)

    str_CMD = "/bin/bash"
    return str_CMD


parser  = argparse.ArgumentParser(description = str_desc)

parser.add_argument(
    'app',
    nargs   = '?',
    default = 'pman'
)
parser.add_argument(
    '--pman',
    action  = 'store_true',
    dest    = 'b_pman',
    default = False,
    help    = 'if specified, indicates transmission to a linked <pman> container.',
)
parser.add_argument(
    '--pfioh',
    action  = 'store_true',
    dest    = 'b_pfioh',
    default = False,
    help    = 'if specified, indicates transmission to a linked <pfioh> container.',
)
parser.add_argument(
    '--msg',
    action  = 'store',
    dest    = 'msg',
    default = '',
    help    = 'JSON msg payload'
)

# Pattern of minimum required purl args
parser.add_argument(
    '--verb',
    action  = 'store',
    dest    = 'verb',
    default = 'POST',
    help    = 'REST verb.'
)
parser.add_argument(
    '--jsonwrapper',
    action  = 'store',
    dest    = 'jsonwrapper',
    default = '',
    help    = 'wrap msg in optional field'
)
parser.add_argument(
    '--raw',
    help    = 'if specified, do not wrap return data from remote call in json field',
    dest    = 'b_raw',
    action  = 'store_true',
    default = False
)


args, unknown   = parser.parse_known_args()

if __name__ == '__main__':
    try:
        fname   = '%s_do(args, unknown)' % args.app
        str_cmd = eval(fname)
        print(str_cmd)
        os.system(str_cmd)
    except:
        print("Misunderstood container app... exiting.")