#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import  abc
import  time
import  os

import  threading
import  zmq
from    webob           import  Response
import  psutil

import  queue
from    functools       import  partial
import  platform

import  multiprocessing
import  inspect

import  json
import  ast
import  shutil
import  datetime
import  socket
import  uuid

import  pfmisc

# pman local dependencies
try:
    from    .openshiftmgr   import *
except:
    from    openshiftmgr    import *
try:
    from    .crunner        import *
except:
    from    crunner         import *

from pfmisc.Auth            import Auth
from pfmisc.C_snode         import  *
from pfmisc._colors         import  Colors

import  docker
import  pudb
import  pprint
from kubernetes.client.rest import ApiException

str_devNotes = """

    08 June 2017
    * NOTE: The zmq socket *always* sends back HTTP formatted headers around
            the response string. The listening object (usually pfurl) should
            *NOT* parse this with --httpResponseBodyParse!

    10 May 2017
    *   Should methods in the listener be functors? Certain methods, such as 
        'run' and 'status' need specialized implementations based on a run 
        environment. This run environment is not known by the listener when 
        it starts, but can be specified at payload parsing by the process() 
        method. This, a method such as
        
            t_run_process()
            
        might need at arbitrary call time to be specialized to some external 
        condition set (say by running as a container). Naively, this can be 
        parsed in the message and thread redirected to
        
            t_run_process_swarm()
            
        for example.
        
        Would a functor type approach be useful at all?

"""

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stopper = threading.Event()

    def stopit(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.isSet()


class pman(object):
    """
    The server class for the pman (process manager) server

    """
    __metaclass__   = abc.ABCMeta

    def col2_print(self, str_left, str_right, level = 1):
        self.dp.qprint(Colors.WHITE +
              ('%*s' % (self.LC, str_left)), 
              end       = '', 
              level     = level,
              syslog    = False)
        self.dp.qprint(Colors.CYAN +
              ('%*s' % (self.RC, str_right)) + Colors.NO_COLOUR, 
              level     = level,
              syslog    = False)

    def __init__(self, **kwargs):
        """
        Constructor
        """
        self.within             = None                      # An encapsulating object

        # Description
        self.str_desc           = ""
        self.str_name           = ""
        self.str_version        = ""
        self.__name__           = 'pman'

        # The main server function
        self.threaded_server    = None

        # The listener thread array -- each element of this array is threaded listener
        # object
        self.l_listener         = []
        self.listenerSleep      = 0.1

        # The fileIO threaded object
        self.fileIO             = None

        # DB
        self.b_clearDB          = False
        self.str_DBpath         = '/tmp/pman'
        self.ptree             = C_stree()
        self.str_fileio         = 'json'
        self.DBsavePeriod       = 60

        # Comms
        self.str_protocol       = "tcp"
        self.str_IP             = "127.0.0.1"
        self.str_port           = "5010"
        self.router_raw         = 0
        self.listeners          = 1
        self.b_http             = False
        self.socket_front       = None
        self.socket_back        = None

        # Job info
        self.auid               = ''
        self.jid                = ''
        self.container_env      = ''

        # Debug parameters
        self.str_debugFile      = '/dev/null'
        self.b_debugToFile      = True
        self.pp                 = pprint.PrettyPrinter(indent=4)
        self.verbosity          = 0

        # Authentication parameters
        self.b_tokenAuth        = False
        self.authModule         = None

        for key,val in kwargs.items():
            if key == 'protocol':       self.str_protocol   = val
            if key == 'IP':             self.str_IP         = val
            if key == 'port':           self.str_port       = val
            if key == 'raw':            self.router_raw     = int(val)
            if key == 'listeners':      self.listeners      = int(val)
            if key == 'listenerSleep':  self.listenerSleep  = float(val)
            if key == 'DBsavePeriod':   self.DBsavePeriod   = int(val)
            if key == 'http':           self.b_http         = int(val)
            if key == 'within':         self.within         = val
            if key == 'debugFile':      self.str_debugFile  = val
            if key == 'debugToFile':    self.b_debugToFile  = val
            if key == 'DBpath':         self.str_DBpath     = val
            if key == 'clearDB':        self.b_clearDB      = val
            if key == 'desc':           self.str_desc       = val
            if key == 'name':           self.str_name       = val
            if key == 'version':        self.str_version    = val
            if key == 'containerEnv':   self.container_env  = val.lower()
            if key == 'verbosity':      self.verbosity      = int(val)
            if key == 'b_tokenAuth':    self.b_tokenAuth    = val
            if key == 'str_tokenPath':
                if self.b_tokenAuth:
                    self.authModule = Auth('socket', val)
        # Screen formatting
        self.LC                 = 30
        self.RC                 = 40
        self.dp                 = pfmisc.debug(    
                                            verbosity   = self.verbosity,
                                            debugFile   = self.str_debugFile,
                                            debugToFile = self.b_debugToFile,
                                            within      = self.__name__)

        if self.b_clearDB and os.path.isdir(self.str_DBpath):
            shutil.rmtree(self.str_DBpath)

        self.dp.qprint(self.str_desc, level = 1)

        self.col2_print('Server is listening on',
                        '%s://%s:%s' % (self.str_protocol, self.str_IP, self.str_port))
        self.col2_print('Router raw mode',                  str(self.router_raw))
        self.col2_print('HTTP response back mode',          str(self.b_http))
        self.col2_print('listener sleep',                   str(self.listenerSleep))

        # Create the main internal DB data structure/abstraction
        self.ptree             = C_stree()

        # Read the DB from HDD
        self.DB_fileIO(cmd = 'load')

        # Setup zmq context
        self.zmq_context        = zmq.Context()

    def DB_read(self, **kwargs):
        """
        Read the DB from filesystem. If DB does not exist on filesystem,
        create an empty DB and save to filesystem.
        """
        if os.path.isdir(self.str_DBpath):
            self.dp.qprint("Reading pman DB from disk...\n")
            self.ptree = C_stree.tree_load(
                pathDiskRoot    = self.str_DBpath,
                loadJSON        = True,
                loadPickle      = False)
            self.dp.qprint("pman DB read from disk...\n")
            self.col2_print('Reading pman DB from disk:', 'OK')
        else:
            P = self.ptree
            # P.cd('/')
            # P.mkdir('proc')
            P.tree_save(
                startPath       = '/',
                pathDiskRoot    = self.str_DBpath,
                failOnDirExist  = False,
                saveJSON        = True,
                savePickle      = False
            )
            self.col2_print('Reading pman DB from disk:',
                            'No DB found... creating empty default DB')
        self.dp.qprint(Colors.NO_COLOUR, end='')

    def DB_fileIO(self, **kwargs):
        """
        Process DB file IO requests. Typically these control the
        DB -- save or load.
        """
        str_cmd     = 'save'
        str_DBpath  = self.str_DBpath
        tree_DB     = self.ptree

        def loadFromDiskAsJSON():
            tree_DB = C_stree.tree_load(
                startPath       = '/',
                pathDiskRoot    = str_DBpath,
                failOnDirExist  = False,
                loadJSON        = True,
                loadPickle      = False)
            return tree_DB

        def loadFromDiskAsPickle():
            tree_DB = C_stree.tree_load(
                startPath       = '/',
                pathDiskRoot    = str_DBpath,
                failOnDirExist  = False,
                loadJSON        = False,
                loadPickle      = True)
            return tree_DB

        def saveToDiskAsJSON(tree_DB):
            tree_DB.tree_save(
                startPath       = '/',
                pathDiskRoot    = str_DBpath,
                failOnDirExist  = False,
                saveJSON        = True,
                savePickle      = False)

        def saveToDiskAsPickle(tree_DB):
            tree_DB.tree_save(
                startPath       = '/',
                pathDiskRoot    = str_DBpath,
                failOnDirExist  = False,
                saveJSON        = False,
                savePickle      = True)
            
        for k,v in kwargs.items():
            if k == 'cmd':      str_cmd             = v
            if k == 'fileio':   self.str_fileio     = v
            if k == 'dbpath':   str_DBpath          = v
            if k == 'db':       tree_DB             = v

        # self.dp.qprint('cmd      = %s' % str_cmd)
        # self.dp.qprint('fileio   = %s' % self.str_fileio)
        # self.dp.qprint('dbpath   = %s' % str_DBpath)

        if str_cmd == 'clear':
            # This wipes the existing DB both in memory
            # and in disk storage.
            self.dp.qprint('Clearing internal memory DB...')
            tree_DB = C_stree()
            self.dp.qprint('Removing DB from persistent storage...')
            if os.path.isdir(str_DBpath):
                shutil.rmtree(str_DBpath, ignore_errors=True)     
            self.dp.qprint('Saving empty DB to peristent storage')
            saveToDiskAsJSON(tree_DB)       

        if str_cmd == 'save':
            if os.path.isdir(str_DBpath):
                shutil.rmtree(str_DBpath, ignore_errors=True)
            #print(tree_DB)
            if self.str_fileio   == 'json':     saveToDiskAsJSON(tree_DB)
            if self.str_fileio   == 'pickle':   saveToDiskAsPickle(tree_DB)

        if str_cmd == 'load':
            if os.path.isdir(str_DBpath):
                self.dp.qprint("Reading pman DB from disk...\n")
                if self.str_fileio   == 'json':     tree_DB = loadFromDiskAsJSON()
                if self.str_fileio   == 'pickle':   tree_DB = loadFromDiskAsPickle()
                self.dp.qprint("Pre-existing DB found at %s..." % str_DBpath)
                self.ptree         = tree_DB
                self.ptree.cd('/')
                self.dp.qprint('DB root nodes:\n%s' % self.ptree.str_lsnode())
            else:
                saveToDiskAsJSON(tree_DB)
                self.col2_print('Reading pman DB from disk:',
                                'No DB found... creating empty default DB')
            self.dp.qprint(Colors.NO_COLOUR, end='')
        self.ptree  = tree_DB

    def thread_serve(self):
        """
        Serve the 'start' method in a thread.
        :return:
        """
        self.threaded_server = StoppableThread(target=self.start)
        self.threaded_server.start()

        while not self.threaded_server.stopped():
            time.sleep(1)

        # Stop the listeners...
        self.dp.qprint("setting b_stopThread on all listeners...")
        for i in range(0, self.listeners):
            self.dp.qprint("b_stopThread on listener %d and executing join()..." % i)
            self.l_listener[i].b_stopThread = True
            self.l_listener[i].join()

        # Stop the fileIO
        self.fileIO.b_stopThread    = True
        self.dp.qprint("b_stopThread on fileIO executing join()...")
        self.fileIO.join()

        self.dp.qprint("Shutting down the zmq infrastructure...")
        try:
            self.dp.qprint('calling self.socket_back.close()')
            self.socket_back.close()
        except:
            self.dp.qprint('Caught exception in closing back socket')

        try:
            self.dp.qprint('calling self.socket_front.close()')
            self.socket_front.close()
        except zmq.error.ZMQError:
            self.dp.qprint('Caught exception in closing front socket...')

        self.dp.qprint('calling zmq_context.term()')
        # self.zmq_context.term()

        self.dp.qprint("calling join() on all this thread...")
        self.threaded_server.join()
        self.dp.qprint("shutdown successful...")

    def start(self):
        """
            Main execution.

            * Instantiate several 'listener' worker threads
                **  'listener' threads are used to process input from external
                    processes. In turn, 'listener' threads can thread out
                    'crunner' threads that actually "run" the job.
            * Instantiate a job poller thread
                **  'poller' examines the internal DB entries and regularly
                    queries the system process table, tracking if jobs
                    are still running.
        """
        self.dp.qprint('Starting %d Listener threads' % self.listeners)

        # Front facing socket to accept client connections.
        self.socket_front = self.zmq_context.socket(zmq.ROUTER)
        self.socket_front.router_raw = self.router_raw
        self.socket_front.setsockopt(zmq.LINGER, 1)
        self.socket_front.bind('%s://%s:%s' % (self.str_protocol,
                                          self.str_IP,
                                          self.str_port)
                          )

        # Backend socket to distribute work.
        self.socket_back = self.zmq_context.socket(zmq.DEALER)
        self.socket_back.setsockopt(zmq.LINGER, 1)
        self.socket_back.bind('inproc://backend')

        # Start the 'fileIO' thread
        self.fileIO      = FileIO(      DB          = self.ptree,
                                        timeout     = self.DBsavePeriod,
                                        within      = self,
                                        debugFile   = self.str_debugFile,
                                        verbosity   = self.verbosity,
                                        debugToFile = self.b_debugToFile)
        self.fileIO.start()


        # Start the 'listener' workers... keep track of each
        # listener instance so that we can selectively stop
        # them later.
        for i in range(0, self.listeners):
            self.l_listener.append(Listener(
                                    id              = i,
                                    context         = self.zmq_context,
                                    DB              = self.ptree,
                                    DBpath          = self.str_DBpath,
                                    http            = self.b_http,
                                    containerEnv    = self.container_env,
                                    within          = self,
                                    listenerSleep   = self.listenerSleep,
                                    verbosity       = self.verbosity,
                                    debugToFile     = self.b_debugToFile,
                                    debugFile       = self.str_debugFile,
                                    b_tokenAuth     = self.b_tokenAuth,
                                    authModule      = self.authModule))
            self.l_listener[i].start()

        # Use built in queue device to distribute requests among workers.
        # What queue device does internally is,
        #   1. Read a client's socket ID and request.
        #   2. Send socket ID and request to a worker.
        #   3. Read a client's socket ID and result from a worker.
        #   4. Route result back to the client using socket ID.
        self.dp.qprint("*******before  zmq.device!!!")
        try:
            zmq.device(zmq.QUEUE, self.socket_front, self.socket_back)
        except:
            self.dp.qprint('Hmmm... some error was caught on shutting down the zmq.device...')
        self.dp.qprint("*******after zmq.device!!!")

    def __iter__(self):
        yield('Feed', dict(self.ptree.snode_root))

    # @abc.abstractmethod
    # def create(self, **kwargs):
    #     """Create a new tree
    #
    #     """

    def __str__(self):
        """Print
        """
        return str(self.ptree.snode_root)

    @property
    def stree(self):
        """STree Getter"""
        return self.ptree

    @stree.setter
    def stree(self, value):
        """STree Getter"""
        self.ptree = value

class FileIO(threading.Thread):
    """
    A class that periodically saves the database from memory out to disk.
    """

    def __init__(self, **kwargs):
        self.__name             = "FileIO"
        self.b_http             = False

        self.str_DBpath         = "/tmp/pman"

        self.timeout            = 60
        self.within             = None

        self.b_stopThread       = False
        self.verbosity          = 0

        # Debug parameters
        self.str_debugFile      = '/dev/null'
        self.b_debugToFile      = True
        self.pp                 = pprint.PrettyPrinter(indent=4)

        for key,val in kwargs.items():
            if key == 'DB':             self.ptree          = val
            if key == 'DBpath':         self.str_DBpath     = val
            if key == 'timeout':        self.timeout        = val
            if key == 'within':         self.within         = val
            if key == 'debugFile':      self.str_debugFile  = val
            if key == 'debugToFile':    self.b_debugToFile  = val
            if key == 'verbosity':      self.verbosity      = int(val)

        self.dp                 = pfmisc.debug(
                                        verbosity   = self.verbosity,
                                        debugFile   = self.str_debugFile,
                                        debugToFile = self.b_debugToFile,
                                        within      = self.__name)

        threading.Thread.__init__(self)

    def run(self):
        """ Main execution. """
        # Socket to communicate with front facing server.
        while not self.b_stopThread:
            # self.dp.qprint('Saving DB as type "%s" to "%s"...' % (
            #     self.within.str_fileio,
            #     self.within.str_DBpath
            # ))
            self.within.DB_fileIO(cmd = 'save')
            # self.dp.qprint('DB saved...')
            for second in range(0, self.timeout):
                if not self.b_stopThread:
                    time.sleep(1)
                else:
                    break

        self.dp.qprint('returning from FileIO run method...')
        # raise ValueError('FileIO thread terminated.')

class Listener(threading.Thread):
    """ Listeners accept communication requests from front facing server.
        Parse input text streams and act accordingly. """

    def __init__(self, **kwargs):
        self.__name             = "Listener"
        self.b_http             = False

        self.poller             = None
        self.str_DBpath         = "/tmp/pman"
        self.str_jobRootDir     = ''

        self.listenerSleep      = 0.1
        self.verbosity          = 0

        self.jid                = ''
        self.auid               = ''

        self.within             = None
        self.b_stopThread       = False

        self.openshiftmgr       = None

        # Debug parameters
        self.str_debugFile      = '/dev/null'
        self.b_debugToFile      = True
        self.pp                 = pprint.PrettyPrinter(indent=4)

        for key,val in kwargs.items():
            if key == 'context':        self.zmq_context    = val
            if key == 'listenerSleep':  self.listenerSleep  = float(val)
            if key == 'id':             self.worker_id      = val
            # if key == 'DB':             self.ptree          = val
            if key == 'DBpath':         self.str_DBpath     = val
            if key == 'http':           self.b_http         = val
            if key == 'within':         self.within         = val
            if key == 'debugFile':      self.str_debugFile  = val
            if key == 'debugToFile':    self.b_debugToFile  = val
            if key == 'containerEnv':   self.container_env  = val
            if key == 'verbosity':      self.verbosity      = int(val)
            if key == 'b_tokenAuth':    self.b_tokenAuth    = val
            if key == 'authModule':     self.authModule     = val

        self.dp                 = pfmisc.debug(
                                        verbosity   = self.verbosity,
                                        debugFile   = self.str_debugFile,
                                        debugToFile = self.b_debugToFile,
                                        within      = self.__name)

        threading.Thread.__init__(self)
        # logging.debug('leaving __init__')

    def df_print(self, adict):
        """
        Return a nicely formatted string representation of a dictionary
        """
        return self.pp.pformat(adict).strip()

    def run(self):
        """ Main execution. """
        # Socket to communicate with front facing server.
        self.dp.qprint('starting...')
        socket = self.zmq_context.socket(zmq.DEALER)
        socket.connect('inproc://backend')

        b_requestWaiting        = False
        resultFromProcessing    = False
        request                 = ""
        client_id               = -1
        self.dp.qprint(Colors.BROWN + "Listener ID - %s: run() - Ready to serve..." % self.worker_id, level = 1)
        while not self.b_stopThread:

            # wait (non blocking) for input on socket
            try:
                client_id, request  = socket.recv_multipart(flags = zmq.NOBLOCK)
                self.dp.qprint('Received %s from client_id: %s' % (request, client_id))
                b_requestWaiting    = True
            except zmq.Again as e:
                if self.listenerSleep:
                    time.sleep(0.1)
                else:
                    pass

            if b_requestWaiting:
                self.dp.qprint(Colors.BROWN + 'Listener ID - %s: run() - Received comms from client.' % (self.worker_id))
                self.dp.qprint(Colors.BROWN + 'Client sends: %s' % (request))

                resultFromProcessing    = self.process(request)
                if resultFromProcessing:
                    self.dp.qprint(Colors.BROWN + 'Listener ID - %s: run() - Sending response to client.' %
                                   (self.worker_id))
                    self.dp.qprint('JSON formatted response:')
                    str_payload = json.dumps(resultFromProcessing, sort_keys=False, indent=4)
                    self.dp.qprint(Colors.LIGHT_CYAN + str_payload)
                    self.dp.qprint(Colors.BROWN + 'len = %d chars' % len(str_payload))
                    socket.send(client_id, zmq.SNDMORE)
                    if self.b_http:
                        str_contentType     = "application/html"
                        res                 = Response(str_payload)
                        res.content_type    = str_contentType

                        str_HTTPpre         = "HTTP/1.1 "
                        str_res             = "%s%s" % (str_HTTPpre, str(res))
                        str_res             = str_res.replace("UTF-8", "UTF-8\nAccess-Control-Allow-Origin: *")
                        self.dp.qprint('HTML response')
                        self.dp.qprint(str_res.encode())
                        socket.send(str_res.encode())
                    else:
                        str_contentType     = "application/json"
                        res                 = Response(str_payload)
                        res.content_type    = str_contentType
                        str_HTTPpre         = "HTTP/1.1 "
                        str_res             = '%s%s' % (str_HTTPpre, (res))
                        self.dp.qprint(str_res)
                        socket.send_string(str_res)
            b_requestWaiting    = False
        self.dp.qprint('Listener ID - %s: Returning from run()...' % self.worker_id)
        # raise('Listener ID - %s: Thread terminated' % self.worker_id)
        return True

    def t_search_process(self, *args, **kwargs):
        """

        Search

        :param args:
        :param kwargs:
        :return:
        """

        self.dp.qprint("In search process...")

        d_request   = {}
        d_ret       = {}
        hits        = 0

        for k, v in kwargs.items():
            if k == 'request':      d_request   = v

        d_meta          = d_request['meta']

        b_pathSpec      = False
        str_path        = ""
        if 'path' in d_meta:
            b_pathSpec  = True
            str_path    = d_meta['path']

        b_jobSpec       = False
        str_jobSpec    = ""
        if 'job' in d_meta:
            b_jobSpec   = True
            str_jobSpec = d_meta['job']

        b_fieldSpec    = False
        str_fieldSpec  = ""
        if 'field' in d_meta:
            b_fieldSpec = True
            str_fieldSpec = d_meta['field']

        b_whenSpec      = False
        str_whenSpec    = "end"
        if 'when' in d_meta:
            b_whenSpec = True
            str_whenSpec = d_meta['when']

        self.dp.qprint(d_meta)
        self.dp.qprint(b_pathSpec)
        str_fileName    = d_meta['key']
        str_target      = d_meta['value']
        p               = self.within.ptree
        str_origDir     = p.cwd()
        str_pathOrig    = str_path
        for r in self.within.ptree.lstr_lsnode('/'):
            if p.cd('/' + r)['status']:
                str_val = p.cat(str_fileName)
                if str_val == str_target:
                    if not b_pathSpec:
                        str_path            = '/api/v1/' + r + '/' + str_fileName
                    else:
                        str_path            = '/api/v1/' + r + str_pathOrig
                        if str_path[-1] == '/': str_path = str_path[:-1]
                    if b_jobSpec:
                        str_path            = '/api/v1/' + r +              '/' + \
                                                str_whenSpec +              '/' + \
                                                str_jobSpec +               '/' + \
                                                '%sInfo' % str_whenSpec +   '/' + \
                                                str_jobSpec +               '/' + \
                                                str_fieldSpec
                    d_ret[str(hits)]    = {}
                    d_ret[str(hits)]    = self.DB_get(path = str_path)
                    hits               += 1
        p.cd(str_origDir)

        return {"d_ret":    d_ret,
                "status":   bool(hits)}

    def t_info_process(self, *args, **kwargs):
        """

        Check if the job corresponding to the search pattern is "done".

        :param args:
        :param kwargs:
        :return:
        """

        self.dp.qprint("In info process...")

        d_request   = {}
        d_ret       = {}
        b_status    = False
        hits        = 0
        for k, v in kwargs.items():
            if k == 'request':      d_request   = v

        d_search    = self.t_search_process(request = d_request)['d_ret']

        p = self.within.ptree
        for j in d_search.keys():
            d_j = d_search[j]
            for job in d_j.keys():
                str_pathStart       = '/api/v1/' + job + '/startInfo'
                str_pathEnd         = '/api/v1/' + job + '/endInfo'
                d_ret[str(hits)+'.0']    = {}
                d_ret[str(hits)+'.0']    = self.DB_get(path = str_pathStart)
                d_ret[str(hits)+'.1']    = {}
                d_ret[str(hits)+'.1']    = self.DB_get(path = str_pathEnd)
                hits               += 1
        if not hits:
            d_ret                   = {
                "-1":   {
                    "noJobFound":   {
                        "endInfo":  {"allJobsDone": None}
                    }
                }
            }
        else:
            b_status            = True
        return {"d_ret":    d_ret,
                "status":   b_status}

    def t_quit_process(self, *args, **kwargs):
        """
        Process the 'quit' POST directive. This might appear counter-intuitive
        at first glance since the 'get' is the result of a REST POST, but is
        logically consistent within the semantics of this system.
        """
        d_request   = {}
        d_ret       = {}
        b_status    = False
        hits        = 0
        for k, v in kwargs.items():
            if k == 'request':      d_request   = v
        d_meta      = d_request['meta']
        if 'saveDB' in d_meta.keys():
            self.dp.qprint("Saving DB...")
            self.within.DB_fileIO(cmd = 'save')

        self.dp.qprint('calling threaded_server.stop()')
        self.within.threaded_server.stopit()
        self.dp.qprint('called threaded_server.stop()')

        return {'d_ret':    d_ret,
                'status':   True}

    def t_get_process(self, *args, **kwargs):
        """
        Process the 'get' POST directive. This might appear counter-intuitive
        at first glance since the 'get' is the result of a REST POST, but is
        logically consistent within the semantics of this system.
        """
        d_request   = {}
        d_ret       = {}
        b_status    = False
        hits        = 0
        for k, v in kwargs.items():
            if k == 'request':      d_request   = v
        d_meta      = d_request['meta']
        str_path    = '/api/v1' + d_meta['path']
        d_ret       = self.DB_get(path  = str_path)
        return {'d_ret':    d_ret,
                'status':   True}

    def t_DBctl_process(self, *args, **kwargs):
        """
        Entry point for internal DB control processing.
        """
        tree_DB     = self.within.ptree
        d_request   = {}
        d_ret       = {}
        b_status    = False
        str_fileio  = self.within.str_fileio
        str_DBpath  = self.within.str_DBpath

        for k, v in kwargs.items():
            if k == 'request':      d_request   = v
        d_meta      = d_request['meta']

        if 'do'         in d_meta:  str_do          = d_meta['do']
        if 'dbpath'     in d_meta:  str_DBpath      = d_meta['dbpath']
        if 'fileio'     in d_meta:  str_fileio      = d_meta['fileio']

        self.within.DB_fileIO( 
                        cmd         = str_do,
                        fileio      = str_fileio,
                        dbpath      = str_DBpath,
                        db          = tree_DB
                        )

        # str_path    = '/api/v1' + str_DBpath
        d_ret       = self.DB_get(path  = str_DBpath)
        return {'d_ret':    d_ret,
                'status':   True}
        

    def t_fileiosetup_process(self, *args, **kwargs):
        """
        Setup a thread with a socket listener. Return listener address to client
        """
        self.dp.qprint("In fileiosetup process...")

        d_ret               = {}
        for k, v in kwargs.items():
            if k == 'request':      d_request   = v

        d_meta  = d_request['meta']

        d_ret['fileioIP']   = "%s" % self.within.str_IP
        d_ret['fileioport'] = "%s" % (int(self.within.str_port) + self.worker_id)
        d_ret['serveforever']=d_meta['serveforever']

        d_args              = {
                                'ip':    d_ret['fileioIP'],
                                'port':  d_ret['fileioport']
                               }

        server              = ThreadedHTTPServer((d_args['ip'], int(d_args['port'])), StoreHandler)
        server.setup(args   = d_args)
        self.dp.qprint("serveforever = %d" % d_meta['serveforever'])
        b_serveforever      = False
        if 'serveforever' in d_meta.keys():
            b_serveforever  = d_meta['serveforever']

        if b_serveforever:
            self.dp.qprint("about to serve_forever()...")
            server.serve_forever()
        else:
            self.dp.qprint("about to handle_request()...")
            server.handle_request()

        return {"d_ret":    d_ret,
                "status":   True}

    def job_state(self, *args, **kwargs):
        """

        Return a structure that can be further processed to determine the job's state.

        :param args:
        :param kwargs:
        :return:
        """

        self.dp.qprint("In job_state()...")

        d_request   = {}
        d_ret       = {}
        b_status    = False
        b_container = False
        hits        = 0
        for k, v in kwargs.items():
            if k == 'request':      d_request   = v

        d_search    = self.t_search_process(request = d_request)['d_ret']

        p   = self.within.ptree
        Ts  = C_stree()
        Te  = C_stree()
        for j in d_search.keys():
            d_j = d_search[j]
            for job in d_j.keys():
                str_pathStart       = '/api/v1/' + job + '/start'
                str_pathEnd         = '/api/v1/' + job + '/end'

                d_start             = self.DB_get(path = str_pathStart)
                d_end               = self.DB_get(path = str_pathEnd)
                Ts.initFromDict(d_start)
                Te.initFromDict(d_end)

                self.dp.qprint("Ts.cwd = %s " % Ts.cwd())
                self.dp.qprint(Ts)
                self.dp.qprint("Te.cwd = %s " % Te.cwd())
                self.dp.qprint(Te)

                l_subJobsStart      = []
                if Ts.cd('/%s/start' % job)['status']:
                    l_subJobsStart  = Ts.lstr_lsnode()
                    l_subJobsStart  = list(map(int, l_subJobsStart))
                    l_subJobsStart.sort()
                    self.dp.qprint("l_subJobsStart  (pre) = %s" % l_subJobsStart)
                    if len(l_subJobsStart) > 1: l_subJobsStart  = l_subJobsStart[:-1]

                l_subJobsEnd        = []
                if Te.cd('/%s/end' % job)['status']:
                    l_subJobsEnd    = Te.lstr_lsnode()
                    l_subJobsEnd    = list(map(int, l_subJobsEnd))
                    l_subJobsEnd.sort()
                    self.dp.qprint("l_subJobsEnd    (pre) = %s " % l_subJobsEnd)
                    if len(l_subJobsEnd) > 1: l_subJobsEnd    = l_subJobsEnd[:-1]

                self.dp.qprint("l_subJobsStart (post) = %s" % l_subJobsStart)
                self.dp.qprint("l_subJobsEnd   (post) = %s" % l_subJobsEnd)

                for j in l_subJobsStart:
                    l_subJobsStart[j]   = Ts.cat('/%s/start/%d/startInfo/%d/startTrigger' % \
                                                 (job, j, j))

                # jobsEnd behaviour can be slightly different to the jobStart, particularly if
                # the job being executed is killed -- sometimes recording the "death" event of
                # the job does not happen and the job indexing ends up missing several epochs:
                #
                #           l_subJobsStart  (pre) = [0, 1, 2, 3, 4]
                #           l_subJobsEnd    (pre) = [0, 1, 3, 4]
                #
                # to assure correct returncode lookup, we always parse the latest job epoch.

                latestJob       = 0
                if len(l_subJobsEnd):
                    latestJob   = l_subJobsEnd[-1]
                    for j in list(range(0, latestJob+1)):
                        l_subJobsEnd[j]         = Te.cat('/%s/end/%s/endInfo/%d/returncode' % (job, latestJob, j))
                T_container     = False

                if p.exists('container', path = '/%s' % job):
                    T_container = C_stree()
                    p.copy(startPath = '/%s/container' % (job), destination = T_container)
                    d_ret[str(hits)+'.container']   = {"jobRoot": job, "tree": dict(T_container.snode_root)}
                else:
                    d_ret[str(hits)+'.container']   = {"jobRoot": job, "tree":      None}
                d_ret[str(hits)+'.start']       = {"jobRoot": job, "startTrigger":  l_subJobsStart}
                d_ret[str(hits)+'.end']         = {"jobRoot": job, "returncode":    l_subJobsEnd}
                hits               += 1
        if not hits:
            d_ret['-1.start']       = {"jobRoot":   None, "startTrigger":   None}
            d_ret['-1.end']         = {"jobRoot":   None, "returncode":     None}
            d_ret['-1.container']   = {"jobRoot":   None, "tree":           None}
        else:
            b_status            = True
        return {"hits":         hits,
                "d_ret":        d_ret,
                "status":       b_status}

    def t_done_process(self, *args, **kwargs):
        """

        Check if the job corresponding to the search pattern is "done".
        :param args:
        :param kwargs:
        :return:
        """

        self.dp.qprint("In done process...")

        return self.job_state(*args, **kwargs)

    def t_status_process(self, *args, **kwargs):
        """

        This method is the main (threaded) entry point for returning
        information on the status of jobs (both active and historical)
        that have been (or are currently) managed by pman.

        Originally, the concept of "job" only extended to a command 
        line process spawned off on the underlying shell. With time,
        however, this concept expanded to encompass processes that
        are containerized.

        While most (if not all) of the use of pman currently is to 
        handle containerized compute, the status determination logic
        still retains the ability to query simple spawned jobs.

        The determination about whether or not a job has been 
        containerized is quite simple -- a token in the internal
        job "state" memory structure (the main pman stree "DB")
        is checked -- this initial chunk of data is returned by a
        call to self.job_state() which delivers a dictionary
        representation of the jobRoot in the DB tree.

        :param args:
        :param kwargs:
        :return: dictionary of components defining job state.
        """
        self.dp.qprint("In status process...")
        status = logs = currentState = ''
        if self.container_env == 'openshift':
            self.dp.qprint('Processing openshift....')
            try:
                d_containerStatus       =   self.t_status_process_openshift(*args, **kwargs)
                status                  =   d_containerStatus['status']
                logs                    =   d_containerStatus['logs']
                currentState            =   d_containerStatus['currentState']
            except Exception as e:
                if e.reason == 'Not Found':
                    status = logs = currentState = e.reason
                else:
                    raise e
            
            d_ret = {
                'status':   status,
                'logs':     logs,         
                'currentState': currentState
            }
            return {
                    "d_ret":    str(d_ret),
                    "status":   str(currentState)
            }
        
        else:

            d_state     = self.job_state(*args, **kwargs)
            # {
            #     "hits":         hits,
            #     "d_ret":        
            #         [<index>+'.container']   = {
            #             "jobRoot": job, "tree": dict(T_container.snode_root)
            #         },
            #     "status":       b_status
            # }

            d_ret       = d_state['d_ret']
            b_status    = d_state['status']

            d_keys      = d_ret.items()
            l_status    = []
            l_logs      = []

            #
            # The d_ret keys consist of groups of
            #
            #       *.start
            #       *.end
            #       *.container
            #
            # thus the loop grouping is number of items / 3
            #
            if '0.start' in d_ret:
                for i in range(0, int(len(d_keys)/3)):
                    try:
                        b_startEvent    = d_ret['%s.start'  % str(i)]['startTrigger'][0]
                    except:
                        b_startEvent    = False
                    try:
                        endcode     = d_ret['%s.end'    % str(i)]['returncode'][0]
                    except:
                        endcode     = None

                    # Was this a containerized job?
                    found_container = False
                    container_path = '%s.%s' % (str(i), 'container')
                    if container_path in d_state['d_ret']           and \
                        d_state['d_ret'][container_path]['tree']    and \
                        b_startEvent:

                        kwargs['d_state']   = d_state
                        kwargs['hitIndex']  = str(i)

                        str_methodSuffix = None
                        if self.container_env == 'swarm':
                            # append suffix _container to redirect to container function
                            str_methodSuffix    = 'container'
                        d_containerStatus       = eval("self.t_status_process_%s(*args, **kwargs)" % str_methodSuffix)
                        # d_ret {
                        #     'status':         d_ret['status'],              # bool
                        #     'logs':           str_logs,                     # logs from app in container
                        #     'currentState':   d_ret['d_process']['state']   # string of 'finishedSuccessfully' etc
                        # }

                        l_status.append(d_containerStatus['currentState'])
                        l_logs.append(d_containerStatus['logs'])
                        found_container = True

                    # The case for non-containerized jobs
                    if not found_container:
                        if endcode is None and not b_startEvent:
                            l_status.append('notstarted')
                        if endcode is None and b_startEvent:
                            l_status.append('started')
                        if not endcode and b_startEvent and type(endcode) is int:
                            l_status.append('finishedSuccessfully')
                        if endcode and b_startEvent:
                            l_status.append('finishedWithError')

                    self.dp.qprint('b_startEvent = %d' % b_startEvent)
                    self.dp.qprint(endcode)
                    self.dp.qprint('l_status = %s' % l_status)

        d_ret['l_status']   = l_status
        d_ret['l_logs']     = l_logs

        return {
                "d_ret":    d_ret,
                "status":   b_status
                }

    def DB_store(self, data, str_path, str_file):
        """
        In the DB memory tree, simply stores <data> to a location called 
        <str_path> and a file called <str_file>.

        Explicitly separating <str_path> and <str_file> is just for 
        expedience in checking up on path validity in the DB memory tree.

        This method also triggers a DB save event.

        """
        if not self.within.ptree.exists(str_file, path = str_path):
            self.within.ptree.touch('%s/%s' % (str_path, str_file), data)
            # Save DB state...
            self.within.DB_fileIO(cmd = 'save')

    def t_status_process_container_stateObject(self, *args, **kwargs):
        """
        This method processes the swarm manager state object and, if 
        necessary, shuts down the service from the swarm scheduler.

        PRECONDITIONS:
        o   This method should only ever be called by t_status_process_container().

        POSTCONDITIONS:
        o   A string denoting the current state is returned.
        o   If state is complete and service still running, save state object to
            tree and remove service.
        o   Store the state object and logs in the internal DB tree!

        """

        def service_exists(str_serviceName):
            """
            Returns a bool:
                - True:     <str_serviceName> does exist
                - False:    <str_serviceName> does not exist
            """
            b_exists        = False
            client          = docker.from_env()
            try:
                service     = client.services.get(str_serviceName)
                b_exists    = True
            except:
                b_exists    = False
            return b_exists

        def service_shutDown_check():
            """
            Verifies that a docker service can be shutdown.

            Should multiple jobs have been scheduled temporally serially
            with the same jid/serviceName, then the actual service can
            only be shut down once all identical jobs have had their
            state stored.

            Returns bool:
                - True:     can shut down
                - False:    cannot shut down
            """
            ret = False
            if int(str_hitIndex) < int(d_jobState['hits'])-1:
                ret     = False
            else:
                ret      = True
            return ret

        def service_shutDown(d_serviceInfo):
            """
            Shut down a service
            """
            client          = docker.from_env()
            str_cmdShutDown = '%s --remove %s' % \
                (d_serviceInfo['managerApp'], d_serviceInfo['serviceName'])
            byte_str        = client.containers.run(
                                    '%s' % d_serviceInfo['managerImage'],
                                    str_cmdShutDown,
                                    volumes = {
                                                '/var/run/docker.sock': 
                                                        {
                                                            'bind': '/var/run/docker.sock',
                                                            'mode': 'rw'
                                                        }
                                                },
                                    remove=True)
            return byte_str

        d_serviceState      = None
        d_jobState          = None
        str_hitIndex        = "0"
        str_logs            = ""
        for k,v in kwargs.items():
            if k == 'jobState':         d_jobState      = v
            if k == 'serviceState':     d_serviceState  = v
            if k == 'hitIndex':         str_hitIndex    = v
            if k == 'logs':             str_logs        = v

        if d_serviceState:

            d_ret    = self.t_status_process_state(**kwargs)
            # d_ret {
            #             'currentState':   str_currentState,
            #             'removeJob':      b_removeJob,
            #             'status':         True
            #         }

            if d_ret['removeJob']:
                str_jobRoot = d_jobState['d_ret']['%s.container' % (str_hitIndex)]['jobRoot']
                self.within.ptree.cd('/%s/container' % str_jobRoot)
                d_serviceInfo       = {
                                        'serviceName':  self.within.ptree.cat('manager/env/serviceName'),
                                        'managerImage': self.within.ptree.cat('manager/image'),
                                        'managerApp':   self.within.ptree.cat('manager/app')
                                    }
                if service_exists(d_serviceInfo['serviceName']):
                    service_shutDown(d_serviceInfo)

        return {
            'status':       True,
            'd_process':    d_ret
            }

    def t_status_process_container(self, *args, **kwargs):
        """
        Execution should only reach this method for "container"ized jobs
        status determination!

        The 'd_state' contains a dictionary representation of the container
        DB tree.

        PRECONDITIONS:
        o   Only call this method if a container structure exists
            in the relevant job tree!

        POSTCONDITIONS:
        o   If the job is completed, then shutdown the container cluster
            service.
        o   The memory container tree contains a dictionary called 'state'
            that is the state returned by the container service, as well as
            a file called 'logs' that is the stdout/stderr generated by the
            job as it ran in the container.
        """
        d_state         = None
        str_jobRoot     = ''
        str_hitIndex    = "0"
        str_logs        = ''

        for k,v in kwargs.items():
            if k == 'd_state':  d_state         = v
            if k == 'hitIndex': str_hitIndex    = v

        self.dp.qprint('checking on status using container...')
        str_jobRoot         = d_state['d_ret']['%s.container' % str_hitIndex]['jobRoot']
        self.within.ptree.cd('/%s/container' % str_jobRoot)
        str_serviceName     = self.within.ptree.cat('manager/env/serviceName')
        str_managerImage    = self.within.ptree.cat('manager/image')
        str_managerApp      = self.within.ptree.cat('manager/app')

        # Check if the state of the container service has been recorded to the data tree
        if self.within.ptree.exists('state', path = '/%s/container' % str_jobRoot):
            # If this exists, then the job has actually completed and 
            # its state has been recorded in the data tree. We can simply 'cat'
            # the state from this memory dictionary
            d_serviceState  = self.within.ptree.cat('/%s/container/state' % str_jobRoot)
            if self.within.ptree.exists('logs', path = '/%s/container' % str_jobRoot):
                # The job has actually completed and its logs are recorded in the data tree
                str_logs     = self.within.ptree.cat('/%s/container/logs' % str_jobRoot)
        else:
            # Here, the manager has not been queried yet about the state of
            # the service. We need to ask the container service for this 
            # state, and then record the state (and logs) in the memory
            # tree, and then "shut down" the service.
            client = docker.from_env()

            # Get the state of the service...
            str_cmdManager  = '%s --state %s' % \
                              (str_managerApp, str_serviceName)
            byte_str        = client.containers.run(
                    '%s' % str_managerImage,
                    str_cmdManager,
                    volumes =   {
                                '/var/run/docker.sock': 
                                    {
                                        'bind': '/var/run/docker.sock',
                                        'mode': 'rw'
                                    }
                                },
                                remove  = True)
            d_serviceState  = json.loads(byte_str.decode())
            # Now, parse for the logs of the actual container run by the service:
            # NB: This has only really tested/used on swarm!!
            b_containerIDFound = True
            try:
                str_contID  = d_serviceState['Status']['ContainerStatus']['ContainerID']
                b_containerIDFound  = True
            except:
                b_containerIDFound  = False
            if b_containerIDFound:
                container   = client.containers.get(str_contID)
                str_logs    = container.logs()
                str_logs    = str_logs.decode()

        d_ret = self.t_status_process_container_stateObject( 
                                    hitIndex        = str_hitIndex,
                                    jobState        = d_state,
                                    serviceState    = d_serviceState,
                                    logs            = str_logs
                                    )
        # d_ret {
        #            'status':      bool,
        #             d_process: {
        #               'currentState':     str_currentState,
        #               'removeJob':        b_removeJob,
        #               'status':           True
        #             }
        #       }

        return {
            'status':           d_ret['status'],
            'logs':             str_logs,
            'currentState':     d_ret['d_process']['currentState']
        }

    def t_status_process_openshift(self, *args, **kwargs):
        """
        Determine the status of a job scheduled using the openshift manager.
        # TODO: @husky-parul: change these comments

        PRECONDITIONS:
        o   Only call this method if a container structure exists
            in the relevant job tree!

        POSTCONDITIONS:
        o   If the job is completed, then shutdown the container cluster
            service.
        """
        self.dp.qprint('Processing job status within t_status_process_openshift ... ')
        str_logs    = ''
        # Get job-id from request
        for k,v in kwargs.items():
            if k == 'request' and v['action'] == 'status' :     jid = v['meta']['value']
        
        # Query OpenShift API to get job state and logs for all worker pods 
        d_json  = self.get_openshift_manager().state(jid)

        if d_json['Status']['Message'] == 'finished':
            pod_names = self.get_openshift_manager().get_pod_names_in_job(jid)
            for _, pod_name in enumerate(pod_names):
                str_logs += self.get_openshift_manager().get_job_pod_logs(pod_name)
        else:
            str_logs = d_json['Status']['Message']

        status  = str(d_json['Status'])
        currentState =  d_json['Status']['Message']
    
        return {
            'status':           status,
            'logs':             str_logs,
            'currentState':     currentState
        }

    def t_status_process_openshift_stateObject(self, *args, **kwargs):
        """
        Process the actual JSON container return object on service
        state.

        PRECONDITIONS:
        o   This method should only ever be called by t_status_process_openshift().

        POSTCONDITIONS:
        o   A string denoting the current state is returned.

        """

        def job_exists(jid):
            """
            Returns a bool:
                - True:     <jid> does exist
                - False:    <jid> does not exist
            """
            b_exists        = False
            try:
                job         = self.get_openshift_manager().get_job(jid)
                b_exists    = True
            except:
                b_exists    = False
            return b_exists

        def job_shutDown(d_serviceInfo):
            """
            Shut down a service
            """
            try:
                self.get_openshift_manager().remove_pvc(jid)
                self.get_openshift_manager().remove_job(jid)
            except Exception as err:
                self.dp.qprint("Error deleting pvc/job:", err)

        d_serviceState      = None
        d_jobState          = None
        str_hitIndex        = "0"
        str_logs            = ""
        d_ret               = {}

        for k,v in kwargs.items():
            if k == 'jobState':         d_jobState      = v
            if k == 'serviceState':     d_serviceState  = v
            if k == 'hitIndex':         str_hitIndex    = v
            if k == 'logs':             str_logs        = v
        if d_serviceState:
            d_ret = self.t_status_process_state(**kwargs)
            if d_ret['removeJob']:
                str_jobRoot = d_jobState['d_ret']['%s.container' % (str_hitIndex)]['jobRoot']
                self.within.ptree.cd('/%s' % str_jobRoot)
                jid = self.within.ptree.cat('jid')
                if job_exists(jid):
                    job_shutDown(jid)
        return {
            'status':       True,
            'd_process':    d_ret
        }

    def get_openshift_manager(self):
        if not self.openshiftmgr:
            self.openshiftmgr = OpenShiftManager()
        return self.openshiftmgr

    def t_status_process_state(self, *args, **kwargs):
        """
        This method processes the swarm state object to make the 
        final determination on a job's state and print out container
        job state and logs.

        It also returns a signal to the caller to trigger the removal
        of the job from the swarm scheduler if the job has completed.
        """

        def debug_print(    str_jobRoot, 
                            d_serviceState, 
                            str_currentState, 
                            str_logs
                        ):
            """
            Simply print some useful debug info.
            """
            l_commsNorm = ['rx',    'rx',    'tx']
            l_commsErr  = ['error', 'error', 'error']
            l_comms     = l_commsNorm
            if str_currentState == 'finishedWithError':
                l_comms = l_commsErr
            self.dp.qprint('\njobRoot %s\n-->%s<--...' % \
                                    (str_jobRoot, 
                                    str_currentState),
                                    comms = l_comms[0])
            self.dp.qprint('\n%s' % self.df_print(d_serviceState), 
                                    comms = l_comms[1])
            self.dp.qprint('\njob logs:\n%s' % str_logs,
                                    comms = l_comms[2])

        d_serviceState      = {}
        d_jobState          = {}
        hitIndex            = 0
        str_logs            = ""
        b_status            = False
        str_currentState    = "undefined"

        for k,v in kwargs.items():
            if k == 'jobState':         d_jobState          = v
            if k == 'serviceState':     d_serviceState      = v
            if k == 'hitIndex':         str_hitIndex        = v
            if k == 'logs':             str_logs            = v

        b_removeJob = False
        str_jobRoot = d_jobState['d_ret']['%s.container' % (hitIndex)]['jobRoot']
        str_state   = d_serviceState['Status']['State']
        str_message = d_serviceState['Status']['Message']
        if str_state == 'running' and str_message == 'started':
            str_currentState    = 'started'
            debug_print(str_jobRoot, d_serviceState, str_currentState, str_logs)
            b_status    = True
        else:
            self.DB_store(d_serviceState,   '/%s/container' % (str_jobRoot), 'state')
            self.DB_store(str_logs,         '/%s/container' % (str_jobRoot), 'logs')
            b_removeJob   = True
            if str_state == 'failed'        and str_message == 'started':
                str_currentState    = 'finishedWithError'
                debug_print(str_jobRoot, d_serviceState, str_currentState, str_logs)
            elif str_state == 'complete'    and str_message == 'finished':
                str_currentState    = 'finishedSuccessfully'
                debug_print(str_jobRoot, d_serviceState, str_currentState, str_logs)
            b_status = True
        self.DB_store(str_currentState, '/%s/container' % (str_jobRoot), 'currentState')
        if str_currentState == 'undefined':
            self.dp.qprint('The state of the job is undefined!', comms = 'error')
            self.dp.qprint('This typically means that the scheduler rejected the job.', comms = 'error')
            self.dp.qprint('jobRoot = %s' % str_jobRoot, comms = 'error')
        return {
                    'currentState':     str_currentState,
                    'removeJob':        b_removeJob,
                    'status':           b_status
                }
    
    def t_hello_process(self, *args, **kwargs):
        """

        The 'hello' action is merely to 'speak' with the server. The server
        can return current date/time, echo back a string, query the startup
        command line args, etc.

        This method is a simple means of checking if the server is "up" and
        running.

        :param args:
        :param kwargs:
        :return:
        """

        self.dp.qprint("In hello process...")
        b_status            = False
        d_ret               = {}
        for k, v in kwargs.items():
            if k == 'request':      d_request   = v

        d_meta  = d_request['meta']
        if 'askAbout' in d_meta.keys():
            str_askAbout    = d_meta['askAbout']
            d_ret['name']       = self.within.str_name
            d_ret['version']    = self.within.str_version
            if str_askAbout == 'timestamp':
                str_timeStamp   = datetime.datetime.today().strftime('%Y%m%d%H%M%S.%f')
                d_ret['timestamp']              = {}
                d_ret['timestamp']['now']       = str_timeStamp
                b_status                        = True
            if str_askAbout == 'sysinfo':
                d_ret['sysinfo']                = {}
                d_ret['sysinfo']['system']      = platform.system()
                d_ret['sysinfo']['machine']     = platform.machine()
                d_ret['sysinfo']['platform']    = platform.platform()
                d_ret['sysinfo']['uname']       = platform.uname()
                d_ret['sysinfo']['version']     = platform.version()
                d_ret['sysinfo']['memory']      = psutil.virtual_memory()
                d_ret['sysinfo']['cpucount']    = multiprocessing.cpu_count()
                d_ret['sysinfo']['loadavg']     = os.getloadavg()
                d_ret['sysinfo']['cpu_percent'] = psutil.cpu_percent()
                d_ret['sysinfo']['hostname']    = socket.gethostname()
                d_ret['sysinfo']['inet']        = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
                b_status                        = True
            if str_askAbout == 'echoBack':
                d_ret['echoBack']               = {}
                d_ret['echoBack']['msg']        = d_meta['echoBack']
                b_status                        = True

        return { 'd_ret':   d_ret,
                 'status':  b_status}

    def t_run_process(self, *args, **kwargs):
        """
        Main job handler -- this is in turn a thread spawned from the
        parent listener thread.
        By being threaded, the client http caller gets an immediate
        response without needing to wait on the jobs actually running
        to completion.
        """

        str_cmd             = ""
        d_request           = {}
        d_meta              = {}
        d_Tcontainer        = {}

        for k,v in kwargs.items():
            if k == 'request':      d_request       = v
            if k == 'treeList':     d_Tcontainer    = v

        d_meta          = d_request['meta']

        if d_meta:
            self.jid    = d_meta['jid']
            self.auid   = d_meta['auid']
            str_cmd     = d_meta['cmd']

        if isinstance(self.jid, int):
            self.jid    = str(self.jid)

        self.dp.qprint("spawning and starting poller thread")

        # Start the 'poller' worker
        self.poller  = Poller(cmd           = str_cmd,
                              debugToFile   = self.b_debugToFile,
                              verbosity     = self.verbosity,
                              debugFile     = self.str_debugFile)
        self.poller.start()

        str_timeStamp       = datetime.datetime.today().strftime('%Y%m%d%H%M%S.%f')
        str_uuid            = uuid.uuid4()
        str_dir             = '%s_%s' % (str_timeStamp, str_uuid)
        self.str_jobRootDir = str_dir

        b_jobsAllDone       = False
        p                   = self.within.ptree

        p.cd('/')
        p.mkcd(str_dir)

        if d_Tcontainer:
            # Save the trees in this list to the DB...
            for name,tree in d_Tcontainer.items():
                p.mkcd(name)
                tree.copy(startPath = '/', destination = p, pathDiskRoot = '/%s/%s' % (str_dir, name))
                p.cd('/%s' % str_dir)

        p.touch('d_meta',       json.dumps(d_meta))
        for detailKey in ['cmdMgr', 'cmdMgr_byte_str']:
            if detailKey in d_meta.keys():
                p.touch(detailKey,   json.dumps(d_meta[detailKey]))
            
        p.touch('cmd',          str_cmd)
        if len(self.auid):
            p.touch('auid',     self.auid)
        if len(self.jid):
            p.touch('jid',      self.jid)

        p.mkdir('start')
        p.mkdir('end')

        jobCount        = 0
        p.touch('jobCount',     jobCount)

        while not b_jobsAllDone:
            try:
                b_jobsAllDone   = self.poller.queueAllDone.get_nowait()
            except queue.Empty:
                self.dp.qprint('Waiting on start job info')
                d_startInfo     = self.poller.queueStart.get()
                str_startDir    = '/%s/start/%d' % (self.str_jobRootDir, jobCount)
                p.mkdir(str_startDir)
                p.cd(str_startDir)
                p.touch('startInfo', d_startInfo.copy())
                p.touch('/%s/startInfo' % str_dir, d_startInfo.copy())

                self.dp.qprint('Waiting on end job info')
                d_endInfo       = self.poller.queueEnd.get()
                str_endDir      = '/%s/end/%d' % (self.str_jobRootDir, jobCount)
                p.mkdir(str_endDir)
                p.cd(str_endDir)
                p.touch('endInfo', d_endInfo.copy())
                p.touch('/%s/endInfo' % str_dir,    d_endInfo.copy())

                p.touch('/%s/jobCount' % str_dir,   jobCount)
                jobCount        += 1
        self.dp.qprint('All jobs processed.')

        # Save DB state...
        self.within.ptree           = p
        self.within.DB_fileIO(cmd   = 'save')

    def FScomponent_pollExists(self, *args, **kwargs):
        """
        This method polls access to a file system component (a file or 
        directory). Its purpose is to wait for possible transients when
        an asynchronous process creates a file system component that some
        method in pmans wants to access.
        """
        maxLoopTries    = 20
        currentLoop     = 1
        str_dir         = ''

        for k, v in kwargs.items():
            if k == 'maxLoopTries': maxLoopTries    = v
            if k == 'dir':          str_dir         = v

        b_exists        = False
        b_checkAgain    = True
        while b_checkAgain:
            self.dp.qprint('Checking if %s exists (currentLoop: %d)...' % (str_dir, currentLoop), comms = 'rx')
            b_exists    = os.path.exists(str_dir)
            if b_exists:
                b_checkAgain    = False
                self.dp.qprint('Dir exists!', comms = 'rx')
            else:
                self.dp.qprint('Dir does not exist! Sleeping...', comms = 'error')
                time.sleep(2)
            currentLoop += 1
            if currentLoop == maxLoopTries:
                b_checkAgain = False
        return b_exists

    def t_run_process_container(self, *args, **kwargs):
        """
        A threaded run method specialized to handling containerized managers and targets.

        NOTE: If 'serviceName' is not specified/present, then this defaults to the 'jid'
        value and is in fact the default behaviour.

        Typical JSON d_request:

        {   "action": "run",
            "meta":  {
                "cmd":      "$execshell $selfpath/$selfexec --prefix test- --sleepLength 0 /share/incoming /share/outgoing",
                "auid":     "rudolphpienaar",
                "jid":      "simpledsapp-1",
                "threaded": true,
                "container":   {
                        "target": {
                            "image":        "fnndsc/pl-simpledsapp"
                        },
                        "manager": {
                            "image":        "fnndsc/swarm",
                            "app":          "swarm.py",
                            "env":  {
                                "shareDir":     "/home/tmp/share",
                                "serviceType":  "docker",
                                "serviceName":  "testService"
                            }
                        }
                }
            }
        }

        """

        str_cmd             = ""
        str_shareDir        = ""
        str_serviceName     = ""
        d_request           = {}
        d_meta              = {}
        d_container         = {}
        d_image             = {}
        d_manager           = {}
        d_env               = {}

        self.dp.qprint('Processing swarm-type job...')

        for k,v in kwargs.items():
            if k == 'request': d_request    = v

        d_meta          = d_request['meta']

        if d_meta:
            self.jid            = d_meta['jid']
            self.auid           = d_meta['auid']
            str_cmd             = d_meta['cmd']
            str_serviceName     = self.jid

            if 'container' in d_meta.keys():
                d_container                 = d_meta['container']
                d_target                    = d_container['target']
                str_targetImage             = d_target['image']

                d_manager                   = d_container['manager']
                str_managerImage            = d_manager['image']
                str_managerApp              = d_manager['app']

                d_env                       = d_manager['env']
                if 'shareDir' in d_env.keys():
                    str_shareDir            = d_env['shareDir']
                    # Remove trailing '/' if it exists in shareDir
                    str_shareDir            = str_shareDir.rstrip('/')
                    b_exists                = self.FScomponent_pollExists(dir = str_shareDir)
                    if not b_exists:
                        self.dp.qprint('Could not access volume mapped share dir: %s' % str_shareDir, comms = 'error')

                if 'STOREBASE' in os.environ:
                    str_storeBase           = os.environ['STOREBASE']
                    (str_origBase, str_key) = os.path.split(str_shareDir)
                    self.dp.qprint('Overriding shareDir (orig): %s' % str_shareDir)
                    str_shareDir            = os.path.join(str_storeBase, str_key)
                    self.dp.qprint('Overriding shareDir (new):  %s' % str_shareDir)
                if 'serviceName' in d_env.keys():
                    str_serviceName         = d_env['serviceName']
                else:
                    d_env['serviceName']    = str_serviceName

            # First, attach to the docker daemon...
            client = docker.from_env()

            str_cmdLine     = str_cmd
            str_cmdManager  = '%s -s %s -m %s -i %s -p none -c "%s"' % \
                              (str_managerApp, str_serviceName, str_shareDir, str_targetImage, str_cmdLine)
            try:
                byte_str    = client.containers.run('%s' % str_managerImage,
                                             str_cmdManager,
                                             volumes = {'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}},
                                             remove  = True)
            except Exception as e:
                # An exception here most likely occurs due to a serviceName collision.
                # Solution is to stop the service and retry.
                str_e   = '%s' % e
                print(str_e)

            d_meta['cmdMgr']            = '%s %s' % (str_managerImage, str_cmdManager)
            d_meta['cmdMrg_byte_str']   = str(byte_str, 'utf-8')

            # Call the "parent" method -- reset the cmdLine to an "echo"
            # and create an stree off the 'container' dictionary to store
            # in the pman DB entry.
            d_meta['cmd']   = 'echo "%s"' % str_cmd
            T_container     = C_stree()
            T_container.initFromDict(d_container)
            d_Tcontainer    = {'container': T_container}
            self.t_run_process(request  = d_request,
                               treeList = d_Tcontainer)
            self.dp.qprint('Returning from swarm-type job...')

    def t_run_process_openshift(self, *args, **kwargs):
        """
        A threaded run method specialized for handling openshift
        """

        str_cmd             = ""
        d_request           = {}
        d_meta              = {}
        d_container         = {}
        d_image             = {}

        self.dp.qprint('Processing openshift job...')

        for k,v in kwargs.items():
            if k == 'request': d_request    = v

        d_meta          = d_request['meta']

        if d_meta:
            self.jid            = d_meta['jid']
            self.auid           = d_meta['auid']
            str_cmd             = d_meta['cmd']

            str_arr = str_cmd.split()
            incoming_dir = str_arr[len(str_arr)-2]
            outgoing_dir = str_arr[len(str_arr)-1]

            if 'number_of_workers' in d_meta:
                number_of_workers = d_meta['number_of_workers']
            else:
                number_of_workers = '1'
            if 'cpu_limit' in d_meta:
                cpu_limit = d_meta['cpu_limit']
            else:
                cpu_limit = '2000m'
            if 'memory_limit' in d_meta:
                memory_limit = d_meta['memory_limit']
            else:
                memory_limit = '1024Mi'

            if 'gpu_limit' in d_meta:
                gpu_limit = d_meta['gpu_limit']
            else:
                gpu_limit = 0

            if 'container' in d_meta:
                d_container                 = d_meta['container']
                d_target                    = d_container['target']
                str_targetImage             = d_target['image']

            # Create the Persistent Volume Claim
            self.dp.qprint("Create PVC")
            try:
                self.get_openshift_manager().create_pvc(self.jid)
            except Exception as err:
                self.dp.qprint("Failed to create PVC:", err)

            str_cmdLine = str_cmd
            self.get_openshift_manager().schedule(str_targetImage, str_cmdLine, self.jid,
                                                  number_of_workers, cpu_limit, memory_limit, gpu_limit,
                                                  incoming_dir, outgoing_dir)

            self.dp.qprint('Returning from openshift job...')

    def json_filePart_get(self, **kwargs):
        """
        If the requested path is *within* a json "file" on the
        DB, then we need to find the file, and map the relevant
        path to components in that file.
        """

    def DB_get(self, **kwargs):
        """
        Returns part of the DB tree based on path spec in the URL
        """

        r           = C_stree()
        p           = self.within.ptree

        pcwd        = p.cwd()
        str_URLpath = "/api/v1/"
        for k,v in kwargs.items():
            if k == 'path':     str_URLpath = v

        str_path    = '/' + '/'.join(str_URLpath.split('/')[3:])

        self.dp.qprint("path = %s" % str_path)

        if str_path == '/':
            # If root node, only return list of jobs
            l_rootdir = p.lstr_lsnode(str_path)
            r.mknode(l_rootdir)
        else:
            # Here is a hidden behaviour. If the 'root' dir starts
            # with an underscore, then replace that component of
            # the path with the actual name in list order.
            # This is simply a short hand way to access indexed
            # offsets.

            l_path  = str_path.split('/')
            jobID   = l_path[1]
            # Does the jobID start with an underscore?
            if jobID[0] == '_':
                jobOffset   = jobID[1:]
                l_rootdir   = list(p.lstr_lsnode('/'))
                self.dp.qprint('jobOffset = %s' % jobOffset)
                self.dp.qprint(l_rootdir)
                try:
                    actualJob   = l_rootdir[int(jobOffset)]
                except:
                    return False
                l_path[1]   = actualJob
                str_path    = '/'.join(l_path)

            r.mkdir(str_path)
            r.cd(str_path)
            r.cd('../')
            # if not r.graft(p, str_path):
            if not p.copy(startPath = str_path, destination = r)['status']:
                # We are probably trying to access a file...
                # First, remove the erroneous path in the return DB
                r.rm(str_path)

                # Now, we need to find the "file", parse the json layer
                # and save...
                n                   = 0
                contents            = p.cat(str_path)
                str_pathFile        = str_path
                l_path              = str_path.split('/')
                totalPathLen        = len(l_path)
                l_pathFile          = []
                while not contents and -1*n < totalPathLen:
                    n               -= 1
                    str_pathFile    = '/'.join(str_path.split('/')[0:n])
                    contents        = p.cat(str_pathFile)
                    l_pathFile.append(l_path[n])

                if contents and n<0:
                    l_pathFile      = l_pathFile[::-1]
                    str_access      = ""
                    for l in l_pathFile:
                        str_access += "['%s']" % l
                    self.dp.qprint('str_access = %s' % str_access)
                    try:
                        contents        = eval('contents%s' % str_access)
                    except:
                        contents        = False

                r.touch(str_path, contents)

        p.cd(pcwd)

        self.dp.qprint(r)
        # self.dp.qprint(dict(r.snode_root))
        self.dp.qprint(self.pp.pformat(dict(r.snode_root)).strip())
        return dict(r.snode_root)

        # return r

    def process(self, request, **kwargs):
        """ Process the message from remote client

        In some philosophical respects, this process() method in fact implements
        REST-like API of its own.

        """
        if len(request):
            REST_header     = ""
            REST_verb       = ""
            str_path        = ""
            json_payload    = ""

            self.dp.qprint("Listener ID - %s: process() - handling request" % (self.worker_id))

            now             = datetime.datetime.today()
            str_timeStamp   = now.strftime('%Y-%m-%d %H:%M:%S.%f')
            self.dp.qprint(Colors.YELLOW)
            self.dp.qprint("***********************************************")
            self.dp.qprint("***********************************************")
            self.dp.qprint("%s incoming data stream" % (str_timeStamp) )
            self.dp.qprint("***********************************************")
            self.dp.qprint("len = %d" % len(request))
            self.dp.qprint("***********************************************")
            self.dp.qprint(Colors.CYAN + "%s\n" % (request.decode()) + Colors.YELLOW)
            self.dp.qprint("***********************************************" + Colors.NO_COLOUR)
            l_raw           = request.decode().split('\n')
            FORMtype        = l_raw[0].split('/')[0]

            self.dp.qprint('Request = ...')
            self.dp.qprint(l_raw)
            REST_header             = l_raw[0]
            REST_verb               = REST_header.split()[0]
            str_path                = REST_header.split()[1]
            json_payload            = l_raw[-1]

            # remove trailing '/' if any on path
            if str_path[-1]         == '/': str_path = str_path[0:-1]

            d_ret                   = {'status': False,
                                       'RESTheader': REST_header,
                                       'RESTverb': REST_verb,
                                       'action': "",
                                       'path': str_path,
                                       'receivedByServer': l_raw}

            self.dp.qprint("Using token authentication: %s" % self.b_tokenAuth)
            if (not self.b_tokenAuth) or self.authModule.authorizeClientRequest(request.decode())[0]:
                self.dp.qprint("Request authorized")
                if REST_verb == 'GET':
                    d_ret['GET']    = self.DB_get(path = str_path)
                    d_ret['status'] = True
                self.dp.qprint('json_payload = %s' % self.pp.pformat(json_payload).strip())
                d_ret['client_json_payload']    = json_payload
                d_ret['client_json_len']        = len(json_payload)
                if len(json_payload):
                    d_payload           = json.loads(json_payload)
                    d_request           = d_payload['payload']
                    payload_verb        = d_request['action']
                    if 'meta' in d_request.keys():
                        d_meta          = d_request['meta']
                    d_ret['payloadsize']= len(json_payload)

                    if payload_verb == 'quit':
                        self.dp.qprint('Shutting down server...')
                        d_ret['status'] = True

                    if payload_verb == 'run' and REST_verb == 'PUT':
                        d_ret['action']     = payload_verb
                        self.processPUT(    request     = d_request)
                        d_ret['status'] = True

                    if REST_verb == 'POST':
                        self.processPOST(   request = d_request,
                                            ret     = d_ret)
            else:
                self.dp.qprint("Request unauthorized")
            return d_ret
        else:
            return False

    def methodName_parse(self, **kwargs):
        """
        Construct the processing method name (string) by parsing the
        d_meta dictionary.
        """
        d_meta              = {}
        str_method          = ""        # The main 'parent' method
        str_methodSuffix    = ""        # A possible 'subclass' specialization

        for k,v in kwargs.items():
            if k == 'request': d_request= v
        payload_verb        = d_request['action']

        if 'meta' in d_request.keys():
            d_meta          = d_request['meta']

        if 'container' in d_meta.keys():
            if self.container_env == 'openshift':
                # append suffix _openshift to redirect to openshift function
                str_methodSuffix    = '_openshift'
            elif self.container_env == 'swarm':
                # append suffix _container to redirect to container function
                str_methodSuffix    = '_container'

        str_method  = 't_%s_process%s' % (payload_verb, str_methodSuffix)
        return str_method

    def processPOST(self, **kwargs):
        """
         Dispatcher for POST
        """

        for k,v in kwargs.items():
            if k == 'request':  d_request   = v
            if k == 'ret':      d_ret       = v

        payload_verb        = d_request['action']
        if 'meta' in d_request.keys():
            d_meta          = d_request['meta']

        d_ret['action'] = payload_verb
        d_ret['meta']   = d_meta

        b_threaded      = False
        if 'threaded' in d_meta.keys():
            b_threaded  = d_meta['threaded']

        if b_threaded:
            self.dp.qprint("Will process request in new thread.")
            pf_method   = None
            str_method  = self.methodName_parse(request = d_request)
            # str_method  = 't_%s_process' % payload_verb
            try:
                pf_method  = getattr(self, str_method)
            except AttributeError:
                raise NotImplementedError("Class `{}` does not implement `{}`".format(pman.__class__.__name__, str_method))

            t_process           = threading.Thread(     target      = pf_method,
                                                        args        = (),
                                                        kwargs      = kwargs)
            t_process.start()
            time.sleep(0.1)
            # if payload_verb == 'run':
            #     d_ret['jobRootDir'] = self.str_jobRootDir
            d_ret['status']     = True
        else:
            self.dp.qprint("Will process request in current thread.")
            d_done              = eval("self.t_%s_process(request = d_request)" % payload_verb)
            try:
                d_ret['d_ret']      = d_done["d_ret"]
                d_ret['status']     = d_done["status"]
            except:
                self.dp.qprint("An error occurred in reading ret structure. Should this method have been threaded?")

        return d_ret

    def processPUT(self, **kwargs):
        """
         Dispatcher for PUT
        """

        d_request       = {}
        str_action      = "run"
        str_cmd         = "save"
        str_DBpath      = self.str_DBpath
        str_fileio      = "json"
        tree_DB         = self.within.ptree

        for k,v in kwargs.items():
            if k == 'request':  d_request   = v

        str_action      = d_request['action']
        self.dp.qprint('action = %s' % str_action)
        d_meta              = d_request['meta']
        self.dp.qprint('action = %s' % str_action)

        # Optional search criteria
        if 'key'        in d_meta:
            d_search    = self.t_search_process(request = d_request)['d_ret']

            Tj          = C_stree()
            Tdb         = C_stree()
            for j in d_search.keys():
                d_j = d_search[j]
                for job in d_j.keys():
                    str_pathJob         = '/api/v1/' + job

                    d_job               = self.DB_get(path = str_pathJob)
                    Tj.initFromDict(d_job)
                    Tj.copy(startPath = '/', destination = Tdb)

                    # Tdb.graft(Tj, '/')

                    # self.DB_get(path = str_pathJob).copy(startPath = '/', destination = Tdb)


            # print(Tdb)
            tree_DB     = Tdb

        if 'context'    in d_meta:  str_context     = d_meta['context']
        if 'operation'  in d_meta:  str_cmd         = d_meta['operation']
        if 'dbpath'     in d_meta:  str_DBpath      = d_meta['dbpath']
        if 'fileio'     in d_meta:  str_fileio      = d_meta['fileio']

        if str_action.lower() == 'run' and str_context.lower() == 'db':
            self.within.DB_fileIO(  cmd         = str_cmd,
                                    fileio      = str_fileio,
                                    dbpath      = str_DBpath,
                                    db          = tree_DB)

class Poller(threading.Thread):
    """
    The Poller checks for running processes based on the internal
    DB and system process table. Jobs that are no longer running are
    removed from the internal DB.
    """

    def __init__(self, **kwargs):

        self.pollTime           = 10
        self.str_cmd            = ""
        self.crunner            = None
        self.queueStart         = queue.Queue()
        self.queueEnd           = queue.Queue()
        self.queueAllDone       = queue.Queue()
        self.__name__           = 'Poller'

        # self.dp.qprint('starting...', level=-1)

        # Debug parameters
        self.str_debugFile      = '/dev/null'
        self.b_debugToFile      = True
        self.verbosity          = 0

        for key,val in kwargs.items():
            if key == 'pollTime':       self.pollTime       = val
            if key == 'cmd':            self.str_cmd        = val
            if key == 'debugFile':      self.str_debugFile  = val
            if key == 'debugToFile':    self.b_debugToFile  = val
            if key == 'verbosity':      self.verbosity      = int(val)

        self.dp                 = pfmisc.debug(
                                        verbosity   = self.verbosity,
                                        debugFile   = self.str_debugFile,
                                        debugToFile = self.b_debugToFile,
                                        within      = self.__name__)

        threading.Thread.__init__(self)


    def run(self):

        timeout = 1
        loop    = 10

        """ Main execution. """

        # Spawn the crunner object container
        self.crunner  = Crunner(cmd         = self.str_cmd,
                                debugToFile = self.b_debugToFile,
                                verbosity   = self.verbosity,
                                debugFile   = self.str_debugFile)
        self.crunner.start()

        b_jobsAllDone   = False

        while not b_jobsAllDone:
            try:
                b_jobsAllDone = self.crunner.queueAllDone.get_nowait()
            except queue.Empty:
                # We basically propagate the queue contents "up" the chain.
                self.dp.qprint('Waiting on start job info')
                self.queueStart.put(self.crunner.queueStart.get())

                self.dp.qprint('Waiting on end job info')
                self.queueEnd.put(self.crunner.queueEnd.get())

        self.queueAllDone.put(b_jobsAllDone)
        self.dp.qprint("done with Poller.run")

class Crunner(threading.Thread):
    """
    The wrapper thread about the actual process.
    """

    def __init__(self, **kwargs):
        self.__name             = "Crunner"

        self.queueStart         = queue.Queue()
        self.queueEnd           = queue.Queue()
        self.queueAllDone       = queue.Queue()

        self.str_cmd            = ""

        # Debug parameters
        self.str_debugFile      = '/dev/null'
        self.b_debugToFile      = True
        self.verbosity          = 0

        for k,v in kwargs.items():
            if k == 'cmd':          self.str_cmd        = v
            if k == 'debugFile':    self.str_debugFile  = v
            if k == 'debugToFile':  self.b_debugToFile  = v
            if k == 'verbosity':    self.verbosity      = int(v)

        self.shell              = crunner(  verbosity   = self.verbosity,
                                            debugToFile = self.b_debugToFile,
                                            debugFile   = self.str_debugFile)

        self.dp                 = pfmisc.debug(    
                                            verbosity   = self.verbosity,
                                            debugFile   = self.str_debugFile,
                                            debugToFile = self.b_debugToFile,
                                            within      = self.__name)
        self.dp.qprint('starting crunner...')

        threading.Thread.__init__(self)

    def jsonJobInfo_queuePut(self, **kwargs):
        """
        Get and return the job dictionary as a json string.
        """

        str_queue   = 'startQueue'
        for k,v in kwargs.items():
            if k == 'queue':    str_queue   = v

        if str_queue == 'startQueue':   queue   = self.queueStart
        if str_queue == 'endQueue':     queue   = self.queueEnd

        # self.dp.qprint(self.shell.d_job)

        queue.put(self.shell.d_job.copy())

    def run(self):

        timeout = 1
        loop    = 10

        """ Main execution. """
        self.dp.qprint("running...")
        self.shell(self.str_cmd)
        # self.shell.jobs_loopctl(    onJobStart  = 'self.jsonJobInfo_queuePut(queue="startQueue")',
        #                             onJobDone   = 'self.jsonJobInfo_queuePut(queue="endQueue")')
        self.shell.jobs_loopctl(    onJobStart  = partial(self.jsonJobInfo_queuePut, queue="startQueue"),
                                    onJobDone   = partial(self.jsonJobInfo_queuePut, queue="endQueue"))
        self.queueAllDone.put(True)
        self.queueStart.put({'allJobsStarted': True})
        self.queueEnd.put({'allJobsDone': True})
        # self.shell.exitOnDone()
        self.dp.qprint('Crunner.run() returning...')
