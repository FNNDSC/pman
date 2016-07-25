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

class Client():

    ''' Represents an example client. '''

    def __init__(self, **kwargs):
        # threading.Thread.__init__(self)

        self.str_cmd        = ""
        self.str_ip         = ""
        self.str_port       = ""
        self.str_msg        = ""
        self.str_testsuite  = ""
        self.str_protocol   = "http"
        self.str_auid       = "<auid>"
        self.str_jid        = "<jid>"
        self.loopStart      = 0
        self.loopEnd        = 0
        self.txpause        = 1
        self.pp             = pprint.PrettyPrinter(indent=4)

        self.shell                      = crunner.crunner()
        self.shell.b_splitCompound      = True
        self.shell.b_showStdOut         = True
        self.shell.b_showStdErr         = True
        self.shell.b_echoCmd            = True

        for key,val in kwargs.items():
            if key == 'cmd':        self.str_cmd        = val
            if key == 'msg':        self.str_msg        = val
            if key == 'ip':         self.str_ip         = val
            if key == 'port':       self.str_port       = val
            if key == 'auid':       self.str_auid       = val
            if key == 'jid':        self.str_jid        = val
            if key == 'txpause':    self.txpause        = int(val)
            if key == 'testsuite':  self.str_testsuite  = val
            if key == 'loopStart':  self.loopStart      = int(val)
            if key == 'loopEnd':    self.loopEnd        = int(val)

        print(Colors.LIGHT_GREEN)
        print("""
        \t+---------------------------------+
        \t| Welcome to the pman client test |
        \t+---------------------------------+
        """)
        print(Colors.CYAN + """
        This program sends command payloads to a 'pman' process manager. A
        command is a typical bash command string to be executed and managed
        by pman.

        In addition, several control messages can also be sent to 'pman'. Typically
        these relate to the saving of the internal database.

        Several "canned" command payloads are available, and are triggered
        by an approprite "--testsuite <index> [--loop <loop>]":

            --testsuite 1:
            Create <loop> instances of 'cmd'. These are in fact 'eval'ed, so
            C-style literals like '%d' are replaced by the current <loop>.

            --testsuite 2:
            Get first <loop> jobInfo packages.
        """)

        print(Colors.WHITE + "\t\tWill transmit to: " + Colors.LIGHT_BLUE, end='')
        print('%s://%s:%s' % (self.str_protocol, self.str_ip, self.str_port))
        print(Colors.WHITE + "\t\tIter-transmit delay: " + Colors.LIGHT_BLUE, end='')
        print('%d second(s)' % (self.txpause))

    def testsuite_handle(self, **kwargs):
        """
        Handle the test suites.
        """

        # First, process the <cmd> string for any special characters

        testsuite       = 0

        str_shellCmd    = ""
        str_cmd = self.str_cmd

        for k,v in kwargs.items():
            if k == 'testsuite':    testsuite   = int(v)

        for l in range(self.loopStart, self.loopEnd):

            if testsuite    == 0:
                if "%d" in self.str_cmd:
                    str_cmd = self.str_cmd.replace("%d", str(l))
                    # print(str_cmd)
                str_shellCmd    = "http POST http://%s:%s/api/v1/cmd/ Content-Type:application/json Accept:application/json payload:='{\"exec\": {\"cmd\": \"%s\"}, \"action\":\"run\",\"meta\":{\"auid\":\"%s\", \"jid\":\"%s-%d\"}}'" \
                                        % (self.str_ip, self.str_port, str_cmd, self.str_auid, self.str_jid, l)
                self.shell                      = crunner.crunner(verbosity=-1)
                self.shell.b_splitCompound      = True
                self.shell.b_showStdOut         = True
                self.shell.b_showStdErr         = True
                self.shell.b_echoCmd            = True
                print(Colors.LIGHT_BLUE)
                print("Sending...")
                self.shell(str_shellCmd)
                self.shell.jobs_loopctl()
                print(Colors.LIGHT_GREEN)
                print("Receiving...")
                json_stdout  = json.loads(self.shell.d_job["0"]["stdout"])
                self.pp.pprint(json_stdout)
                print("\n")
                print("Pausing for %d second(s)..." % self.txpause)
                time.sleep(self.txpause)
                print("\n")

    def run(self):
        ''' Connects to server. Send message, poll for and print result to standard out. '''

        if len(self.str_testsuite):
            self.testsuite_handle()

        print(Colors.LIGHT_PURPLE + 'msg to transmit - %s ' % (self.str_msg))



if __name__ == '__main__':

    parser  = argparse.ArgumentParser(description = 'simple client for talking to pman')

    parser.add_argument(
        '--cmd',
        action  = 'store',
        dest    = 'cmd',
        default = '',
        help    = 'Command to be managed by pman.'
    )
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
        default = '127.0.0.1',
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
        '--jid',
        help    = 'job ID.',
        dest    = 'jid',
        action  = 'store',
        default = '<jid>'
    )
    parser.add_argument(
        '--auid',
        help    = 'apparent user id',
        dest    = 'auid',
        action  = 'store',
        default = '<aiud>'
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
        default = ''
    )
    parser.add_argument(
        '--loopEnd',
        help    = 'end internal testsuite loop at loopEnd',
        dest    = 'loopEnd',
        action  = 'store',
        default = ''
    )

    args    = parser.parse_args()
    client  = Client(
                        msg         = args.msg,
                        cmd         = args.cmd,
                        ip          = args.ip,
                        port        = args.port,
                        jid         = args.jid,
                        auid        = args.auid,
                        txpause     = args.txpause,
                        testsuite   = args.testsuite,
                        loopStart   = args.loopStart,
                        loopEnd     = args.loopEnd
                )
    client.run()
    sys.exit(0)