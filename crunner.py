#!/usr/bin/env python3.5


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
import  platform
from    functools       import  partial

def synopsis(ab_shortOnly = False):
    str_scriptName  = os.path.basename(sys.argv[0])
    str_shortSynopsis = """

    NAME

        %s

    SYNOPSIS


        %s \\
                    -c|--command <CMD>              \\
                    --pipeline                      \\
                    --ssh <user@machine[:<port>]>   \\
                    --auid <apparentUserID>         \\
                    --jid <jobID>                   \\
                    --prettyprint                   \\
                    --jsonprint                     \\
                    --showStdOut                    \\
                    --showStdErr                    \\
                    --echoCmd                       \\
                    --eventLoop                     \\
                    --verbosity <verbosity>         \\

        Run <CMD> in a variety of ways.


    """ % (str_scriptName, str_scriptName)
    str_description = """

    DESCRIPTION

        '%s' is a wrapper about an underlying system shell that
        executes commands in that shell.

        Standard returns (stdout, stderr) and exit codes are captured
        and available to other processes.

    ARGS

        -c|--command <CMD>
        Command to execute

        --verbosity <verbosity>
        The verbosity. Set to "-1" for silent.

        --pipeline
        If specified, treat compound commands (i.e. command strings
        concatenated together with ';') as a pipeline. Track each
        individual command separately.

        --auid <apparentUserID>
        Set the apparent User ID. This is a field stored at the root level
        of a job data structure and is useful is a job is run as one user
        but is apparently run as another. In particular, for certain cluster
        jobs, all jobs might be run as a single "master" user, but need to
        retain some concept of the apparent user that actually scheduled or
        started the job.

        --jid <jobID>
        Set the jobID, which is a field stored at the root level of a job
        data structure.

        --ssh <user@machine[:port]>
        If specified, ssh as <user> to <machine>[:port]> and execute the <CMD>
        on remote host.

        --prettyprint
        If specified, pretty print internal job dictionary object at finish.

        --jsonprint
        If specified, json.dumps() internal job dictionary object at finish.

        --showStdOut
        If specified, print the stdout of each job executed.

        --showStdErr
        If specified, print the stderr of each job executed.

        --echoCmd
        If specified, echo the actual command string that crunner will execute
        on the underlying shell.

        --eventLoop
        If specified, turn on job start/end event processing.

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
        self.level      = 0

        for k, v in kwargs.items():
            if k == 'verbosity':    self.verbosity  = v
            if k == 'level':        self.level      = v

    def __call__(self, *args, **kwargs):
        self.print(*args, **kwargs)

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

            print('%26s | %50s | %30s | ' % (
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
        ----->--O----->---------O----->-- ... ------->----- ... ---->------>
                |              /   ^                                   ^
                |  __call__   /    | (startEvent)                      | (endEvent)
                O---->--+-->--     |                                   |
                        |          |                                   |
                        |          |     t_ctl thread (join t_exe)     |
                        --->-------O---->------------>------ ...--->---O--- (end)
                                 ^ |                                   ^
                                 | |                                  /|
                                 | |  t_exe thread                   / |
                                 | --------O--------->------ ... ---O--+- (end)
                                 |         |                       /   |
                                 |         | subprocess           /    |
                                 \         ---------->------ ... -    /
                                  \         (each job)               /
                                   -----<------------<------ ... -<-


        The main caller, however, returns to the parent context after a
        short interval. In this manner, main execution can continue in the parent
        process. The parent can query the crunner on the state of spawned
        threads, and can provide the object with callbacks that are executed
        on each job's startEvent and endEvent.

    """

    def __init__(self, **kwargs):
        """
        Initial object, set control and other flags.
        :param kwargs:
        """


        self.b_shell            = True
        self.b_showStdOut       = True
        self.b_showStdErr       = True
        self.b_echoCmd          = True

        # Debugging
        self.verbosity          = 0

        # Toggle special handling of "compound" jobs
        self.l_cmd              = []
        self.b_splitCompound    = True
        self.b_syncMasterSlave  = True      # If True, sub-commands will pause
                                            # after complete and need to be
                                            # explicitly told to continue by
                                            # master. The master needs to monitor
                                            # internal state to know when a thread
                                            # is waiting to be told to continue.

        # Queues for communicating between threads
        self.queue_startEvent   = Queue()
        self.queue_endEvent     = Queue()

        # Queues for extracting specific information
        # Separate queues for <start> and <end> events need to be maintained
        self.queue_pid          = Queue()
        self.queueStart_pid     = Queue()
        self.queueEnd_pid       = Queue()

        self.queue_continue     = Queue()
        self.queue              = Queue()

        # Job info
        # Each job executed is stored in a list of
        # dictionaries.
        self.jobCount           = 0
        self.jobTotal           = -1
        self.d_job              = {}
        self.d_fjob             = {}
        self.b_synchronized     = False
        self.b_jobsAllDone      = False
        self.jid                = ''
        self.auid               = ''

        # Threads for job control and execution
        self.t_ctl              = None      # Controller thread
        self.t_exe              = None      # Exe thread

        self.pp                 = pprint.PrettyPrinter(indent=4)

        for key, val in kwargs.items():
            if key == 'verbosity':  self.verbosity  = val
        self.debug              = debug(verbosity = self.verbosity)

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

        if self.b_echoCmd: print(str_cmd)
        l_args          = shlex.split(str_cmd)
        self.l_cmd      = []
        if self.b_splitCompound:
            self.l_cmd  = str_cmd.split(";")
        else:
            self.l_cmd.append(str_cmd)

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

        self.jobTotal   = len(self.l_cmd)

        for job in self.l_cmd:
            # This thread runs independently of the master, so set
            # an unsynchronized flag
            self.b_synchronized         = False


            # Declare the structure
            str_jobCount    = str(self.jobCount)
            self.d_job[str_jobCount]   = {}
            self.d_fjob[str_jobCount]  = {}

            self.t_exe                  =   threading.Thread(   target = self.exe,
                                                                args   = (job,),
                                                                kwargs = kwargs)
            self.t_exe.start()
            self.t_exe.join()

            # self.d_job[str_jobCount]   = self.queue.get()

            # Now, "block" until the parent thread says we can continue...
            self.debug.print("waiting for continue event from master...", level=2)
            blockUntil = self.queue_continue.get()
            self.debug.print("continue event processed", level=2)

            # Increase the job count
            self.jobCount               += 1
            self.debug.print("increasing job count to %d" % self.jobCount, level = 2)

        self.debug.print("b_synchronized = %r" % self.b_synchronized, level=2)
        self.debug.print(msg = 'done ctl', level=2)
        self.b_jobsAllDone  = True

    def queue_pop(self, **kwargs):
        """
        get() [i.e. pop()] from a queue specified in the kwargs

        The main purpose of this method is to control the size of the queue in the
        main exe loop. Each timeout iteration a pid is written to a specific queue, and
        popped during an exception handling.

        Once the event is finished, the pid queues must ONLY have ONE entry, not multiple.

        :param kwargs:
        :return:
        """
        queue = None
        str_queue = ""
        for key, val in kwargs.items():
            if key == 'queue':  str_queue   = val

        if str_queue == 'queueStart':   queue = self.queueStart_pid
        if str_queue == 'queueEnd':     queue = self.queueEnd_pid

        if queue.qsize():
            self.debug("%s queue has %d elements" % (str_queue, queue.qsize()),
                       level=3)
            pid = queue.get()
            self.debug("%s queue popping pid %d..." % (str_queue, pid), level=3)
            self.debug("%s queue has %d elements"   % (str_queue, queue.qsize()),
                       level=3)

    def queue_flush(self, **kwargs):
        """
        Clear a queue.

        :param kwargs:
        :return:
        """
        queue = None
        str_queue = ""
        for key, val in kwargs.items():
            if key == 'queue':  str_queue   = val

        if str_queue == 'queueStart':   queue = self.queueStart_pid
        if str_queue == 'queueEnd':     queue = self.queueEnd_pid

        self.debug("Flushing %s (currently contains %d elements)" % (str_queue, queue.qsize()), level=3)
        for q in range(0, queue.qsize()):
            pid = queue.get()
        self.debug("Flushed %s (currently contains %d elements)" % (str_queue, queue.qsize()), level=3)

    def exe(self, str_cmd, **kwargs):
        """
        Execute <str_cmd> on the underlying shell in a separate thread.

        Job/process info is written to the thread queue construct

        :param str_cmd: command to execute
        :param kwargs:
        """

        b_ssh   = False
        wait    = 0.3

        for key,val in kwargs.items():
            if key == 'ssh':    b_ssh   = bool(val)
            if key == 'wait':   wait    = val

        self.debug.print(msg    = "start << %s >> " % str_cmd,
                         level  = 3)
        str_jobCount    = str(self.jobCount)
        self.d_job[str_jobCount]['cmd']                = str_cmd
        self.d_job[str_jobCount]['done']               = False
        self.d_job[str_jobCount]['started']            = True
        self.d_job[str_jobCount]['startTrigger']       = True
        self.d_job[str_jobCount]['eventFunctionDone']  = False
        if len(self.auid):
            self.d_job[str_jobCount]['auid']           = self.auid
        if len(self.jid):
            self.d_job[str_jobCount]['jid']            = self.jid

        # Platform info
        self.d_job[str_jobCount]['system']             = platform.system()
        self.d_job[str_jobCount]['machine']            = platform.machine()
        self.d_job[str_jobCount]['platform']           = platform.platform()
        self.d_job[str_jobCount]['uname']              = platform.uname()
        self.d_job[str_jobCount]['version']            = platform.version()

        if b_ssh:
            self.d_job[str_jobCount]['pid_remote']     = ""
            self.d_job[str_jobCount]['remoteHost']     = self.str_remoteHost
            self.d_job[str_jobCount]['remoteUser']     = self.str_remoteUser
            self.d_job[str_jobCount]['remotePort']     = self.str_remotePort
            self.d_job[str_jobCount]['sshInput']       = self.str_sshInput

        self.queue_flush(queue = 'queueStart')
        self.queue_flush(queue = 'queueEnd')

        self.queue_startEvent.put({'startTrigger': True})

        self.d_job[str_jobCount]['startstamp']         = '%s' % datetime.datetime.now()
        proc = subprocess.Popen(
            str_cmd,
            stdout              = subprocess.PIPE,
            stderr              = subprocess.PIPE,
            shell               = True,
            universal_newlines  = True
        )

        b_subprocessRunning     = True
        pollLoop                = 0
        self.remotePID          = ""
        while b_subprocessRunning:
            try:
                # self.queue_pid.put(proc.pid)
                self.queueStart_pid.put(proc.pid)
                self.queueEnd_pid.put(proc.pid)
                self.debug.print("Putting pid %d in queues..." % proc.pid, level=3)
                o = proc.communicate(timeout=0.1)
                b_subprocessRunning = False
            except subprocess.TimeoutExpired:
                if b_ssh:
                    self.remotePID    += proc.stdout.readline().strip()
                    self.d_job[str_jobCount]['pid_remote'] = self.remotePID
                # pid = self.queue_pid.get()
                if self.queueStart_pid.qsize(): self.queue_pop(queue = 'queueStart')
                if self.queueEnd_pid.qsize():   self.queue_pop(queue = 'queueEnd')
                self.d_job[str_jobCount]['pid']    = proc.pid
                pollLoop += 1
                if pollLoop % 10 == 0:
                    self.debug.print("job %d (%s) running... started = %r" %
                                     (self.jobCount,
                                      proc.pid,
                                      self.d_job[str_jobCount]['started']),
                                     level = 3)

        self.d_job[str_jobCount]['endstamp']       = '%s' % datetime.datetime.now()
        self.d_job[str_jobCount]['done']           = True
        self.d_job[str_jobCount]['doneTrigger']    = True
        self.d_job[str_jobCount]['started']        = False
        self.d_fjob[str_jobCount]['proc']          = proc
        self.d_job[str_jobCount]['pid']            = proc.pid
        self.d_job[str_jobCount]['returncode']     = proc.returncode
        self.d_job[str_jobCount]['stdout']         = o[0]
        self.d_job[str_jobCount]['stderr']         = o[1]
        self.d_job[str_jobCount]['cmd']            = str_cmd

        self.debug.print("Putting end event in queue...", level=3)
        self.queue_endEvent.put({'endTrigger': True})
        self.queue.put(self.d_job[str_jobCount])

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
        str_jobCount    = str(self.jobCount)
        b_tagPrinted    = False
        print("in tag_print...")
        while not b_tagPrinted:
            try:
                print("%s = %s" % (str_tag, self.d_job[str_jobCount][str_tag]))
                b_tagPrinted    = True
            except:
                pollLoop += 1
                if pollLoop % 10 == 0:
                    self.debug.print("tag not available")
                time.sleep(timeout)

    def pid_get(self, **kwargs):
        """
        Simply reads the pid from the queue_pid().
        """

        b_queueStart_pid    = False
        b_queueEnd_pid      = False
        str_queue           = ""

        for key, val in kwargs.items():
            if key == 'queue':  str_queue   = val

        queue = None
        if str_queue == "queueStart":   queue = self.queueStart_pid
        if str_queue == "queueEnd":     queue = self.queueEnd_pid

        self.debug.print("getting %s pid... (queue size = %d)" % (str_queue, queue.qsize()))
        pid = queue.get()
        self.debug.print("%s pid = %d" % (str_queue, pid))
        return pid

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
        str_jobCount    = str(self.jobCount)
        while not self.d_job[str_jobCount]['done'] and self.exe_stillRunning():
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

        while not b_success and job < self.jobTotal:
            try:
                ret         = self.d_job[str(job)][field]
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

        job     = self.jobCount
        b_end   = False

        for k, v in kwargs.items():
            if k == 'job':  job = v

        self.debug.print("End Queue contains: %d events" % self.queue_endEvent.qsize())
        self.debug.print("End Queue current job = %d/%d" % (self.jobCount, self.jobTotal))
        if self.jobCount < self.jobTotal:
            b_end = self.queue_endEvent.get()
            self.debug.print("Got an end event!")
        return b_end

    def job_started(self, **kwargs):
        """

        Simply returns a boolean if the current or (other) job has started

        :param kwargs:
        :return:
        """

        job     = self.jobCount
        b_start = False

        for k, v in kwargs.items():
            if k == 'job':  job = v

        self.debug.print("Start Queue contains: %d events" % self.queue_startEvent.qsize())
        self.debug.print("Start Queue current job = %d/%d" % (self.jobCount, self.jobTotal))
        if self.jobCount < self.jobTotal:
            b_start = self.queue_startEvent.get()
            self.debug.print("Got a start event!")
        return b_start

    def jobs_loopctl(self, **kwargs):
        """
        This is an even loop entry point.

        The particular method can fire callbacks at two distinct epochs:

            * onJobStart
            * onJobDone

        These call back functions accept a standard arg construct and must return a dictionary
        of which one element contain a boolean 'status'.

        :param kwargs:
        :return:
        """

        timeout         = 0.1
        b_onJobStart    = False
        f_onJobStart    = None
        b_onJobDone     = False
        f_onJobDone     = None

        for key,val in kwargs.items():
            if key == 'timeout':        timeout         = val
            if key == 'onJobStart':
                f_onJobStart    = val
                b_onJobStart    = True
            if key == 'onJobDone':
                f_onJobDone     = val
                b_onJobDone     = True

        # This is the main event loop for this method. Each loop of the while
        # encompasses the lifetime of a single job. Trigger events are
        # evaluated first, and at the end of the loop, processing waits to make
        # sure the job is in fact done so that the main thread can communicate
        # to the ctl thread that the next job can be processed.
        while self.jobCount < self.jobTotal:
            # This short timeout during the very last job loop is needed for
            # synchronization at the very end of the processing loop. It's
            # probably a very very BAD idea to do this but I couldn't figure
            # out another way. The final loop needed a small delay at the start
            # so that the final all-loops-done event can sync properly.
            if self.jobCount == self.jobTotal-1: time.sleep(timeout)

            # Wait for the start event trigger
            while not self.job_started() and self.jobCount < self.jobTotal: pass
            if b_onJobStart and self.jobCount < self.jobTotal: f_onJobStart()

            # Finally, before looping on, we need to wait until the job is in fact
            # over and then set the synchronized flag to tell the ctl thread
            # it's safe to continue
            while not self.job_done() and self.jobCount < self.jobTotal: pass
            if b_onJobDone and self.jobCount < self.jobTotal: f_onJobDone()
            self.debug.print("Setting synchronized flag from %r to True" % self.b_synchronized)
            self.debug.print("jobCount / jobTotal = %d / %d" % (self.jobCount, self.jobTotal))
            self.b_synchronized     = True
            self.debug.print("continue queue has length %d" % self.queue_continue.qsize())
            self.debug.print("putting ok in continue queue")
            self.queue_continue.put(True)

    # This method is somewhat historical and largely depreciated. It is left here
    # for reference/legacy purposes.
    def jobs_eventLoop(self, **kwargs):
        """
        This an event loop entry point.

        Two event/condition families of callbacks should be provided
        by the caller:

            * a list of functions to execute on specific events in
              the queue:

                * onEventTriggered_do
                * onNewJobSpawned_do

            * a list of functions to evaluate when the event loop
              should terminate

        The caller can provide
        callback functions to be triggered on events in the
        proces7sing loop.

        A caller can provide a list of functions to execute on
        events in the job queue and should also provide a terminating
        condition for this event loop.

        Events include:

            * onEventTriggered_do
            * onNewJobSpawned_do


        :param kwargs:
        :return:
        """

        timeout                 = 0.1
        onEventTriggeredDo      = None
        b_onEventTriggeredDo    = False
        f_waitForEvent          = None

        for key,val in kwargs.items():
            if key == 'timeout':        timeout             = val
            if key == 'waitForEvent':   f_waitForEvent      = val
            if key == 'onEventTriggeredDo':
                onEventTriggeredDo    = val
                b_onEventTriggeredDo  = True

        # This is the main event loop for this method. Each loop of the while
        # encompasses the lifetime of a single job. Trigger events are
        # evaluated first, and at the end of the loop, processing waits to make
        # sure the job is in fact done so that the main thread can communicate
        # to the ctl thread that the next job can be processed.
        while self.jobCount < self.jobTotal:
            # Keep the currentJob id fixed during this loop -- while this loop
            # actually runs, the self.jobCount might change, but this loop will
            # only process the self.jobCount as captured here.
            currentJob  = self.jobCount

            time.sleep(timeout)

            # Wait for the event trigger
            self.debug.print("EL: CurrentJob = %d/%d" %(self.jobCount, self.jobTotal))
            while not eval(f_waitForEvent) and self.jobCount < self.jobTotal: pass
            if b_onEventTriggeredDo and self.jobCount < self.jobTotal:
                eval(onEventTriggeredDo)
                self.d_job[str(currentJob)]['eventFunctionDone']   = True
                self.debug.print(msg = "currentJob = %d job queue = %d / %d  -->b_synchronized = %r<--" %
                                       (currentJob,
                                        self.jobCount,
                                        self.jobTotal,
                                        self.b_synchronized), level = 0)

            # Finally, before looping on, we need to wait until the job is in fact
            # over and then set the synchronized flag to tell the ctl thread
            # it's safe to continue
            if self.queueEnd_pid.qsize():
                while not self.job_done() and self.jobCount < self.jobTotal: pass
            self.debug.print("Setting synchronized flag from %r to True" % self.b_synchronized)
            self.b_synchronized     = True
            self.debug.print("continue queue has length %d" % self.queue_continue.qsize())
            self.debug.print("putting ok in continue queue")
            self.queue_continue.put(True)

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
        str_jobCount    = str(self.jobCount-1)
        if not b_overrideReturn:
            returncode  = self.d_job[str_jobCount]['returncode']

        if self.b_showStdOut:
            for j in range(0, self.jobTotal):
                print(self.d_job[str(j)]['stdout'])
        if self.b_showStdErr:
            for j in range(0, self.jobTotal):
                print(self.d_job[str(j)]['stderr'])

        sys.exit(returncode)

    def run(self, str_cmd, **kwargs):
        """
        A convenience function that "runs" the passed <str_cmd> and returns information
        of job "0". Different jobs can be specified by kwargs for compound statements.

        Returns a dictionary:

            {
                "stdout":   <stdout from job>,
                "stderr":   <stderr from job>,
                "exitCode": <exitCode from job>
            }

        """

        str_job = "0"

        for k,v in kwargs.items():
            if k == 'job':  str_job = v

        self.__call__(str_cmd)
        self.jobs_loopctl()

        d_ret                   = {}
        d_ret['stdout']         = self.d_job[str_job]['stdout']
        d_ret['stderr']         = self.d_job[str_job]['stderr']
        d_ret['returncode']     = self.d_job[str_job]['returncode']

        return d_ret

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

        self.l_cmd      = []
        if self.b_splitCompound:
            self.l_cmd  = str_cmd.split(";")
        else:
            self.l_cmd.append(str_cmd)

        i = 0
        for j in self.l_cmd:
            str_sshCmd = "ssh -p %s %s@%s \'%s & echo $!\'" % (
                self.str_remotePort,
                self.str_remoteUser,
                self.str_remoteHost,
                j
            )
            self.l_cmd[i] = str_sshCmd
            i += 1

        str_cmd = " ; ".join(self.l_cmd)

        kwargs['ssh']    = True
        crunner.__call__(self, str_cmd, **kwargs)
        self.waitForRemotePID()

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

