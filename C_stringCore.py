#!/usr/bin/env python
"""
    NAME

        C_stringCore

    DESCRIPTION
        
        'C_stringCore' is a wrapper about a python cStringIO
        class. It provides a thins wrapper abstracting some
        simple methods to write/read to and from a StringIO 
        object.

    NOTES

    HISTORY

        06 February 2008
        o Design consolidated from several sources.

        25 February 2014
        o print --> print()

        27 February 2014
        o Fix class/instance variable mixup
        o Refactor and cleanup

"""

# System modules
import  os
import  sys
from    string          import  *

try:
	from    cStringIO       import  StringIO
except ImportError:
	from 	io 		import 	StringIO
from    cgi             import  *

class C_stringCore:
        """
        This class is a wrapper about a cStringIO instance, keeping
        track of an internal file-string instance and syncing its
        contents to an internal string buffer.
        """

        
        #
        # Methods
        #
        def __init__(self):
                # 
                # Member variables
                #
                #       - Core variables
                self.str_obj    = 'C_stringCore'        # name of object class
                self.str_name   = 'void'                # name of object variable
                self._id        = -1                    # id of agent
                self._iter      = 0                     # current iteration in an
                                                        #       arbitrary processing 
                                                        #       scheme
                self._verbosity = 0                     # debug related value for
                                                        #       object
                self._warnings  = 0                     # show warnings
                                                        #       (and warnings level)
                
                #
                #       - Class variables
                self.StringIO           = StringIO()    # A file string buffer that
                                                        #       functions as a 
                                                        #       scratch space for
                                                        #       the core
                self.str                = ""

        def metaData_print(self):
                print('str_obj\t\t= %s'         % self.str_obj)
                print('str_name\t\t= %s'        % self.str_name)
                print('_id\t\t\t= %d'           % self._id)
                print('_iter\t\t\t= %d'         % self._iter)
                print('_verbosity\t\t= %d'      % self._verbosity)
                print('_warnings\t\t= %d'       % self._warnings)
                return 'This class functions as a string file handler.'

        def __str__(self):
                return self.str 
        
        #
        # core methods
        def strout(self, astr_text=""):
            if(len(astr_text)): 
                self.write(astr_text)
                print("%s" % self.strget())

        def reset(self, astr_newCore = ""):
            self.StringIO.close()
            self.StringIO       = StringIO()
            self.StringIO.write(astr_newCore)

        def strget(self):
            return self.StringIO.getvalue()

        def write(self, astr_text):
            if isinstance(astr_text, list):
              astr_text         = '\n'.join(astr_text)
            self.StringIO.write(astr_text)
            self.str            = self.strget()
            return astr_text
