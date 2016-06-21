#!/usr/bin/python3.5


from __future__         import print_function

import  subprocess
import  shlex
import  argparse
import  os
import  sys
import  threading
import  time
from    queue           import  Queue
import  json
import  datetime

def synopsis(ab_shortOnly = False):
    str_scriptName  = os.path.basename(sys.argv[0])
    str_shortSynopsis = """

    NAME

        Run <CMD> in a variety of ways.

        %s     -c|--command <CMD>


    """ % str_scriptName
    str_description = """

    ARGS

        -c|--command <CMD>
        Command to execute

    DESCRIPTION

        '%s' is a wrapper about an underlying system shell that
        executes commands in that shell.

        Standard returns (stdout, stderr) and exit codes are captured
        and available to other processes.
    """ % str_scriptName
    if ab_shortOnly:
        return str_shortSynopsis
    else:
        return str_shortSynopsis + str_description


class crunner(object):
    """
        This family of functor classes provides a unified interface
        to running shell-commands in several contexts:

            - locally on the underlying OS
            - remote host via ssh
            - cluster via scheduler

        Internally, 'crunner' spawns two threads. The first, 'ctl' is a
        control thread that in turn spawns the actual 'exe' thread that
        calls the subprocess module on the passed command line. The 'ctl'
        thread joins the 'exe' thread and so "waits" on it to complete.

            parent execution
        --------O---------------O-------- ... --------
                |              /
                |  __call__   /
                O-------------
                        |
                        |  t_ctl thread (join t_exe)
                        +-------O------------------------ ...--------O--- (end)
                                |                                  /
                                |  t_exe thread                   /
                                +-------O---------------- ... ---O---- (end)
                                        |                       /
                                        | subprocess           /
                                        +---------------- ... +




        The main caller, however, returns to the parent context after a
        short interval. In this manner, main execution can continue in the parent
        process. The parent can query the crunner on the state of spawned
        threads.

    """

    def __init__(self, **kwargs):
        """
        Initial object, set control and other flags.
        :param kwargs:
        """

        self.b_waitForChild     = True
        self.b_shell            = True
        self.b_showStdOut       = True
        self.b_showStdErr       = True

        self.b_splitCompound    = True

        # Queue for communicating between threads
        self.queue              = Queue()

        # Job info
        # Each job executed is stored in a list of
        # dictionaries.
        self.jobCount           = -1
        self.l_job              = []

        # Job template
        self.d_jobInfoTemplate  =  {
            'cmd':          '',
            'status':       'undefined',
            'proc':         None,
            'pid':          -1,
            'returncode':   -1111,
            'stdout':       '',
            'stderr':       ''
        }

        # Threads for job control and execution
        self.t_ctl              = None      # Controller thread
        self.t_exe              = None      # Exe thread

    def __call__(self, str_cmd, **kwargs):
        """
        The __call__ functor essentially creates a controller thread
        which in turns creates an exe thread for the subprocess call.

        The __call__ thus returns to the parent context with minimal
        delay.

        :param str_cmd:
        :param kwargs:
        :return:
        """

        l_args  = shlex.split(str_cmd)
        self.t_ctl     =   threading.Thread(target = self.ctl,
                                            args   = (str_cmd,),
                                            kwargs = kwargs)
        self.t_ctl.start()

        # We wait a small interval to give the exe thread enough
        # time to start the subprocess and determine its PID
        time.sleep(0.5)

    def ctl(self, str_cmd, **kwargs):
        """
        A controller thread.

        :param q:
        :return:
        """
        print("In ctl thread...")

        self.jobCount           += 1
        self.l_job.append(self.jobCount)
        # Populate the jobInfo with template data
        self.l_job[self.jobCount]   = self.d_jobInfoTemplate.copy()

        self.t_exe     =   threading.Thread(target = self.exe,
                                            args   = (str_cmd,),
                                            kwargs = kwargs)
        self.t_exe.start()
        self.t_exe.join()

        self.l_job[self.jobCount]   = self.queue.get()

        # self.d_jobInfo = self.queue.get()
        # print(self.d_jobInfo)
        # print(json.dumps(self.l_job))
        print(self.l_job)

    def exe(self, str_cmd, **kwargs):
        """
        Execute <str_cmd> on the underlying shell in a separate thread.

        Job/process info is written to the thread queue construct

        :param str_cmd: command to execute
        :param kwargs:
        """

        b_ssh   = False

        for key,val in kwargs.items():
            if key == 'ssh':    b_ssh   = bool(val)

        print("In exe thread...")
        print("About to run << %s >> " % str_cmd)

        self.l_job[self.jobCount]['startdate']      = '%s' % datetime.datetime.now()
        proc = subprocess.Popen(
            str_cmd,
            stdout              = subprocess.PIPE,
            stderr              = subprocess.PIPE,
            shell               = True,
            universal_newlines  = True
        )

        b_subprocessRunning     = True
        while b_subprocessRunning:
            try:
                o = proc.communicate(timeout=0.1)
                b_subprocessRunning = False
            except subprocess.TimeoutExpired:
                # self.d_jobInfo['pid']  = proc.pid
                # if b_ssh:
                #     self.remotePID    += proc.stdout.readline().strip()
                self.l_job[self.jobCount]['pid']    = proc.pid

        print("exe complete")

        self.l_job[self.jobCount]['enddate']        = '%s' % datetime.datetime.now()
        self.l_job[self.jobCount]['status']         = 'done'
        self.l_job[self.jobCount]['proc']           = proc
        self.l_job[self.jobCount]['pid']            = proc.pid
        self.l_job[self.jobCount]['returncode']     = proc.returncode
        self.l_job[self.jobCount]['stdout']         = o[0]
        self.l_job[self.jobCount]['stderr']         = o[1]
        self.l_job[self.jobCount]['cmd']            = str_cmd

        # d_data = {
        #     'status':       'done',
        #     'proc':         proc,
        #     'pid':          proc.pid,
        #     'returncode':   proc.returncode,
        #     'stdout':       o[0],
        #     'stderr':       o[1]
        # }

        self.queue.put(self.l_job[self.jobCount])

    def exe_stillRunning(self):
        """
        Checks if the exe thread is still running.
        """
        return self.t_exe.isAlive()

    def exe_waitUntilDone(self, **kwargs):
        """
        Blocks in method until thread is done, i.e. !isAlive()
        """
        timeout = 1

        for key,val in kwargs.items():
            if key == 'timeout':    timeout = val

        while self.exe_stillRunning():
            time.sleep(timeout)

    def exitOnDone(self, **kwargs):
        """
        An exit function that blocks on any threads that might still be
        running. If called with

            timeout     = timeout

        will sleep for timeout seconds between polling. If called with

            returncode  = code

        will force exit to system with passed code, otherwise will
        pass to system exitcode of spawned subprocess.
        """
        timeout             = 1
        b_overrideReturn    = False
        for key,val in kwargs.items():
            if key == 'timeout':    timeout = val
            if key == 'returncode':
                                    b_overrideReturn    = True
                                    returncode          = val
        self.exe_waitUntilDone(timeout = timeout)
        if not b_overrideReturn:
            returncode  = self.l_job[self.jobCount]['returncode']

        if self.b_showStdOut:
            print(self.l_job[self.jobCount]['stdout'])

        sys.exit(returncode)