def pid_print(shell, **kwargs):

    str_queue   = "None"
    b_silent    = False
    for k, v in kwargs.items():
        if k == 'queue':    str_queue   = v
        if k == 'silent':   b_silent    = v

    pid = shell.pid_get(**kwargs)
    if not b_silent: print("%20s: id of process: %d" % (str_queue, pid))

def job_started(shell):
    return shell.job_started()

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print(synopsis())
        sys.exit(1)

    parser = argparse.ArgumentParser(description=synopsis(True))

    parser.add_argument(
        '-c', '--command',
        help    = 'command to run on system.',
        dest    = 'command',
        action  = 'store',
        default = ''
    )
    parser.add_argument(
        '-v', '--verbosity',
        help    = 'verbosity level.',
        dest    = 'verbosity',
        action  = 'store',
        default = '0'
    )
    parser.add_argument(
        '--ssh',
        help    = 'ssh to remote host.',
        dest    = 'ssh',
        action  = 'store',
        default = ''
    )
    parser.add_argument(
        '--jid',
        help    = 'job ID.',
        dest    = 'jid',
        action  = 'store',
        default = ''
    )
    parser.add_argument(
        '--auid',
        help    = 'apparent user id',
        dest    = 'auid',
        action  = 'store',
        default = ''
    )
    parser.add_argument(
        '--pipeline',
        help    = 'interpret compound cmd as series of jobs',
        dest    = 'b_pipeline',
        action  = 'store_true',
        default = False
    )
    parser.add_argument(
        '--showStdOut',
        help    = 'show stdout of all jobs',
        dest    = 'b_stdout',
        action  = 'store_true',
        default = False
    )
    parser.add_argument(
        '--showStdErr',
        help    = 'show stderr of all jobs',
        dest    = 'b_stderr',
        action  = 'store_true',
        default = False
    )
    parser.add_argument(
        '--echoCmd',
        help    = 'show cmd',
        dest    = 'b_echoCmd',
        action  = 'store_true',
        default = False
    )
    parser.add_argument(
        '--prettyprint',
        help    = 'pretty print job object',
        dest    = 'b_prettyprint',
        action  = 'store_true',
        default = False
    )
    parser.add_argument(
        '--jsonprint',
        help    = 'json print job object',
        dest    = 'b_jsonprint',
        action  = 'store_true',
        default = False
    )
    parser.add_argument(
        '--eventloop',
        help    = 'turn on event loop start/end processing',
        dest    = 'b_eventloop',
        action  = 'store_true',
        default = False
    )

    args = parser.parse_args()

    verbosity   = int(args.verbosity)

    d   = debug(verbosity = verbosity)
    d.print('start module')

    # Create a crunner shell
    if len(args.ssh):
        shell   = crunner_ssh(verbosity = verbosity, ssh = args.ssh)
    else:
        shell   = crunner(verbosity = verbosity)

    shell.b_splitCompound   = args.b_pipeline
    shell.b_showStdOut      = args.b_stdout
    shell.b_showStdErr      = args.b_stderr
    shell.b_echoCmd         = args.b_echoCmd

    shell.jid               = args.jid
    shell.auid              = args.auid

    # Call the shell on a command line argument
    shell(args.command)

    # Once sub-theads have been spawned, execution returns here,
    # even if the threads are still running. The caller can
    # now query the crunner shell for information on its
    # subprocesses.
    d.print(msg = "CLI << %s >>" % args.command, level = 0)

    if not args.b_eventloop:
        shell.jobs_loopctl()
    else:
        # shell.jobs_loopctl( onJobStart   = "pid_print(shell, queue='queueStart')",
        #                     onJobDone    = "pid_print(shell, queue='queueEnd')")
        shell.jobs_loopctl( onJobStart   = partial(pid_print, shell, queue='queueStart'),
                            onJobDone    = partial(pid_print, shell, queue='queueEnd'))

    # These are two legacy/depreciated methods
    # shell.jobs_eventLoop(waitForEvent       = "self.job_started()",
    #                      onEventTriggeredDo = "pid_print(shell, queue='queueStart')")

    # shell.jobs_eventLoop(waitForEvent       = "self.job_done()",
    #                      onEventTriggeredDo = "pid_print(shell, queue='queueEnd')")


    # This exits to the system, but only once all threads have completed.
    # The exitcode of the subprocess is returned to the system by this
    # call.
    d.print('done module')
    if args.b_prettyprint:  shell.pp.pprint(shell.d_job)
    if args.b_jsonprint:    print(json.dumps(shell.d_job))
    shell.exitOnDone()

