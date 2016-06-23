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
import  inspect
import  datetime
import  pprint

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


class debug(object):
    """
        A simple class that provides some helper debug functions. Mostly
        printing function/thread names and checking verbosity level
        before printing.
    """

    def __init__(self, **kwargs):
        """
        Constructor
        """

        self.verbosity  = 0

        for k, v in kwargs.items():
            if k == 'verbosity':    self.verbosity  = v

    def print(self, *args, **kwargs):
        """
        The "print" command for this object.

        :param kwargs:
        :return:
        """

        self.level  = 0
        self.msg    = ""

        for k, v in kwargs.items():
            if k == 'level':    self.level  = v
            if k == 'msg':      self.msg    = v

        if len(args):
            self.msg    = args[0]

        if self.level <= self.verbosity:

            print('%26s | Current thread = %50s | Current function = %30s | ' % (
                datetime.datetime.now(),
                threading.current_thread(),
                inspect.stack()[1][3]
            ), end='')
            for t in range(0, self.level): print("\t", end='')
            print(self.msg)

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

        self.b_shell            = True
        self.b_showStdOut       = True
        self.b_showStdErr       = True

        # Debugging
        self.verbosity          = 0
        self.debug              = debug(verbosity = 10)

        # Toggle special handling of "compound" jobs
        self.b_splitCompound    = True
        self.b_syncMasterSlave  = True      # If True, sub-commands will pause
                                            # after complete and need to be
                                            # explicitly told to continue by
                                            # master. The master needs to monitor
                                            # internal state to know when a thread
                                            # is waiting to be told to continue.

        # Queue for communicating between threads
        self.queue              = Queue()

        # Job info
        # Each job executed is stored in a list of
        # dictionaries.
        self.jobCount           = 0
        self.jobTotal           = -1
        self.d_job              = {}
        # self.b_currentJobDone   = False
        self.b_synchronized     = False

        # Threads for job control and execution
        self.t_ctl              = None      # Controller thread
        self.t_exe              = None      # Exe thread

        self.pp                 = pprint.PrettyPrinter(indent=4)

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

        l_args          = shlex.split(str_cmd)
        self.t_ctl      = threading.Thread(target = self.ctl,
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

        self.debug.print(msg = 'start ctl', level=2)
        timeout = 0.1

        l_cmd   = []
        if self.b_splitCompound:
            l_cmd       = str_cmd.split(";")
        else:
            l_cmd.append(str_cmd)

        self.jobTotal   = len(l_cmd)

        for job in l_cmd:
            # This thread runs independently of the master, so set
            # an unsynchronized flag
            self.b_synchronized         = False


            # Declare the structure
            self.d_job[self.jobCount]   = {}

            self.t_exe                  =   threading.Thread(   target = self.exe,
                                                                args   = (job,),
                                                                kwargs = kwargs)
            self.t_exe.start()
            self.t_exe.join()

            self.d_job[self.jobCount]   = self.queue.get()

            # Now, "block" until the parent thread says we can continue...
            pollLoop = 0
            while self.b_syncMasterSlave and not self.b_synchronized:
                pollLoop += 1
                if pollLoop % 10 == 0:
                    self.debug.print(msg    = "ctl waiting for master sync... b_synchronized = %r" %
                                              self.b_synchronized,
                                     level  = 2)
                time.sleep(timeout)

            # Increase the job count
            self.jobCount               += 1
            self.debug.print("increasing job count to %d" % self.jobCount, level = 2)

        self.debug.print(msg = 'done ctl', level=2)

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

        self.debug.print(msg    = "start << %s >> " % str_cmd,
                         level  = 3)

        self.d_job[self.jobCount]['done']               = False
        self.d_job[self.jobCount]['started']            = True

        self.d_job[self.jobCount]['startstamp']         = '%s' % datetime.datetime.now()
        proc = subprocess.Popen(
            str_cmd,
            stdout              = subprocess.PIPE,
            stderr              = subprocess.PIPE,
            shell               = True,
            universal_newlines  = True
        )

        b_subprocessRunning     = True
        pollLoop                = 0
        while b_subprocessRunning:
            try:
                o = proc.communicate(timeout=0.1)
                b_subprocessRunning = False
            except subprocess.TimeoutExpired:
                # self.d_jobInfo['pid']  = proc.pid
                # if b_ssh:
                #     self.remotePID    += proc.stdout.readline().strip()
                self.d_job[self.jobCount]['pid']    = proc.pid
                pollLoop += 1
                if pollLoop % 10 == 0:
                    self.debug.print("job %s running..." % proc.pid, level = 3)

        self.d_job[self.jobCount]['endstamp']       = '%s' % datetime.datetime.now()
        self.d_job[self.jobCount]['done']           = True
        self.d_job[self.jobCount]['started']        = False
        self.d_job[self.jobCount]['proc']           = proc
        self.d_job[self.jobCount]['pid']            = proc.pid
        self.d_job[self.jobCount]['returncode']     = proc.returncode
        self.d_job[self.jobCount]['stdout']         = o[0]
        self.d_job[self.jobCount]['stderr']         = o[1]
        self.d_job[self.jobCount]['cmd']            = str_cmd

        self.queue.put(self.d_job[self.jobCount])

        # self.b_currentJobDone   = True
        self.debug.print(msg = "done << %s >> " % str_cmd, level=3)

    def exe_stillRunning(self):
        """
        Checks if the exe thread is still running.
        """
        return self.t_exe.isAlive()

    def tag_print(self, **kwargs):
        """
        Simply print the passed tag from the internal data structure, but block
        possibly on error -- there are thread timing considerations and it is
        possible that the child thread hasn't started the job by the time this
        method attempts to access the tag.

        :param kwargs:
        :return:
        """

        timeout = 0.1
        str_tag = 'pid'

        for key, val in kwargs.items():
            if key == 'tag':        str_tag = val
            if key == 'timeout':    timeout = val

        pollLoop        = 0
        try:
            print("%s = %s" % (str_tag, self.d_job[self.jobCount][str_tag]))
        except:
            if pollLoop % 10 == 0:
                self.debug.print("tag not available")
            pollLoop += 1

    def currentJob_waitUntilDone(self, **kwargs):
        """
        Waits until the current job is done. This method
        monitors both the self.b_currentJobDone flag and
        also checks that the exe thread is alive.

        :param kwargs:
        :return:
        """

        timeout     = 0.1

        for key,val in kwargs.items():
            if key == 'timeout':    timeout = val

        pollLoop    = 0
        while not self.d_job[self.jobCount]['done'] and self.exe_stillRunning():
            pollLoop += 1
            if pollLoop % 10 == 0:
                self.debug.print(msg    = "job queue = %d / %d, -->b_synchronized = %r<--" %
                                          (self.jobCount,
                                           self.jobTotal,
                                           self.b_synchronized),
                                 level  = 0)
            time.sleep(timeout)

    def jobInfo_get(self, **kargs):
        """
        A buffered method to access elements of the d_job dictionary. Since
        the requested field might not exist when this function is called,
        the method blocks in a limited timeout.

        Only a certain number of timeouts are allowed before this method
        gives up with an error.

        :param kargs:
        :return:
        """

        timeout             = 0.1
        attemptsTotal       = 500
        job                 = self.jobCount
        field               = 'pid'

        for key, val in kargs.items():
            if key == 'job':            job             = val
            if key == 'field':          field           = val
            if key == 'timeout':        timeout         = val
            if key == 'attemptsTotal':  attemptsTotal   = val

        attempts    = 0
        b_success   = False
        ret         = None


        while not b_success:
            try:
                ret         = self.d_job[job][field]
                b_success   = True
            except:
                time.sleep(timeout)
                attempts += 1
                if attempts > attemptsTotal:
                    b_success   = False
                    break

        return{'success':   b_success,
               'field':     ret}

    def job_done(self, **kwargs):
        """

        Simply returns a boolean if the current or (other) job is done.

        :param kwargs:
        :return:
        """

        job = self.jobCount

        for k, v in kwargs.items():
            if k == 'job':  job = v

        d_ret   = self.jobInfo_get(field = 'done')

        return d_ret['field']

    def job_started(self, **kwargs):
        """

        Simply returns a boolean if the current or (other) job is done.

        :param kwargs:
        :return:
        """

        job = self.jobCount

        for k, v in kwargs.items():
            if k == 'job':  job = v

        d_ret   = self.jobInfo_get(field = 'started')

        return d_ret['field']

    def jobs_eventLoop(self, **kwargs):
        """
        This an event loop entry point.

        Two event/condition families of callbacks should be provided
        by the caller:

            * a list of functions to execute on specific events in
              the queue:

                * onJobEvent_do
                * onNewJobSpawned_do

            * a list of functions to evaluate when the event loop
              should terminate

        The caller can provide
        callback functions to be triggered on events in the
        processing loop.

        A caller can provide a list of functions to execute on
        events in the job queue and should also provide a terminating
        condition for this event loop.

        Events include:

            * onJobEvent_do
            * onNewJobSpawned_do


        :param kwargs:
        :return:
        """

        timeout             = 0.1
        onJobEventDo     = None
        b_onJobEventDo   = False

        oldJobCount         = 0
        newJobCount         = 0

        for key,val in kwargs.items():
            if key == 'timeout':        timeout         = val
            if key == 'onJobEventDo':
                onJobEventDo    = val
                b_onJobEventDo  = True

        self.debug.print(msg = onJobEventDo, level = 0)
        self.debug.print(msg = "job queue = %d / %d  -->b_synchronized = %r<--" %
                               (self.jobCount,
                                self.jobTotal,
                                self.b_synchronized), level = 0)
        while self.jobCount < self.jobTotal:
            self.currentJob_waitUntilDone(**kwargs)
            time.sleep(timeout)
            self.b_synchronized     = True
            self.debug.print(msg = "job queue = %d / %d  -->b_synchronized = %r<--" %
                                   (self.jobCount,
                                    self.jobTotal,
                                    self.b_synchronized), level = 0)
            if b_onJobEventDo and self.jobCount < self.jobTotal:
                eval(onJobEventDo)


    def jobs_waitUntilDone(self, **kwargs):
        """
        Waits until *all* jobs are done.

        :param kwargs:
        :return:
        """

        timeout             = 0.1
        onJobEventDo     = None
        b_onJobEventDo   = False

        for key,val in kwargs.items():
            if key == 'timeout':        timeout         = val
            if key == 'onJobEventDo':
                onJobEventDo    = val
                b_onJobEventDo  = True

        # This is the main event loop for this method.
        while self.jobCount < self.jobTotal:
            # Wait for the job to be done
            while not self.job_done() and self.jobCount < self.jobTotal: pass
            # if self.jobCount < self.jobTotal:
            #     self.d_job[self.jobCount]['done'] = False
            self.b_synchronized     = True
            self.debug.print(msg = "job queue = %d / %d  -->b_synchronized = %r<--" %
                  (self.jobCount,
                   self.jobTotal,
                   self.b_synchronized), level = 0)
            if b_onJobEventDo and self.jobCount < self.jobTotal:
                eval(onJobEventDo)

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
        timeout             = 0.1
        b_overrideReturn    = False
        for key,val in kwargs.items():
            if key == 'timeout':    timeout = val
            if key == 'returncode':
                                    b_overrideReturn    = True
                                    returncode          = val
        self.exe_waitUntilDone(timeout = timeout)
        if not b_overrideReturn:
            returncode  = self.d_job[self.jobCount-1]['returncode']

        if self.b_showStdOut:
            for j in range(0, self.jobTotal):
                print(self.d_job[j]['stdout'])

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

    d   = debug(verbosity = 10)
    d.print('start module')

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
    # subprocesses.
    d.print(msg = "CLI << %s >>" % args.command, level = 0)

    shell.jobs_waitUntilDone(onJobEventDo = "self.tag_print(tag = 'pid')")
    # shell.pp.pprint(shell.d_job)

    if len(args.ssh):
        shell.waitForRemotePID()
        print('PID of process on remote host: %s' % shell.remotePID)

    # This exits to the system, but only once all threads have completed.
    # The exitcode of the subprocess is returned to the system by this
    # call.
    d.print('done module')
    d.print('%s' % shell.pp.pprint(shell.d_job))
    shell.exitOnDone()

