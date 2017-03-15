#!/usr/bin/env python3.5

'''

purl - python curl module

'''


# import  threading
import  argparse
import  time
import  sys
import  json
import  pprint
import  socket
import  pycurl
import  io
import  os
import  urllib
import  datetime
import  codecs

import  pudb

# pman local dependencies
from    ._colors         import  Colors
from    .pfioh           import  *
from    .message         import  Message

# A global variable that tracks if script was started from CLI or programmatically
b_startFromCLI  = False

class Purl():

    ''' Represents an example client. '''

    def qprint(self, msg, **kwargs):

        str_comms  = "status"
        for k,v in kwargs.items():
            if k == 'comms':    str_comms  = v

        if self.b_useDebug:
            write   = self.debug
        else:
            write   = print

        # pudb.set_trace()

        if not self.b_quiet:
            if not self.b_useDebug:
                if str_comms == 'status':   write(Colors.PURPLE,    end="")
                if str_comms == 'error':    write(Colors.RED,       end="")
                if str_comms == "tx":       write(Colors.YELLOW + "---->")
                if str_comms == "rx":       write(Colors.GREEN  + "<----")
                write('%s' % datetime.datetime.now() + " ",       end="")
            write(' | ' + msg)
            if not self.b_useDebug:
                if str_comms == "tx":       write(Colors.YELLOW + "---->")
                if str_comms == "rx":       write(Colors.GREEN  + "<----")
                write(Colors.NO_COLOUR, end="")

    def col2_print(self, str_left, str_right):
        print(Colors.WHITE +
              ('%*s' % (self.LC, str_left)), end='')
        print(Colors.LIGHT_BLUE +
              ('%*s' % (self.RC, str_right)) + Colors.NO_COLOUR)

    def __init__(self, **kwargs):
        # threading.Thread.__init__(self)

        self._log                   = Message()
        self._log._b_syslog         = True
        self.__name                 = "Purl"
        self.b_useDebug             = False
        self._startFromCLI          = False

        str_debugDir                = '%s/tmp' % os.environ['HOME']
        if not os.path.exists(str_debugDir):
            os.makedirs(str_debugDir)
        self.str_debugFile          = '%s/debug-charm.log' % str_debugDir

        self.str_http           = ""
        self.str_ip             = ""
        self.str_port           = ""
        self.str_URL            = ""
        self.str_verb           = ""
        self.str_msg            = ""
        self.str_auth           = ""
        self.d_msg              = {}
        self.str_protocol       = "http"
        self.pp                 = pprint.PrettyPrinter(indent=4)
        self.b_man              = False
        self.str_man            = ''
        self.b_quiet            = False
        self.b_raw              = False
        self.b_oneShot          = False
        self.auth               = ''
        self.str_jsonwrapper    = ''
        self.str_contentType    = ''
        self.b_useDebug         = False
        self.str_debugFile      = ''

        self.LC                 = 40
        self.RC                 = 40

        for key,val in kwargs.items():
            if key == 'msg':
                self.str_msg                = val
                try:
                    self.d_msg              = json.loads(self.str_msg)
                except:
                    pass
            if key == 'http':           self.httpStr_parse( http    = val)
            if key == 'auth':           self.str_auth               = val
            if key == 'verb':           self.str_verb               = val
            if key == 'contentType':    self.str_contentType        = val
            if key == 'ip':             self.str_ip                 = val
            if key == 'port':           self.str_port               = val
            if key == 'b_quiet':        self.b_quiet                = val
            if key == 'b_raw':          self.b_raw                  = val
            if key == 'b_oneShot':      self.b_oneShot              = val
            if key == 'man':            self.str_man                = val
            if key == 'jsonwrapper':    self.str_jsonwrapper        = val
            if key == 'useDebug':       self.b_useDebug             = val
            if key == 'debugFile':      self.str_debugFile          = val
            if key == 'startFromCLI':   self._startFromCLI          = val

        if self.b_useDebug:
            self.debug                  = Message(logTo = self.str_debugFile)
            self.debug._b_syslog        = True
            self.debug._b_flushNewLine  = True

        if len(self.str_man):
            print(self.man(on = self.str_man))
            sys.exit(0)

        if not self.b_quiet:

            print(Colors.LIGHT_GREEN)
            print("""
            \t\t\t\t+--------------------+
            \t\t\t\t|  Welcome to purl!  |
            \t\t\t\t+--------------------+
            """)
            print(Colors.CYAN + """
            'purl' is a wrapper about pycurl, originally designed for the ChRIS/pman interface.
            It also functions as a reasonable CLI curl client, too!

            Type 'purl --man commands' for more help.""")
            if self.b_useDebug:
                print("""
            Debugging output is directed to the file '%s'.
                """ % (self.str_debugFile))
            else:
                print("""
            Debugging output will appear in *this* console.
                """)

            self.qprint('purl: Start from CLI = %d' % self._startFromCLI)
            self.qprint('purl: Command line args = %s' % sys.argv)
            if self._startFromCLI and (sys.argv) == 1: sys.exit(1)

            self.col2_print("Will transmit to",     '%s://%s:%s' % (self.str_protocol, self.str_ip, self.str_port))


    def man(self, **kwargs):
        """
        Print some man for each understood command
        """

        str_man     = 'commands'
        str_amount  = 'full'

        for k, v in kwargs.items():
            if k == 'on':       str_man     = v
            if k == 'amount':   str_amount  = v

        if str_man == 'commands':
            str_commands = """
            This script/module provides CURL-based GET/PUT/POST communication over http
            to a remote REST-like service: """ + Colors.GREEN + """

                 ./purl.py [--auth <username:passwd>] [--verb <GET/POST>]   \\
                            --http <IP>[:<port>]</some/path/>

            """ + Colors.WHITE + """
            Where --auth is an optional authorization to pass to the REST API,
            --verb denotes the REST verb to use and --http specifies the REST URL.

            Additionally, a 'message' described in JSON syntax can be pushed to the
            remote service, in the following syntax: """ + Colors.GREEN + """

                 ./purl.py [--auth <username:passwd>] [--verb <GET/POST>]   \\
                            --http <IP>[:<port>]</some/path/>               \\
                           [--msg <JSON-formatted-string>]

            """ + Colors.WHITE + """
            In the case of the 'pman' system this --msg flag has very specific
            contextual syntax, for example:
            """ + Colors.GREEN + """
                 ./purl.py --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                                '{  "action": "run",
                                    "meta": {
                                        "cmd":      "cal 7 1970",
                                        "auid":     "rudolphpienaar",
                                        "jid":      "<jid>-1",
                                        "threaded": true
                                    }
                                }'


            """ % (self.str_ip, self.str_port) + Colors.CYAN + """

            The following specific action directives are directly handled by script:
            """ + "\n" + \
            self.man_pushPath(          description =   "short")      + "\n" + \
            self.man_pullPath(          description =   "short")      + "\n" + \
            Colors.YELLOW + \
            """
            To get detailed help on any of the above commands, type
            """ + Colors.LIGHT_CYAN + \
            """
                ./purl.py --man <command>
            """

            return str_commands

        if str_man  == 'pushPath':  return self.man_pushPath(       description  =   str_amount)
        if str_man  == 'pullPath':  return self.man_pullPath(       description  =   str_amount)

    def man_pushPath(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "pushPath" + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "push a filesystem path over HTTP." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This pushes a file over HTTP. The 'meta' dictionary
                can be used to specify content specific information
                and other information.

                Note that the "file" server is typically *not* on the
                same port as the `pman` process. Usually a prior call
                must be made to `pman` to start a one-shot listener
                on a given port. This port then accepts the file transfer
                from the 'pushPath' method.
                
                The "meta" dictionary consists of several nested 
                dictionaries. In particular, the "remote/path"
                field can be used to suggest a location on the remote
                filesystem to save the transmitted data. Successful
                saving to this path depends on whether or not the
                remote server process actually has permission to
                write in that location.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                purl --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                    '{  "action": "pushPath",
                        "meta":
                            {
                                "local":
                                    {
                                        "path":         "/path/on/client"
                                    },
                                "remote":
                                    {
                                        "path":         "/path/on/server"
                                    },
                                "transport":
                                    {
                                        "mechanism":    "compress",
                                        "compress": {
                                            "encoding": "base64",
                                            "archive":  "zip",
                                            "unpack":   true,
                                            "cleanup":  true
                                        }
                                    }
                            }
                    }'
                """ % (self.str_ip, self.str_port) + Colors.NO_COLOUR  + """
                """ + Colors.YELLOW + """ALTERNATE -- using copy/symlink:
                """ + Colors.LIGHT_GREEN + """
                purl --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                    '{  "action": "pushPath",
                        "meta":
                            {
                                "local":
                                    {
                                        "path":         "/path/on/client"
                                    },
                                "remote":
                                    {
                                        "path":         "/path/on/server"
                                    },
                                "transport":
                                    {
                                        "mechanism":    "copy",
                                        "copy": {
                                            "symlink": true
                                        }
                                    }
                            }
                    }'
                """ % (self.str_ip, self.str_port) + Colors.NO_COLOUR

        return str_manTxt

    def man_pullPath(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "pullPath" + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "pull a filesystem path over HTTP." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This pulls data over HTTP from a remote server.
                The 'meta' dictionary can be used to specify content
                specific information and other detail.

                Note that the "file" server is typically *not* on the
                same port as a `pman` process. Usually a prior call
                must be made to `pman` to start a one-shot listener
                on a given port. This port then accepts the file transfer
                from the 'pullPath' method.

                The "meta" dictionary consists of several nested
                dictionaries. In particular, the "remote/path"
                field can be used to specify a location on the remote
                filesystem to pull. Successful retrieve from this path
                depends on whether or not the remote server process actually
                has permission to read in that location.

                """ + Colors.YELLOW + """EXAMPLE -- using zip:
                """ + Colors.LIGHT_GREEN + """
                purl --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                    '{  "action": "pullPath",
                        "meta":
                            {
                                "local":
                                    {
                                        "path":         "/path/on/client"
                                    },
                                "remote":
                                    {
                                        "path":         "/path/on/server"
                                    },
                                "transport":
                                    {
                                        "mechanism":    "compress",
                                        "compress": {
                                            "encoding": "base64",
                                            "archive":  "zip",
                                            "unpack":   true,
                                            "cleanup":  true
                                        }
                                    }
                            }
                    }'
                """ % (self.str_ip, self.str_port) + Colors.NO_COLOUR + """
                """ + Colors.YELLOW + """ALTERNATE -- using copy/symlink:
                """ + Colors.LIGHT_GREEN + """
                purl --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                    '{  "action": "pullPath",
                        "meta":
                            {
                                "local":
                                    {
                                        "path":         "/path/on/client"
                                    },
                                "remote":
                                    {
                                        "path":         "/path/on/server"
                                    },
                                "transport":
                                    {
                                        "mechanism":    "copy",
                                        "copy": {
                                            "symlink": true
                                        }
                                    }
                            }
                    }'
                """ % (self.str_ip, self.str_port) + Colors.NO_COLOUR

        return str_manTxt

    def pull_core(self, **kwargs):
        """
        Just the core of the pycurl logic.
        """

        str_ip              = self.str_ip
        str_port            = self.str_port
        verbose             = 0
        d_msg               = {}

        for k,v in kwargs.items():
            if k == 'ip':       str_ip      = v
            if k == 'port':     str_port    = v
            if k == 'msg':      d_msg       = v
            if k == 'verbose':  verbose     = v

        response            = io.BytesIO()

        str_query   = ''
        if len(d_msg):
            d_meta              = d_msg['meta']
            str_query           = '?%s' % urllib.parse.urlencode(d_msg)

        str_URL = "http://%s:%s%s%s" % (str_ip, str_port, self.str_URL, str_query)

        self.qprint(str_URL,
                    comms  = 'tx')

        c                   = pycurl.Curl()
        c.setopt(c.URL, str_URL)
        if verbose: c.setopt(c.VERBOSE, 1)
        c.setopt(c.FOLLOWLOCATION,  1)
        c.setopt(c.WRITEFUNCTION,   response.write)
        if len(self.str_auth):
            c.setopt(c.USERPWD, self.str_auth)
        self.qprint("Waiting for PULL response...", comms = 'status')
        c.perform()
        c.close()
        try:
            str_response        = response.getvalue().decode()
        except:
            str_response        = response.getvalue()

        self.qprint('Incoming transmission received, length = %s' % "{:,}".format(len(str_response)),
                    comms = 'rx')
        return str_response

    def pullPath_core(self, d_msg, **kwargs):
        """
        Just the core of the pycurl logic.
        """

        str_response = self.pull_core(msg = self.d_msg)

        if len(str_response) < 800:
            # It's possible an error occurred for the response to be so short.
            # Try and json load, and examine for 'status' field.
            b_response      = False
            b_status        = False
            try:
                d_response  = json.loads(str_response)
                b_response  = True
                b_status    = d_response['status']
                str_error   = d_response
            except:
                str_error   = str_response
            if not b_status or 'Network Error' in str_response:
                self.qprint('Some error occurred at remote location:',
                            comms = 'error')
                return {'status':       False,
                        'msg':          'PULL unsuccessful',
                        'response':     str_error,
                        'timestamp':    '%s' % datetime.datetime.now(),
                        'size':         "{:,}".format(len(str_response))}
            else:
                return {'status':       d_response['status'],
                        'msg':          'PULL successful',
                        'response':     d_response,
                        'timestamp':    '%s' % datetime.datetime.now(),
                        'size':         "{:,}".format(len(str_response))}

        self.qprint("Received " + Colors.YELLOW + "{:,}".format(len(str_response)) +
                    Colors.PURPLE + " bytes..." ,
                    comms = 'status')

        return {'status':       True,
                'msg':          'PULL successful',
                'response':     str_response,
                'timestamp':    '%s' % datetime.datetime.now(),
                'size':         "{:,}".format(len(str_response))}

    def pullPath_compress(self, d_msg, **kwargs):
        """

        This pulls a compressed path from a remote host/location.

        """

        # Parse "header" information
        d_meta                  = d_msg['meta']
        d_local                 = d_meta['local']
        str_localPath           = d_local['path']
        d_remote                = d_meta['remote']
        d_transport             = d_meta['transport']
        d_compress              = d_transport['compress']
        d_ret                   = {}
        d_ret['remoteServer']   = {}
        d_ret['localOp']        = {}

        if 'cleanup' in d_compress:
            b_cleanZip      = d_compress['cleanup']

        # Pull the actual data into a dictionary holder
        d_pull                  = self.pullPath_core(d_msg)
        d_ret['remoteServer']   = d_pull

        if not d_pull['status']:
            return {'stdout': json.dumps(d_pull['stdout'])}

        str_localStem       = os.path.split(d_remote['path'])[-1]
        str_fileSuffix      = ""
        if d_compress['archive']     == "zip":       str_fileSuffix   = ".zip"

        str_localFile       = "%s/%s%s" % (d_meta['local']['path'], str_localStem, str_fileSuffix)
        str_response        = d_pull['response']
        d_pull['response']  = '<truncated>'

        if d_compress['encoding'] == 'base64':
            self.qprint("Decoding base64 encoded text stream to %s..." % \
                        str_localFile, comms = 'status')
            d_fio = base64_process(
                action          = 'decode',
                payloadBytes    = str_response,
                saveToFile      = str_localFile
            )
            d_ret['localOp']['decode']   = d_fio
        else:
            self.qprint("Writing byte stream to %s..." % str_localFile,
                        comms = 'status')
            with open(str_localFile, 'wb') as fh:
                fh.write(str_response)
                fh.close()
            d_ret['localOp']['stream']                  = {}
            d_ret['localOp']['stream']['status']        = True
            d_ret['localOp']['stream']['fileWritten']   = str_localFile
            d_ret['localOp']['stream']['timestamp']     = '%s' % datetime.datetime.now()
            d_ret['localOp']['stream']['filesize']      = "{:,}".format(len(str_response))

        if d_compress['archive'] == 'zip':
            self.qprint("Unzipping %s to %s"  % (str_localFile, str_localPath),
                        comms = 'status')
            d_fio = zip_process(
                action          = "unzip",
                payloadFile     = str_localFile,
                path            = str_localPath
            )
            d_ret['localOp']['unzip']       = d_fio
            d_ret['localOp']['unzip']['timestamp']  = '%s' % datetime.datetime.now()
            d_ret['localOp']['unzip']['filesize']   = '%s' % "{:,}".format(os.stat(d_fio['fileProcessed']).st_size)
            d_ret['status']                 = d_fio['status']
            d_ret['msg']                    = d_fio['msg']

        if b_cleanZip and d_ret['status']:
            self.qprint("Removing zip file %s..." % str_localFile,
                        comms = 'status')
            os.remove(str_localFile)

        return d_ret

    def pullPath_copy(self, d_msg, **kwargs):
        """
        Handle the "copy" pull operation
        """

        # Parse "header" information
        d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        str_localPath       = d_local['path']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_copy              = d_transport['copy']

        # Pull the actual data into a dictionary holder
        d_curl                      = {}
        d_curl['remoteServer']      = self.pullPath_core(d_msg)
        d_curl['copy']              = {}
        d_curl['copy']['status']    = d_curl['remoteServer']['status']
        if not d_curl['copy']['status']:
            d_curl['copy']['msg']   = "Copy on remote server failed!"
        else:
            d_curl['copy']['msg']   = "Copy on remote server success!"

        return d_curl

    def path_remoteLocationCheck(self, d_msg, **kwargs):
        """
        This method checks if the "remote" path is valid.
        """

        # Pull the actual data into a dictionary holder
        d_pull = self.pullPath_core(d_msg)
        return d_pull

    def path_localLocationCheck(self, d_msg, **kwargs):
        """
        Check if a path exists on the local filesystem

        :param self:
        :param kwargs:
        :return:
        """
        d_meta              = d_msg['meta']
        d_local             = d_meta['local']

        str_localPath       = d_local['path']

        b_isFile            = os.path.isfile(str_localPath)
        b_isDir             = os.path.isdir(str_localPath)
        b_exists            = os.path.exists(str_localPath)

        d_ret               = {
            'status':  b_exists,
            'isfile':  b_isFile,
            'isdir':   b_isDir
        }

        return {'check':        d_ret,
                'status':       d_ret['status'],
                'timestamp':    '%s' % datetime.datetime.now()}

    def push_core(self, d_msg, **kwargs):
        """

        """

        str_fileToProcess   = ""
        str_encoding        = "none"
        d_ret               = {}
        str_ip              = self.str_ip
        str_port            = self.str_port
        verbose             = 0

        for k,v in kwargs.items():
            if k == 'fileToPush':   str_fileToProcess   = v
            if k == 'encoding':     str_encoding        = v
            if k == 'd_ret':        d_ret               = v
            if k == 'ip':           str_ip              = v
            if k == 'port':         str_port            = v
            if k == 'verbose':      verbose     = v

        if len(self.str_jsonwrapper):
            str_msg         = json.dumps({self.str_jsonwrapper: d_msg})
        else:
            str_msg         = json.dumps(d_msg)
        response            = io.BytesIO()

        self.qprint("http://%s:%s%s" % (str_ip, str_port, self.str_URL) + '\n '+ str(d_msg),
                    comms  = 'tx')

        c = pycurl.Curl()
        c.setopt(c.POST, 1)
        # c.setopt(c.URL, "http://%s:%s/api/v1/cmd/" % (str_ip, str_port))
        c.setopt(c.URL, "http://%s:%s%s" % (str_ip, str_port, self.str_URL))
        if str_fileToProcess:
            fread               = open(str_fileToProcess, "rb")
            filesize            = os.path.getsize(str_fileToProcess)
            c.setopt(c.HTTPPOST, [  ("local",       (c.FORM_FILE, str_fileToProcess)),
                                    ("encoding",    str_encoding),
                                    ("d_msg",       str_msg),
                                    ("filename",    str_fileToProcess)]
                     )
            c.setopt(c.READFUNCTION,    fread.read)
            c.setopt(c.POSTFIELDSIZE,   filesize)
        else:
            # c.setopt(c.HTTPPOST, [
            #                         ("d_msg",    str_msg),
            #                      ]
            #          )
            c.setopt(c.POSTFIELDS, str_msg)
        if verbose:                     c.setopt(c.VERBOSE, 1)
        # print(self.str_contentType)
        if len(self.str_contentType):   c.setopt(c.HTTPHEADER, ['Content-type: %s' % self.str_contentType])
        c.setopt(c.WRITEFUNCTION,   response.write)
        if len(self.str_auth):
            c.setopt(c.USERPWD, self.str_auth)
        if str_fileToProcess:
            self.qprint("Transmitting " + Colors.YELLOW + "{:,}".format(os.stat(str_fileToProcess).st_size) + \
                        Colors.PURPLE + " bytes...",
                        comms = 'status')
        else:
            self.qprint("Sending data...",
                        comms = 'status')
        try:
            c.perform()
            str_response        = response.getvalue().decode()
        except Exception as e:
            str_exception   = str(e)
            self.qprint('Execption trapped: %s' % str_exception)
            str_response    = str_exception
        c.close()

        self.qprint('response from call = %s' % str_response, comms = 'status')
        if self.b_raw:
            try:
                d_ret           = json.loads(str_response)
            except:
                d_ret           = str_response
        else:
            try:
                d_ret['stdout']     = json.loads(str_response)
            except:
                d_ret['stdout']     = str_response
            if 'status' in d_ret['stdout']:
                d_ret['status']     = d_ret['stdout']['status']
            d_ret['msg']        = 'push OK.'

        if isinstance(d_ret, object):
            self.qprint(json.dumps(d_ret), comms = 'rx')
        if isinstance(d_ret, str):
            self.qprint(d_ret, comms = 'rx')

        return d_ret

    def pushPath_core(self, d_msg, **kwargs):
        """

        """

        str_fileToProcess   = ""
        str_encoding        = "none"
        d_ret               = {}
        for k,v in kwargs.items():
            if k == 'fileToPush':   str_fileToProcess   = v
            if k == 'encoding':     str_encoding        = v
            if k == 'd_ret':        d_ret               = v

        d_meta              = d_msg['meta']
        str_ip              = self.str_ip
        str_port            = self.str_port
        if 'remote' in d_meta:
            d_remote            = d_meta['remote']
            if 'ip' in d_remote:    str_ip      = d_remote['ip']
            if 'port' in d_remote:  str_port    = d_remote['port']

        d_ret               = self.push_core(
                                                fileToPush  = str_fileToProcess,
                                                encoding    = str_encoding,
                                                ip          = str_ip,
                                                port        = str_port
                                            )
        return d_ret

    def pushPath_compress(self, d_msg, **kwargs):
        """
        """

        d_meta              = d_msg['meta']
        str_meta            = json.dumps(d_meta)
        d_local             = d_meta['local']
        str_localPath       = d_local['path']

        d_remote            = d_meta['remote']
        str_ip              = self.str_ip
        str_port            = self.str_port
        if 'ip' in d_remote:
            str_ip          = d_remote['ip']
        if 'port' in d_remote:
            str_port        = d_remote['port']

        str_mechanism       = ""
        str_encoding        = ""
        str_archive         = ""
        d_transport         = d_meta['transport']
        if 'compress' in d_transport:
            d_compress      = d_transport['compress']
            str_archive     = d_compress['archive']
            str_encoding    = d_compress['encoding']

        str_remotePath      = d_remote['path']

        if 'cleanup' in d_compress:
            b_cleanZip      = d_compress['cleanup']


        str_fileToProcess   = str_localPath
        str_zipFile         = ""
        str_base64File      = ""

        b_zip               = True

        if str_archive      == 'zip':   b_zip   = True
        else:                           b_zip   = False

        if os.path.isdir(str_localPath):
            b_zip           = True
            str_archive     = 'zip'

        d_ret               = {}
        d_ret['local']      = {}
        # If specified (or if the target is a directory), create zip archive
        # of the local path
        if b_zip:
            self.qprint("Zipping target...", comms = 'status')
            d_fio   = zip_process(
                action  = 'zip',
                path    = str_localPath,
                arcroot = str_localPath
            )
            if not d_fio['status']: return {'stdout': json.dumps(d_fio)}
            str_fileToProcess   = d_fio['fileProcessed']
            str_zipFile         = str_fileToProcess
            self.qprint("Zipped to %s..." % str_fileToProcess, comms = 'status')
            d_ret['local']['zip']               = d_fio

        # Encode possible binary filedata in base64 suitable for text-only
        # transmission.
        if str_encoding     == 'base64':
            self.qprint("base64 encoding target...", comms = 'status')
            d_fio   = base64_process(
                action      = 'encode',
                payloadFile = str_fileToProcess,
                saveToFile  = str_fileToProcess + ".b64"
            )
            str_fileToProcess       = d_fio['fileProcessed']
            self.qprint("base64 encoded to %s..." % str_fileToProcess, comms = 'status')
            str_base64File          = str_fileToProcess
            d_ret['local']['encoding']                   = d_fio

        # Push the actual file -- note the d_ret!
        d_ret['remoteServer']  = self.push_core(    d_msg,
                                                    fileToPush  = str_fileToProcess,
                                                    encoding    = str_encoding)
                                                    # d_ret       = d_ret)
        d_ret['status'] = d_ret['remoteServer']['status']
        d_ret['msg']    = d_ret['remoteServer']['msg']

        if b_cleanZip:
            self.qprint("Removing temp files...", comms = 'status')
            if os.path.isfile(str_zipFile):     os.remove(str_zipFile)
            if os.path.isfile(str_base64File):  os.remove(str_base64File)

        return d_ret

        # return {'stdout': {'return' : d_ret},
        #         'status': d_ret['fromServer']['status']}

    def pushPath_copy(self, d_msg, **kwargs):
        """
        Handle the "copy" pull operation
        """

        # Parse "header" information
        d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        str_localPath       = d_local['path']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_copy              = d_transport['copy']

        # Pull the actual data into a dictionary holder
        d_curl                      = {}
        d_curl['remoteServer']      = self.push_core(d_msg)
        d_curl['copy']              = {}
        d_curl['copy']['status']    = d_curl['remoteServer']['status']
        if not d_curl['copy']['status']:
            d_curl['copy']['msg']   = "Copy on remote server failed!"
        else:
            d_curl['copy']['msg']   = "Copy on remote server success!"

        return d_curl

    def pathOp_do(self, d_msg, **kwargs):
        """
        Entry point for path-based push/pull calls.

        Essentially, this method is the central dispatching nexus to various
        specialized push operations.

        """

        d_meta              = d_msg['meta']
        d_transport         = d_meta['transport']
        b_OK                = True
        d_ret               = {}

        str_action          = "pull"
        for k,v, in kwargs.items():
            if k == 'action':   str_action  = v

        # First check on the paths, both local and remote
        self.qprint('Checking local path status...', comms = 'status')
        d_ret['localCheck'] = self.path_localLocationCheck(d_msg)
        if not d_ret['localCheck']['status']:
            self.qprint('An error occurred while checking on the local path.',
                        comms = 'error')
            d_ret['localCheck']['msg']          = 'The local path spec is invalid!'
            d_ret['localCheck']['status'] = False
            b_OK            = False
        else:
            d_ret['localCheck']['msg']          = "Check on local path successful."
        d_ret['status']     = d_ret['localCheck']['status']
        d_ret['msg']        = d_ret['localCheck']['msg']

        if b_OK:
            d_transport['checkRemote']  = True
            self.qprint('Checking remote path status...', comms = 'status')
            d_ret['remoteCheck']   = self.path_remoteLocationCheck(d_msg)
            self.qprint(str(d_ret), comms = 'rx')
            if not d_ret['remoteCheck']['status']:
                self.qprint('An error occurred while checking the remote server.',
                            comms = 'error')
                d_ret['remoteCheck']['msg']     = "The remote path spec is invalid!"
                b_OK        = False
            else:
                d_ret['remoteCheck']['msg']     = "Check on remote path successful."
            d_transport['checkRemote']  = False
            d_ret['status']             = d_ret['localCheck']['status']
            d_ret['msg']                = d_ret['localCheck']['msg']

        b_jobExec           = False
        if b_OK:
            if 'compress' in d_transport and d_ret['status']:
                self.qprint('Calling %s_compress()...' % str_action, comms = 'status')
                d_ret['compress']   = eval("self.%s_compress(d_msg, **kwargs)" % str_action)
                d_ret['status']     = d_ret['compress']['status']
                d_ret['msg']        = d_ret['compress']['msg']
                b_jobExec       = True

            if 'copy' in d_transport:
                self.qprint('Calling %s_copy()...' % str_action, comms = 'status')
                d_ret['copyOp']     = eval("self.%s_copy(d_msg, **kwargs)" % str_action)
                d_ret['status']     = d_ret['copyOp']['copy']['status']
                d_ret['msg']        = d_ret['copyOp']['copy']['msg']
                b_jobExec       = True

        if not b_jobExec:
            d_ret['status']   = False
            d_ret['msg']      = 'No push/pull operation was performed! A filepath check failed!'

        if self.b_oneShot:
            d_ret['shutdown'] = self.server_ctlQuit(d_msg)
        return {'stdout': d_ret}

    def server_ctlQuit(self, d_msg):
        """

        :return: d_shutdown shut down JSON message from remote service.
        """

        d_shutdown      = {}
        d_meta          = d_msg['meta']
        d_meta['ctl'] = {
            'serverCmd': 'quit'
        }

        self.qprint('Attempting to shut down remote server...', comms = 'status')
        try:
            # d_shutdown  = self.push_core(d_msg, fileToPush = None)
            d_shutdown  = self.push_core(d_msg)
        except:
            pass
        return d_shutdown

    def pushPath(self, d_msg, **kwargs):
        """
        Push data to a remote server using pycurl.

        Essentially, this method is the central dispatching nexus to various
        specialized push operations.

        """

        return self.pathOp_do(d_msg, action = 'push')

    def pullPath(self, d_msg, **kwargs):
        """
        Pulls data from a remote server using pycurl.

        This method assumes that a prior call has "setup" a remote fileio
        listener and has the ip:port of that instance.

        Essentially, this method is the central dispatching nexus to various
        specialized pull operations.

        :param d_msg:
        :param kwargs:
        :return:
        """

        return self.pathOp_do(d_msg, action = 'pull')

    def httpStr_parse(self, **kwargs):

        for k,v in kwargs.items():
            if k == 'http':     self.str_http   = v

        # Split http string into IP:port and URL
        str_IPport          = self.str_http.split('/')[0]
        self.str_URL        = '/' + '/'.join(self.str_http.split('/')[1:])
        try:
            (self.str_ip, self.str_port) = str_IPport.split(':')
        except:
            self.str_ip     = str_IPport.split(':')
            self.str_port   = args.str_port

    def __call__(self, *args, **kwargs):
        """
        Main entry point for "calling".

        :param self:
        :param kwargs:
        :return:
        """
        str_action  = ''

        for key,val in kwargs.items():
            if key == 'msg':
                self.str_msg    = val
                self.d_msg      = json.loads(self.str_msg)
            if key == 'http':       self.httpStr_parse( http    = val)
            if key == 'verb':       self.str_verb               = val

        if len(self.str_msg):
            if 'action' in self.d_msg: str_action  = self.d_msg['action']
            if 'path' in str_action.lower():
                d_ret = self.pathOp_do(self.d_msg, action = str_action)
            else:
                if self.str_verb == 'GET':
                    d_ret = self.pull_core(msg = self.d_msg)
                if self.str_verb == 'POST':
                    d_ret = self.push_core(self.d_msg)
            str_stdout  = json.dumps(d_ret)
        else:
            d_ret = self.pull_core()
            str_stdout  = '%s' % d_ret

        if not self.b_quiet: print(Colors.CYAN)
        return(str_stdout)