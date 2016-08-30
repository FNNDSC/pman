#!/usr/bin/env python3.5

'''

Send simple messages to pman server.

'''


# import  threading
import  argparse
from    _colors     import  Colors
import  crunner
import  time
import  sys
import  json
import  pprint
import  socket
import  pycurl
import  io
import  os
# import  uu
# import  zipfile
# import  base64
# import  uuid
# import  shutil
import  pfioh
import  urllib
import  codecs

class Client():

    ''' Represents an example client. '''

    def qprint(self, msg, **kwargs):

        str_comms  = ""
        for k,v in kwargs.items():
            if k == 'comms':    str_comms  = v

        if not self.b_quiet:
            if str_comms == 'status':   print(Colors.PURPLE,    end="")
            if str_comms == 'error':    print(Colors.RED,       end="")
            if str_comms == "tx":       print(Colors.YELLOW + "---->")
            if str_comms == "rx":       print(Colors.GREEN  + "<----")
            print(msg)
            if str_comms == "tx":       print(Colors.YELLOW + "---->")
            if str_comms == "rx":       print(Colors.GREEN  + "<----")
            print(Colors.NO_COLOUR, end="")

    def col2_print(self, str_left, str_right):
        print(Colors.WHITE +
              ('%*s' % (self.LC, str_left)), end='')
        print(Colors.LIGHT_BLUE +
              ('%*s' % (self.RC, str_right)) + Colors.NO_COLOUR)

    def __init__(self, **kwargs):
        # threading.Thread.__init__(self)

        # self.str_cmd        = ""
        self.str_ip         = ""
        self.str_port       = ""
        self.str_msg        = ""
        self.str_testsuite  = ""
        self.str_protocol   = "http"
        self.loopStart      = 0
        self.loopEnd        = 0
        self.txpause        = 1
        self.pp             = pprint.PrettyPrinter(indent=4)
        self.b_man          = False
        self.str_man        = ''
        self.b_quiet        = False
        self.LC             = 40
        self.RC             = 40

        for key,val in kwargs.items():
            # if key == 'cmd':        self.str_cmd        = val
            if key == 'msg':        self.str_msg        = val
            if key == 'ip':         self.str_ip         = val
            if key == 'port':       self.str_port       = val
            if key == 'txpause':    self.txpause        = int(val)
            if key == 'testsuite':  self.str_testsuite  = val
            if key == 'loopStart':  self.loopStart      = int(val)
            if key == 'loopEnd':    self.loopEnd        = int(val)
            if key == 'b_quiet':    self.b_quiet        = val
            if key == 'man':        self.str_man        = val

        if len(self.str_man):
            print(self.man(on = self.str_man))
            sys.exit(0)

        self.shell_reset()

        if not self.b_quiet:

            print(Colors.LIGHT_GREEN)
            print("""
            \t\t\t+---------------------------+
            \t\t\t| Welcome to pman_client.py |
            \t\t\t+---------------------------+
            """)
            print(Colors.CYAN + """
            This program sends command payloads to a 'pman.py' process manager. A
            command is a typical bash command string to be executed and managed
            by 'pman.py'.

            In addition to sending compute requests to a 'pman.py' manager, this
            program can also push/pull files/dirs between this host and the host
            running 'pman.py'. This decouples the 'pman.py' compute processes from
            the local filesystem.

            See 'pman_client.py --man commands' for more help.

            """)

            if len(sys.argv) == 1: sys.exit(1)

            self.col2_print("Will transmit to",     '%s://%s:%s' % (self.str_protocol, self.str_ip, self.str_port))
            self.col2_print("Inter-transmit delay:",'%d second(s)' % (self.txpause))

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
            str_commands = Colors.CYAN + """
            The following commands are serviced by this script:
            """ + "\n" + \
            self.man_searchREST(    description =   "short")      + "\n" + \
            self.man_search(        description =   "short")      + "\n" + \
            self.man_done(          description =   "short")      + "\n" + \
            self.man_info(          description =   "short")      + "\n" + \
            self.man_run(           description =   "short")      + "\n" + \
            self.man_testsuite(     description =   "short")      + "\n" + \
            self.man_save(          description =   "short")      + "\n" + \
            self.man_get(           description =   "short")      + "\n" + \
            self.man_fileiosetup(   description =   "short")      + "\n" + \
            self.man_push(          description =   "short")      + "\n" + \
            self.man_pull(          description =   "short")      + "\n" + \
            Colors.YELLOW + \
            """
            To get detailed help on any of the above commands, type
            """ + Colors.LIGHT_CYAN + \
            """
                ./pman_client.py --man <command>
            """

            return str_commands

        if str_man  == 'searchREST':    return self.man_searchREST( description  =   str_amount)
        if str_man  == 'search':        return self.man_search(     description  =   str_amount)
        if str_man  == 'info':          return self.man_info(       description  =   str_amount)
        if str_man  == 'done':          return self.man_done(       description  =   str_amount)
        if str_man  == 'run':           return self.man_run(        description  =   str_amount)
        if str_man  == 'get':           return self.man_get(        description  =   str_amount)
        if str_man  == 'testsuite':     return self.man_testsuite(  description  =   str_amount)
        if str_man  == 'save':          return self.man_save(       description  =   str_amount)
        if str_man  == 'fileiosetup':   return self.man_fileiosetup(description  =   str_amount)
        if str_man  == 'push':          return self.man_push(       description  =   str_amount)
        if str_man  == 'pull':          return self.man_pull(       description  =   str_amount)

    def man_save(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "save"     + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "saves the internal DB to disk." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This saves the internal DB to disk. Note that the DB is saved
                automatically by a timed thread, however, there are times when
                it is useful to trigger a save event directly.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port 5010  --msg  \\
                    '{  "action": "run",
                        "meta": {
                                    "context":      "db",
                                    "operation":    "save",
                                    "dbpath":       "/tmp/pman",
                                    "fileio":       "json"
                                }
                    }'
                """ % self.str_ip + Colors.LIGHT_PURPLE + """

                It is also possible to save an arbitrary sub-set of the
                data base tree by passing optional 'key' and 'value' fields
                which are used to determine a <search> operation. The results
                of this search are then saved as opposed to the entire tree:
                """ + Colors.LIGHT_GREEN + """

                ./pman_client.py --ip %s --port 5010  --msg  \\
                    '{  "action": "run",
                        "meta": {
                                    "context":      "db",
                                    "operation":    "save",
                                    "dbpath":       "/tmp/pman-jid-1",
                                    "fileio":       "json",
                                    "key":          "jid",
                                    "value":        "<jid>-1"
                                }
                    }'

                """ % self.str_ip + Colors.LIGHT_PURPLE + """
                where for example only the part of the database that has a
                'jid' of '<jid>-1' is saved (and also to a different part
                of the filesystem).
                """ + Colors.NO_COLOUR

        return str_manTxt


    def man_testsuite(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "testsuite"    + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "runs several convenience functions in a loop." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This runs several convenience functions in a loop -- used primarily
                to populate an empty pman DB with some default data. Any '%d' strings
                in the <cmd> and <jid> fields will be replaced by the current loop index.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_PURPLE + """

                Run 12 instances of "cal %d 2016" with given auid and jid prefix: """+ \
                Colors.LIGHT_GREEN + """

                ./pman_client.py --ip %s --port 5010      \\
                    --testsuite POST                                \\
                    --loopStart 1 --loopEnd 13                      \\
                    --msg                                           \\
                    '{  "meta": {
                                    "cmd":  "cal %s 2016",
                                    "auid": "rudolphpienaar",
                                    "jid":  "<jid>-%s"
                                }
                    }'
                """ % (self.str_ip, "%d", "%d") + Colors.LIGHT_PURPLE + """

                Get the first 12 "cmd" values from the root data tree: + """ +\
                Colors.LIGHT_GREEN + """

                ./pman_client.py --ip %s --port 5010      \\
                    --testsuite GET_cmd                             \\
                    --loopStart 0 --loopEnd 12                      \\
                    --txpause 0

                """ % self.str_ip + Colors.NO_COLOUR

        return str_manTxt

    def man_searchREST(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "searchREST"    + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "searches for a target using an external client and REST calls." + \
                        Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This searches for a target by first GETting a list of all jobs and then
                GETting each job in turn and parsing its internal fields for a match.
                Effectively, the "client" does the search.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip 192.168.1.189 --port 5010  --msg  \\
                    '{  "action": "searchREST",
                        "meta": {
                                    "key":      "auid",
                                    "value":    "rudolphpienaar"
                                }
                    }'
                """ + Colors.NO_COLOUR

        return str_manTxt

    def man_search(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "search"       + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "searches for a target in a single call." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This searches for a target in a single call by triggering
                an internal search. Effectively the "server" does the search.

                By default, the search returns the key and value that was
                queried as found in the target data tree.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port 5010  --msg  \\
                    '{  "action": "search",
                        "meta": {
                                    "key":      "auid",
                                    "value":    "rudolphpienaar"
                                }
                    }'
                """ % self.str_ip + Colors.LIGHT_PURPLE + """

                It is also possible to return an arbitrary part of the data
                tree that resulted from the search, using an optional "path"
                in the meta dictionary (paths should start with "/"):
                """ + Colors.LIGHT_GREEN + """

                ./pman_client.py --ip %s --port 5010  --msg  \\
                    '{  "action": "search",
                        "meta": {
                                    "key":      "auid",
                                    "value":    "rudolphpienaar",
                                    "path":     "/start/0/startInfo/0/cmd"
                                }
                    }'

                """ % self.str_ip + Colors.LIGHT_PURPLE + """
                to return the "cmd" (or command) part of the starting state
                of the first part of the command pipeline, or
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port 5010  --msg  \\
                    '{  "action": "search",
                        "meta": {
                                    "key":      "auid",
                                    "value":    "rudolphpienaar",
                                    "path":     "/"
                                }
                    }'

                """ % self.str_ip + Colors.LIGHT_PURPLE + """
                to return the entire jobInfo tree of the target.
                """ + Colors.NO_COLOUR

        return str_manTxt

    def man_info(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "info"     + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "returns information on the current job info." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This searches over the jobs space for a job matching the hit
                pattern and returns the startInfo and endInfo fields

                The hit pattern is specified by searching for a <key> in the
                job space that has value <value>

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port 5010  --msg  \\
                    '{  "action": "info",
                        "meta": {
                                    "key":      "jid",
                                    "value":    "<jid>-1"
                                }
                    }'
                """ % self.str_ip + Colors.NO_COLOUR

        return str_manTxt

    def man_done(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "done"       + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "returns information on whether the job is done." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This searches over the jobs space for a job matching the hit
                pattern and returns the OR'd returncode of all per-job components.

                The hit pattern is specified by searching for a <key> in the
                job space that has value <value>

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port 5010  --msg  \\
                    '{  "action": "done",
                        "meta": {
                                    "key":      "jid",
                                    "value":    "<jid>-1"
                                }
                    }'
                """ % self.str_ip + Colors.NO_COLOUR

        return str_manTxt

    def man_push(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "send"       + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "sends a file over HTTP." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This pushes a file over HTTP. The 'meta' dictionary
                can be used to specifiy content specific information
                and other information.

                Note that the "file" server is typically *not* on the
                same port as the pman.py process. Usually a prior call
                must be made to pman.py to start a one-shot listener
                on a given port. This port then accepts the file transfer
                from the 'push' method.
                
                The "meta" dictionary consists of several nested 
                dictionaries. In particular, the "remote/path"
                field can be used to suggest a location on the remote
                filesystem to save the transmitted data. Successful
                saving to this path depends on whether or not the
                remote server process actually has permission to
                write in that location.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port %s  --msg  \\
                    '{  "action": "push",
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
                ./pman_client.py --ip %s --port %s --msg  \\
                    '{  "action": "push",
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

    def man_pull(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "send"       + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "sends a file over HTTP." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This pulls data over HTTP from a remote server.
                The 'meta' dictionary can be used to specifiy content
                specific information and other detail.

                Note that the "file" server is typically *not* on the
                same port as the pman.py process. Usually a prior call
                must be made to pman.py to start a one-shot listener
                on a given port. This port then accepts the file transfer
                from the 'pull' method.

                The "meta" dictionary consists of several nested
                dictionaries. In particular, the "remote/path"
                field can be used to specify a location on the remote
                filesystem to pull. Successful retrieve from this path
                depends on whether or not the remote server process actually
                has permission to read in that location.

                """ + Colors.YELLOW + """EXAMPLE -- using zip:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port %s  --msg  \\
                    '{  "action": "pull",
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
                ./pman_client.py --ip %s --port %s --msg  \\
                    '{  "action": "pull",
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

    def man_fileiosetup(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN                + \
                       "\t\t%-20s" % "fileiosetup"      + \
                       Colors.LIGHT_PURPLE              + \
                       "%-60s" % "starts a single-shot fileio service." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This starts a singleshot "fileserver" that can be used to
                PUSH/PULL files between the remote 'pman.py' server and the
                local client.

                By singleshot is meant that once the file operation is complete
                the server ends.

                The "meta" parameters suggest an ip and port for the server.
                When 'pman.py' starts the service it will return the actual IP
                and port in a JSON payload.

                The "serveforever", however, is honored by the remote pman.py
                process.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port 5010 --msg  \\
                    '{  "action": "fileiosetup",
                        "meta": {
                                    "ip":               "%s",
                                    "port":             "5055",
                                    "serveforever":     false,
                                    "threaded":         true
                                }
                    }'
                """ % (self.str_ip, self.str_ip) + Colors.NO_COLOUR

        return str_manTxt

    def man_run(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "run"       + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "runs a command with optional meta information." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This runs an actual <cmd>, as well some passing some additional meta
                information.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port 5010 --msg  \\
                    '{  "action": "run",
                        "meta": {
                                    "cmd":      "cal 7 1970",
                                    "auid":     "rudolphpienaar",
                                    "jid":      "<jid>-1",
                                    "threaded": true
                                }
                    }'
                """ % self.str_ip + Colors.NO_COLOUR

        return str_manTxt

    def man_get(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "get"       + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "gets a specific quantum of job information." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This GETs information from the internal DB tree.

                The actual quantum of information is specfied in the "path"
                meta parameter, and must start with "/". Any valid element down the
                path from the root of this job in that DB job space can be
                retrieved, eg:

                        /_01/endInfo
                        /_01/start/0/startInfo/0/cmd
                        /_01/end/0/endInfo/0/stdout

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """
                ./pman_client.py --ip %s --port 5010 --msg  \\
                    '{  "action": "get",
                        "meta": {
                                    "path":     "/_01/endInfo"
                                }
                    }'
                """ % self.str_ip + Colors.NO_COLOUR

        return str_manTxt

    def shell_reset(self):
        """
        "resets" i.e. re-initializes the internal crunner shell
        :return:
        """
        self.shell                      = crunner.crunner(verbosity=-1)
        self.shell.b_splitCompound      = False
        self.shell.b_showStdOut         = not self.b_quiet
        self.shell.b_showStdErr         = not self.b_quiet
        self.shell.b_echoCmd            = not self.b_quiet

    def testsuite_handle(self, d_msg, **kwargs):
        """
        Handle the test suites.
        """

        # First, process the <cmd> string for any special characters

        d_meta          = d_msg['meta']
        str_shellCmd    = ""
        b_tx            = False
        str_baseCmd     = d_meta["cmd"]
        str_jid         = d_meta['jid']
        str_cmd         = str_baseCmd
        str_test        = "POST"
        str_suffix      = ""
        l_testsuite     = self.str_testsuite.split('_')
        if len(l_testsuite) == 2:
            [str_test, str_suffix]  = l_testsuite
        if len(l_testsuite) == 1:
            [str_test]  = l_testsuite

        for l in range(self.loopStart, self.loopEnd):
            b_tx        = False
            if "%d" in str_baseCmd:
                d_meta['cmd']   = d_meta['jid'].replace("%d", str(l))
            if "%d" in d_meta['jid']:
                d_meta['jid']   = d_meta['jid'].replace("%d", str(l))
            str_meta            = json.dumps(d_meta)
            d_meta['jid']       = str_jid
            d_meta['cmd']       = str_baseCmd
            self.shell_reset()

            if str_test == "POST":
                #
                # POST <cmd>
                #
                # str_shellCmd    = "http POST http://%s:%s/api/v1/cmd/ Content-Type:application/json Accept:application/json payload:='{\"exec\": {\"cmd\": \"%s\"}, \"action\":\"run\",\"meta\":%s}'" \
                #                         % (self.str_ip, self.str_port, str_cmd, str_meta)
                str_shellCmd    = "http POST http://%s:%s/api/v1/cmd/ Content-Type:application/json Accept:application/json payload:='{\"action\":\"run\",\"meta\":%s}'" \
                                  % (self.str_ip, self.str_port, str_meta)
                b_tx            = True
            if str_test == "GET":
                #
                # GET <cmd>
                #
                str_shellCmd    = "http GET http://%s:%s/api/v1/_%d/%s Content-Type:application/json Accept:application/json" \
                                  % (self.str_ip, self.str_port, l, str_suffix)
                b_tx            = True

            if b_tx:
                print(Colors.LIGHT_BLUE)
                print("Sending...")

                d_ret   = self.shell.run(str_shellCmd)

                print(Colors.LIGHT_GREEN)
                print("Receiving...")
                json_stdout         = {}
                json_stderr         = {}
                json_returncode     = {}
                if len(d_ret["stdout"]):
                    json_stdout         = {"stdout":    json.loads(d_ret["stdout"])}
                else:
                    json_stdout         = {"stdout": ""}
                if len(d_ret["stderr"]):
                    json_stderr         = {"stderr":    d_ret["stderr"]}
                else:
                    json_stderr         = {"stderr": ""}
                if len(str(d_ret["returncode"])):
                    json_returncode     = {"returncode": json.loads(str(d_ret["returncode"]))}
                else:
                    json_returncode     = {"returncode": ""}
                d_out   = {
                    "0":    json_stdout,
                    "1":    json_stderr,
                    "2":    json_returncode
                }
                print(json.dumps(d_out, indent = 4))
                print("\n")
                print(Colors.LIGHT_RED + "Pausing for %d second(s)..." % self.txpause)
                time.sleep(self.txpause)
                print("\n")

    def action_process(self, d_msg):
        """
        Process the "action" in d_msg
        """
        d_meta          = d_msg['meta']

        if d_msg['action'] == 'searchREST':
            str_key     = d_meta['key']
            str_value   = d_meta['value']
            # First get list of all "jobs"
            self.shell_reset()
            str_shellCmd    = "http GET http://%s:%s/api/v1/ Content-Type:application/json Accept:application/json" \
                              % (self.str_ip, self.str_port)
            d_ret       = self.shell.run(str_shellCmd)
            json_stdout = json.loads(d_ret['stdout'])
            json_GET    = json_stdout['GET']
            l_keys      = json_GET.keys()

            for j in l_keys:
                self.shell_reset()
                str_shellCmd    = "http GET http://%s:%s/api/v1/%s/%s Content-Type:application/json Accept:application/json" \
                                  % (self.str_ip, self.str_port, j, str_key)
                d_ret       = self.shell.run(str_shellCmd)
                json_stdout = json.loads(d_ret['stdout'])
                json_val    = json_stdout['GET'][j][str_key]
                if json_val == str_value:
                    if not self.b_quiet: print(Colors.YELLOW)
                    print(j)

        self.transmit(d_msg)

    def pull_core(self, d_msg, **kwargs):
        """
        Just the core of the pycurl logic.
        """

        d_meta              = d_msg['meta']
        str_query           = urllib.parse.urlencode(d_msg)
        response            = io.BytesIO()

        d_remote            = d_meta['remote']
        str_ip              = self.str_ip
        str_port            = self.str_port
        if 'ip' in d_remote:
            str_ip          = d_remote['ip']
        if 'port' in d_remote:
            str_port        = d_remote['port']

        self.qprint("http://%s:%s/api/v1/file?%s" % (str_ip, str_port, str_query),
                    comms  = 'tx')

        c                   = pycurl.Curl()
        c.setopt(c.URL, "http://%s:%s/api/v1/file?%s" % (str_ip, str_port, str_query))
        # c.setopt(c.VERBOSE, 1)
        c.setopt(c.FOLLOWLOCATION,  1)
        c.setopt(c.WRITEFUNCTION,   response.write)
        self.qprint("Waiting for PULL response...", comms = 'status')
        c.perform()
        c.close()
        try:
            str_response        = response.getvalue().decode()
        except:
            str_response        = response.getvalue()
        if len(str_response) < 300:
            # It's possible an error occurred for the response to be so short.
            # Try and json load, and examine for 'status' field.
            b_response      = False
            try:
                d_response  = json.loads(str_response)
                b_response  = True
            except:
                pass
            if b_response:
                if not d_response['status']:
                    self.qprint('Some error occurred at remote location:',
                                comms = 'error')
                    return {'status':   False,
                            'mag':      'PULL unsuccessful',
                            'response': d_response}
                else:
                    return {'status':   d_response['status'],
                            'msg':      'PULL successful',
                            'response': d_response}

        self.qprint("Received " + Colors.YELLOW + "%d" % len(str_response) +
                    Colors.PURPLE + " bytes..." ,
                    comms = 'status')

        return {'status':   True,
                'msg':      'PULL successful',
                'response': str_response}

    def pull_compress(self, d_msg, **kwargs):
        """
        Handle the "compress" pull operation
        """

        # Parse "header" information
        d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        str_localPath       = d_local['path']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_compress          = d_transport['compress']

        if 'cleanup' in d_compress:
            b_cleanZip      = d_compress['cleanup']

        # Pull the actual data into a dictionary holder
        d_pull = self.pull_core(d_msg)

        if not d_pull['status']:
            return {'stdout': json.dumps(d_pull['stdout'])}

        str_localStem       = os.path.split(d_remote['path'])[-1]
        str_fileSuffix      = ""
        if d_compress['archive']     == "zip":       str_fileSuffix   = ".zip"

        str_localFile       = "%s/%s%s" % (d_meta['local']['path'], str_localStem, str_fileSuffix)
        str_response        = d_pull['response']

        d_ret                   = {}
        d_ret['remoteServer']   = {}

        if d_compress['encoding'] == 'base64':
            self.qprint("Decoding base64 encoded text stream to %s..." % \
                        str_localFile, comms = 'status')
            d_fio = pfioh.base64_process(
                action          = 'decode',
                payloadBytes    = str_response,
                saveToFile      = str_localFile
            )
            d_ret['remoteServer']['decode']   = d_fio
        else:
            self.qprint("Writing byte stream to %s..." % str_localFile,
                        comms = 'status')
            with open(str_localFile, 'wb') as fh:
                fh.write(str_response)
                fh.close()
            d_ret['remoteServer']['stream']         = True
            d_ret['remoteServer']['fileWritten']    = str_localFile

        if d_compress['archive'] == 'zip':
            self.qprint("Unzipping %s to %s"  % (str_localFile, str_localPath),
                        comms = 'status')
            d_fio = pfioh.zip_process(
                action          = "unzip",
                payloadFile     = str_localFile,
                path            = str_localPath
            )
            d_ret['remoteServer']['unzip']  = d_fio
            d_ret['status']                 = d_fio['status']
            d_ret['msg']                    = d_fio['msg']

        print(d_ret)
        if b_cleanZip and d_ret['status']:
            self.qprint("Removing zip file %s..." % str_localFile,
                        comms = 'status')
            os.remove(str_localFile)

        return d_ret

    def pull_copy(self, d_msg, **kwargs):
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
        d_curl['remoteServer']      = self.pull_core(d_msg)
        d_curl['copy']              = {}
        d_curl['copy']['status']    = d_curl['remoteServer']['status']
        if not d_curl['copy']['status']:
            d_curl['copy']['msg']   = "Copy on remote server failed!"
        else:
            d_curl['copy']['msg']   = "Copy on remote server success!"

        return d_curl

    def pull_remoteLocationCheck(self, d_msg, **kwargs):
        """
        This method checks if the "remote" path is valid.
        """

        # Pull the actual data into a dictionary holder
        d_pull = self.pull_core(d_msg)
        return d_pull

    def localPath_check(self, d_msg, **kwargs):
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

        return {'check': d_ret, 'status': d_ret['status']}

    def pull(self, d_msg, **kwargs):
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

        return self.remoteOp_do(d_msg, action = 'pull')

    def push_core(self, d_msg, **kwargs):
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
        str_meta            = json.dumps(d_meta)

        d_remote            = d_meta['remote']
        str_ip              = self.str_ip
        str_port            = self.str_port
        if 'ip' in d_remote:
            str_ip          = d_remote['ip']
        if 'port' in d_remote:
            str_port        = d_remote['port']

        d_transport         = d_meta['transport']

        response            = io.BytesIO()

        self.qprint("http://%s:%s/api/v1/cmd/" % (str_ip, str_port) + '\n '+ str(d_msg),
                    comms  = 'tx')

        c = pycurl.Curl()
        c.setopt(c.POST, 1)
        c.setopt(c.URL, "http://%s:%s/api/v1/cmd/" % (str_ip, str_port))
        if str_fileToProcess:
            fread               = open(str_fileToProcess, "rb")
            filesize            = os.path.getsize(str_fileToProcess)
            c.setopt(c.HTTPPOST, [  ("local",    (c.FORM_FILE, str_fileToProcess)),
                                    ("encoding",  str_encoding),
                                    ("d_meta",    str_meta),
                                    ("filename",  str_fileToProcess)]
                     )
            c.setopt(c.READFUNCTION,    fread.read)
            c.setopt(c.POSTFIELDSIZE,   filesize)
        else:
            c.setopt(c.HTTPPOST, [
                                    ("d_meta",    str_meta),
                                  ]
                     )
        # c.setopt(c.VERBOSE, 1)
        c.setopt(c.WRITEFUNCTION,   response.write)
        if str_fileToProcess:
            self.qprint("Transmitting " + Colors.YELLOW + \
                        "%d " % os.stat(str_fileToProcess).st_size + \
                        Colors.PURPLE + "bytes...",
                        comms = 'status')
        else:
            self.qprint("Sending ctl data to server...",
                        comms = 'status')
        c.perform()
        c.close()

        str_response        = response.getvalue().decode()
        d_ret['push_core']  = json.loads(str_response)
        d_ret['status']     = d_ret['push_core']['status']
        d_ret['msg']        = 'push OK.'
        self.qprint(d_ret, comms = 'rx')

        return d_ret

    def push_compress(self, d_msg, **kwargs):
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
            d_fio   = pfioh.zip_process(
                action  = 'zip',
                path    = str_localPath,
                arcroot = str_localPath
            )
            if not d_fio['status']: return {'stdout': json.dumps(d_fio)}
            str_fileToProcess   = d_fio['fileProcessed']
            str_zipFile         = str_fileToProcess
            d_ret['local']['zip']               = d_fio

        # Encode possible binary filedata in base64 suitable for text-only
        # transmission.
        if str_encoding     == 'base64':
            self.qprint("base64 encoding target...", comms = 'status')
            d_fio   = pfioh.base64_process(
                action      = 'encode',
                payloadFile = str_fileToProcess,
                saveToFile  = str_fileToProcess + ".b64"
            )
            str_fileToProcess       = d_fio['fileProcessed']
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

    def push_copy(self, d_msg, **kwargs):
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

    def remoteOp_do(self, d_msg, **kwargs):
        """
        Push data to a remote server using pycurl.

        This method assumes that a prior call has "setup" a remote fileio
        listener and has the ip:port of that instance.

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
        d_ret['localCheck'] = self.localPath_check(d_msg)
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
            d_ret['remoteCheck']   = self.pull_remoteLocationCheck(d_msg)
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
            d_ret['msg']      = 'No push/pull operation was performed! The local check failed!'

        d_meta['ctl']       = {
            'serverCmd':    'quit'
        }

        self.qprint('Shutting down server...', comms = 'status')
        d_shutdown  = self.push_core(d_msg, fileToPush = None)

        return {'stdout': json.dumps(d_ret)}


    def push(self, d_msg, **kwargs):
        """
        Push data to a remote server using pycurl.

        This method assumes that a prior call has "setup" a remote fileio
        listener and has the ip:port of that instance.

        Essentially, this method is the central dispatching nexus to various
        specialized push operations.

        """

        return self.remoteOp_do(d_msg, action = 'push')

    def transmit(self, d_msg, **kwargs):
        """
        Transmit dispatcher.
        """

        d_meta          = d_msg['meta']
        str_action      = d_msg['action']
        # print(d_meta)
        str_meta        = json.dumps(d_meta)
        if str_action != "push" and str_action != "pull":
            str_shellCmd    = "http POST http://%s:%s/api/v1/cmd/ Content-Type:application/json Accept:application/json payload:='{\"action\":\"%s\",\"meta\":%s}'" \
                              % (self.str_ip, self.str_port, str_action, str_meta)
            d_ret           = self.shell.run(str_shellCmd)
        if str_action == 'push':
            d_ret           = self.push(d_msg)
        if str_action == 'pull':
            d_ret           = self.pull(d_msg)
        if len(d_ret['stdout']):
            # print(d_ret['stdout'])
            json_stdout = json.loads(d_ret['stdout'])
        else:
            json_stdout = d_ret
        if not self.b_quiet: print(Colors.YELLOW)
        print(json.dumps(json_stdout, indent=4))


    def run(self):
        ''' Connects to server. Send message, poll for and print result to standard out. '''

        d_msg   = json.loads(self.str_msg)
        if len(self.str_testsuite):
            self.testsuite_handle(d_msg)

        if len(self.str_msg):
            if 'action' in d_msg.keys():
                self.action_process(d_msg)

