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
        try:
            str_serverPort  = os.environ['PMAN_PORT_5010_TCP_ADDR']
        except:
            str_serverPort  = "172.17.0.2"
        str_http    = '--http %s:5010/api/v1/cmd/' % str_serverPort

    return str_http

def pman_do(args, unknown):
    str_CMD = "/usr/local/bin/pman --raw 1 --http --port 5010 --listeners 12"
    return str_CMD

def pfioh_do(args, unknown):
    str_CMD = "/usr/local/bin/phfioh --forever"
    return str_CMD

def purl_do(args, unknown):

    str_http        = http_construct(args, unknown)
    str_otherArgs   = ' '.join(unknown)

    str_CMD = "/usr/local/bin/purl --verb POST --raw  %s --jsonwrapper 'payload' --msg '%s' %s" % (str_http, args.msg, str_otherArgs)
    return str_CMD


parser  = argparse.ArgumentParser(description = str_desc)

parser.add_argument(
    'app',
    nargs   = '?',
    default = 'pman'
)

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
        fname   = '%s_do(args, unknown)' % args.app
        str_cmd = eval(fname)
        print(str_cmd)
        os.system(str_cmd)
    except:
        print("Misunderstood container app... exiting.")