class crunner_ssh(crunner):
    """
    A specialized class that handles ssh connections to remote
    hosts.

    Effectively this prepends commands with <sshString> and captures
    the remote process ID.

    """

    def __init__(self, **kwargs):
        """
        The constructor for this class. The ssh argument from the
        command line is of form:

            username@host:port

        """

        crunner.__init__(self, **kwargs)

        self.str_remoteUser = ''
        self.str_remoteHost = ''
        self.str_remotePort = '22'
        self.str_sshInput   = ''
        self.remotePID      = ''

        for key, val in kwargs.items():
            if key == 'ssh':    str_sshInput    = val

        self.str_remoteUser = str_sshInput.split('@')[0]
        l_namePort          = str_sshInput.split(':')
        if len(l_namePort) > 1:
            self.str_remotePort = l_namePort[1]
        self.str_remoteHost = l_namePort[0].split('@')[1]

    def __call__(self, str_cmd, *args, **kwargs):
        """
        Pre and post-pend the call with ssh related constructs.

        If the <str_cmd> is a compound shell expression (i.e. has
        semi-colon ';' joins), then each component is executed
        separately.
        """
        str_cmd = "ssh -p %s %s@%s \'%s & echo $!\'" % (
            self.str_remotePort,
            self.str_remoteUser,
            self.str_remoteHost,
            str_cmd
        )

        kwargs['ssh']    = True
        crunner.__call__(self, str_cmd, **kwargs)

    def waitForRemotePID(self, **kwargs):
        """
         This method blocks until the ssh connection has been made and
         the remote processes spawned and its PID captured.
        """
        timeout     = 0.1

        for key,val in kwargs.items():
            if key == 'timeout':    timeout = val

        while not len(self.remotePID):
            time.sleep(timeout)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=synopsis(True))

    parser.add_argument(
        '-c', '--command',
        help    = 'command to run on system.',
        dest    = 'command',
        action  = 'store',
        default = ''
    )

    parser.add_argument(
        '--ssh',
        help    = 'ssh to remote host.',
        dest    = 'ssh',
        action  = 'store',
        default = ''
    )

    args = parser.parse_args()

    # Create a crunner shell
    if len(args.ssh):
        shell   = crunner_ssh(ssh = args.ssh)
    else:
        shell   = crunner()

    # Call the shell on a command line argument
    shell(args.command)

    # Once sub-theads have been spawned, execution returns here,
    # even if the threads are still running. The caller can
    # now query the crunner shell for information on its
    # subprocess.
    print("CLI << %s >>" % args.command)
    print('PID from spawned job on localhost: %s' % shell.l_job[shell.jobCount]['pid'])
    if len(args.ssh):
        shell.waitForRemotePID()
        print('PID of process on remote host: %s' % shell.remotePID)

    # This exits to the system, but only once all threads have completed.
    # The exitcode of the subprocess is returned to the system by this
    # call.
    shell.exitOnDone()