if __name__ == '__main__':

    str_defIP = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

    parser  = argparse.ArgumentParser(description = 'simple client for talking to pman')

    parser.add_argument(
        '--msg',
        action  = 'store',
        dest    = 'msg',
        default = '',
        help    = 'Control signal to send to pman.'
    )
    parser.add_argument(
        '--ip',
        action  = 'store',
        dest    = 'ip',
        default = str_defIP,
        help    = 'IP to connect.'
    )
    parser.add_argument(
        '--port',
        action  = 'store',
        dest    = 'port',
        default = '5010',
        help    = 'Port to use.'
    )
    parser.add_argument(
        '--txpause',
        help    = 'pause length between transmits',
        dest    = 'txpause',
        action  = 'store',
        default = '1'
    )
    parser.add_argument(
        '--testsuite',
        help    = 'internal test suite',
        dest    = 'testsuite',
        action  = 'store',
        default = ''
    )
    parser.add_argument(
        '--loopStart',
        help    = 'start internal testsuite loop at loopStart',
        dest    = 'loopStart',
        action  = 'store',
        default = '0'
    )
    parser.add_argument(
        '--loopEnd',
        help    = 'end internal testsuite loop at loopEnd',
        dest    = 'loopEnd',
        action  = 'store',
        default = '0'
    )
    parser.add_argument(
        '--quiet',
        help    = 'if specified, only echo JSON output from server response',
        dest    = 'b_quiet',
        action  = 'store_true',
        default = False
    )
    parser.add_argument(
        '--man',
        help    = 'request help',
        dest    = 'man',
        action  = 'store',
        default = ''
    )

    args    = parser.parse_args()
    client  = Client(
                        msg         = args.msg,
                        ip          = args.ip,
                        port        = args.port,
                        txpause     = args.txpause,
                        testsuite   = args.testsuite,
                        loopStart   = args.loopStart,
                        loopEnd     = args.loopEnd,
                        b_quiet     = args.b_quiet,
                        man         = args.man
                )
    client.run()
    sys.exit(0)