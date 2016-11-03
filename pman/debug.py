import  os
import  datetime
import  threading
import  inspect
import  logging

# pman local dependencies
from   .message           import Message

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s')

class debug(object):
    """
        A simple class that provides some helper debug functions. Mostly
        printing function/thread names and checking verbosity level
        before printing.
    """

    def log(self, *args):
        """
        get/set the log object.

        Caller can further manipulate the log object with object-specific
        calls.
        """
        if len(args):
            self._log = args[0]
        else:
            return self._log

    def name(self, *args):
        """
        get/set the descriptive name text of this object.
        """
        if len(args):
            self.__name = args[0]
        else:
            return self.__name

    def __init__(self, **kwargs):
        """
        Constructor
        """

        self.verbosity  = 0
        self.level      = 0

        self.b_useDebug             = False
        self.str_debugDirFile       = '/tmp'
        for k, v in kwargs.items():
            if k == 'verbosity':    self.verbosity          = v
            if k == 'level':        self.level              = v
            if k == 'debugToFile':  self.b_useDebug         = v
            if k == 'debugFile':    self.str_debugDirFile   = v

        if self.b_useDebug:
            str_debugDir                = os.path.dirname(self.str_debugDirFile)
            str_debugName               = os.path.basename(self.str_debugDirFile)
            if not os.path.exists(str_debugDir):
                os.makedirs(str_debugDir)
            self.str_debugFile          = '%s/%s' % (str_debugDir, str_debugName)
            self.debug                  = Message(logTo = self.str_debugFile)
            self.debug._b_syslog        = False
            self.debug._b_flushNewLine  = True
        self._log                   = Message()
        self._log._b_syslog         = True
        self.__name                 = "pman"


    def __call__(self, *args, **kwargs):
        self.qprint(*args, **kwargs)

    def qprint(self, *args, **kwargs):
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

        if self.b_useDebug:
            write   = self.debug
        else:
            write   = print

        if self.level <= self.verbosity:

            if self.b_useDebug:
                write('| %50s | %30s | ' % (
                    threading.current_thread(),
                    inspect.stack()[1][3]
                ), end='', syslog = True)
            else:
                write('%26s | %50s | %30s | ' % (
                    datetime.datetime.now(),
                    threading.current_thread(),
                    inspect.stack()[1][3]
                ), end='')
            for t in range(0, self.level): write("\t", end='')
            write(self.msg)