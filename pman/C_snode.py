#!/usr/bin/env python3.5

"""
    NAME

        C_snode, C_snodeBranch, C_stree

    DESCRIPTION

        These three classes are used to construct tree-structures
        composed of 'C_snode' instances. Branches contain dictionaries
        of C_snodes, while leaves contain dictionaries of a specific
        external data class.

    HISTORY
        o 26 March 2008
          Initial design and coding

        o 25 February 2014
          Resurrection as part of the fnndsc-netmap app.

        o 27 February 2014
          Cleanup, refactoring, re-indenting.
          Fix class/instance variable mixups.
"""

# System modules
import  os
import  sys
import  re
from    string                  import  *
import  pickle
import  json
import  collections
import  pudb

# pman local dependencies
from    .C_stringCore           import  *
from    .message                import  Message

class C_meta:
        """
        A "base" class containing 'meta' data pertinent to a node.
        """

        def __init__(self, al_mustInclude          = [],
                           al_mustNotInclude       = []):
            self._hitCount              = 0
            self.l_canInclude           = []
            self.l_mustInclude          = al_mustInclude
            self.l_mustNotInclude       = al_mustNotInclude
            self.b_printPre             = False
            self.sCore                  = C_stringCore()
            self._depth                 = 0
            self.str_pre                = ' '

        def __iter__(self):
            for key in ['_depth']:
                yield(key, getattr(self, key))

        #
        ## Getters/setters

        def pre(self, *args):
            """
            Get / set the str_pre
            """
            if len(args):
                self.str_pre = args[0]
            else:
                return self.str_pre

        def mustInclude(self, *args):
            """
            Get / set the [mustInclude].
            """
            if len(args):
                self.l_mustInclude = args[0]
            else:
                return l_mustInclude

        def mustNotInclude(self, *args):
            """
            Get / set the [mustInclude].
            """
            if len(args):
                self.l_mustNotInclude = args[0]
            else:
                return l_mustNotInclude

        def canInclude(self, *args):
            """
            Get / set the [mustInclude].
            """
            if len(args):
                self.l_canInclude = args[0]
            else:
                return l_canInclude

        def depth(self, *args):
            """
            Get/set the depth
            """
            if len(args):
                self._depth = args[0]
            else:
                return self._depth

        #
        ## core overloads

        def __str__(self):
            self.sCore.write('%s   +--depth............ %d\n' % (self.str_pre, self._depth))
            self.sCore.write('%s   +--hitCount......... %d\n' % (self.str_pre, self._hitCount))
            self.sCore.write('%s   +--mustInclude...... %s\n' % (self.str_pre, self.l_mustInclude))
            self.sCore.write('%s   +--mustNotInclude... %s\n' % (self.str_pre, self.l_mustNotInclude))
            str_ret = self.sCore.strget()
            self.sCore.reset()
            return str_ret

class C_snode:
        """
        A "container" node class. This container is the
        basic building block for larger tree-like database
        structures.

        The C_snode defines a single 'node' in this tree. It contains
        two lists, 'l_mustInclude' and 'l_mustNotInclude' that define
        the features described in the 'd_nodes' dictionary. This
        dictionary can in turn contain other C_snodes.
        """

        #
        # Methods
        #
        def __init__(self,      astr_nodeName           = "",
                                al_mustInclude          = [],
                                al_mustNotInclude       = []
                                ):
            #       - Core variables
            self.str_obj        = 'C_snode'      # name of object class
            self.str_name       = 'void'         # name of object variable
            self._id            = -1             # id of agent
            self._iter          = 0              # current iteration in an
                                                 #       arbitrary processing
                                                 #       scheme
            self._verbosity     = 0              # debug related value for
                                                 #       object
            self._warnings      = 0              # show warnings

            self.sCore          = C_stringCore()

            # The d_nodes is the basic building block of the C_snode container
            #+ class. It is simply a dictionary that contains 'nodes' that
            #+ satisfy a given feature set described by 'mustInclude' and
            #+ 'mustNotInclude'.
            #+
            #+ In general:
            #+  'snode_parent'      :       the parent node of this node -- useful
            #+                              for tree structuring.
            #+  '_hitCount'         :       count of hits for all items branching
            #+                              at this level. At the leaf level, this
            #+                              contains the length of 'contents'.
            #+  'l_mustInclude'     :       descriptive trait for specific feature
            #+                              level
            #+  'l_mustNotInclude'  :       exclusion trait for specific feature
            #+                              level
            #+  'd_nodes'           :       dictionary of child nodes branching
            #+                              from this node
            #+  'd_data'            :       a dictionary of data for *this* node
            #+
            #+ The pattern of 'mustInclude' and 'mustNotInclude' uniquely
            #+ characterizes a particular level. "Deeper" features (i.e. features
            #+ further along the dictionary tree) must satisfy the combined set
            #+ described by all the 'mustInclude' and 'mustNotInclude' traits of
            #+ each higher level.

            # self.meta                   = C_meta()
            self.snode_parent           = None
            self.d_nodes                = {}
            self.d_data                 = {}
            # self.b_printMetaData        = True
            self.b_printContents        = True
            self.b_printPre             = False
            self.str_nodeName           = astr_nodeName
            self.b_printPre             = False

        def __iter__(self):
            # yield('meta', dict(self.meta))
            if len(self.d_data):
                for key in self.d_data.keys():
                    yield(key, self.d_data[key])
            for key in self.d_nodes:
                yield(self.d_nodes[key].str_nodeName, dict(self.d_nodes[key]))

        #
        # Getters and setters

        def metaData_print(self, *args):
            return True
            # if len(args):
            #     self.b_printMetaData    = args[0]
            #     return True
            # else:
            #     return self.b_printMetaData

        def depth(self, *args):
            """
            Get/set the depth of this node.
            """
            if len(args):
                pass
                # self.meta.depth(args[0])
            else:
                # return self.meta.depth()
                return 0

        def printPre(self, *args):
            """
            get/set the str_pre string.
            """
            if len(args):
                self.b_printPre = args[0]
            else:
                return self.b_printPre

        @staticmethod
        def str_blockIndent(astr_buf, a_tabs=1, a_tabLength=4, **kwargs):
            """
            For the input string <astr_buf>, replace each '\n'
            with '\n<tab>' where the number of tabs is indicated
            by <a_tabs> and the length of the tab by <a_tabLength>

            Trailing '\n' are *not* replaced.
            """
            str_tabBoundary = " "
            for key, value in kwargs.items():
              if key == 'tabBoundary':  str_tabBoundary = value
            b_trailN = False
            length = len(astr_buf)
            ch_trailN = astr_buf[length - 1]
            if ch_trailN == '\n':
              b_trailN = True
              astr_buf = astr_buf[0:length - 1]
            str_ret = astr_buf
            str_tab = ''
            str_Indent = ''
            for i in range(a_tabLength):
                str_tab = '%s ' % str_tab
            str_tab = "%s%s" % (str_tab, str_tabBoundary)
            for i in range(a_tabs):
                str_Indent = '%s%s' % (str_Indent, str_tab)
            str_ret = re.sub('\n', '\n%s' % str_Indent, astr_buf)
            str_ret = '%s%s' % (str_Indent, str_ret)
            if b_trailN: str_ret = str_ret + '\n'
            return str_ret

        def __str__(self):
            self.sCore.reset()
            str_pre     = ""
            if not self.depth():
                str_pre = "o"
            else:
                str_pre = "+"
            self.sCore.write('%s---%s\n' % (str_pre, self.str_nodeName))
            if self.b_printPre:
                str_pre = "|"
            else:
                str_pre = " "
            # self.meta.pre(str_pre)
            # if self.b_printMetaData: self.sCore.write('%s' % self.meta)

            for key, value in self.d_data.items():
                self.sCore.write('%s   +--%-17s %s\n' % (str_pre, key, value))

            nodeCount     = len(self.d_nodes)
            if nodeCount and self.b_printContents:
                self.sCore.write('%s   +---+\n' % str_pre )
                elCount   = 0
                lastKey   = list(self.d_nodes)[-1]
                for node in list(self.d_nodes):
                    self.d_nodes[node].printPre(True)
                    if node == lastKey:
                        self.d_nodes[node].printPre(False)
                    str_contents = C_snode.str_blockIndent('%s' %
                        self.d_nodes[node], 1, 8, tabBoundary = "")
                    # str_contents = re.sub(r'                ', 'xxxxxxxx|xxxxxxx', str_contents)
                    if self.d_nodes[node].printPre():
                        str_contents = re.sub(r'                ', '        |       ', str_contents)
                    self.sCore.write(str_contents)
                    elCount   = elCount + 1
            return self.sCore.strget()

        #
        # Simple error handling
        def error_exit(self, astr_action, astr_error, astr_code):
            print("%s: FATAL error occurred"                % self.str_obj)
            print("While %s,"                               % astr_action)
            print("%s"                                      % astr_error)
            print("\nReturning to system with code %s\n"    % astr_code)
            sys.exit(astr_code)

        def node_branch(self, al_keys, al_values):
            """
            For each node in <al_values>, add to internal contents
            dictionary using key from <al_keys>.
            """
            if len(al_keys) != len(al_values):
                self.error_exit("adding branch nodes", "#keys != #values", 1)
            ldict = dict(zip(al_keys, al_values))
            self.node_dictBranch(ldict)

        def node_dictBranch(self, adict):
            """
            Expands the internal md_nodes with <adict>
            """
            self.d_nodes.update(adict)

class C_snodeBranch:
        """
        The C_snodeBranch class is basically a dictionary collection
        of C_snodes. Conceptually, a C_snodeBranch is a single "layer"
        of C_snodes all branching from a common ancestor node.
        """
        #
        # Member variables
        #


        #
        # Methods
        #

        def __str__(self):
            self.sCore.reset()
            for node in self.dict_branch.keys():
              self.sCore.write('%s' % self.dict_branch[node])
            return self.sCore.strget()

        def __init__(self, al_branchNodes):
            """
            Constructor.

            If instantiated with a list of nodes, will create/populate
            internal dictionary with appropriate C_snodes.
            """

            self.str_obj                = 'C_snodeBranch';  # name of object class
            self.str_name               = 'void';           # name of object variable
            self._id                    = -1;               # id of agent
            self._iter                  = 0;                # current iteration in an
                                                            #       arbitrary processing
                                                            #       scheme
            self._verbosity             = 0;                # debug related value for
                                                            #       object
            self._warnings              = 0;                # show warnings

            self.dict_branch            = {}
            self.sCore                  = C_stringCore()
            element                     = al_branchNodes[0]
            if isinstance(element, C_snode):
              for node in al_branchNodes:
                self.dict_branch[node]  = node
            else:
              for node in al_branchNodes:
                self.dict_branch[node]  = C_snode(node)

        #
        # Simple error handling
        def error_exit(self, astr_action, astr_error, astr_code):
            print("%s: FATAL error occurred"                % self.str_obj)
            print("While %s,"                               % astr_action)
            print("%s"                                      % astr_error)
            print("\nReturning to system with code %s\n"    % astr_code)
            sys.exit(astr_code)

        def node_branch(self, astr_node, abranch):
            """
            Adds a branch to a node, i.e. depth addition. The given
            node's md_nodes is set to the abranch's mdict_branch.
            """
            self.dict_branch[astr_node].node_dictBranch(abranch.dict_branch)

class C_stree:
        """
        The C_stree class provides methods for creating / navigating
        a tree composed of C_snodes.

        A C_stree is an ordered (and nested) collection of C_snodeBranch
        instances, with additional logic to match nodes with their parent
        node.

        The metaphor designed into the tree structure is that of a UNIX
        directory tree, with equivalent functions for 'cdnode', 'mknode'
        'lsnode'.
        """

        #
        # Methods
        #

        def metaData_print(self, *args):
            if len(args):
                # self.b_printMetaData    = args[0]
                return True
            else:
                # return self.b_printMetaData
                return True

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
            Creates a tree structure and populates the "root"
            branch.
            """
            #
            # Member variables
            #
            #       - Core variables

            self.b_debugToFile          = True
            self.str_debugFile          = '/dev/null'
            for key,val in kwargs.items():
                if key == 'debugFile':      self.str_debugFile  = val
                if key == 'debugToFile':    self.b_debugToFile  = val

            self.debug                  = Message(logTo = self.str_debugFile)
            self.debug._b_syslog        = True
            self._log                   = Message()
            self._log._b_syslog         = True
            self.__name                 = "C_stree"

            self.str_obj                = 'C_stree'     # name of object class
            self.str_name               = 'void'        # name of object variable
            self._id                    = -1            # id of agent
            self._iter                  = 0             # current iteration in an
                                                        #       arbitrary processing
                                                        #       scheme
            self._verbosity             = 0             # debug related value for
                                                        #       object
            self._warnings              = 0             # show warnings
            self.b_printMetaData        = False

            self.l_allPaths             = []            # Each time a new C_snode is
                                                        #+ added to the tree, its path
                                                        #+ list is appended to this
                                                        #+ list variable.
            self.l_allFiles             = []            # A list of lists of of all files
                                                        #+ in the tree
            self.l_lwd                  = []            # A scratch path list variable
                                                        #+ for the lwd() method.
            self.l_fwd                  = []            # A scratch path list variable
                                                        #+ for the fwd() method.

            self.b_initFromDict         = False
            adict                       = {}
            al_rootBranch               = []
            for key,value in kwargs.items():
                if key == 'rootBranch': al_rootBranch   = value
                if key == 'dict':
                    self.b_initFromDict = True
                    adict               = value

            if not len(al_rootBranch):
                al_rootBranch           = ['/']
            if len(al_rootBranch):
                if not isinstance(al_rootBranch, list):
                    al_rootBranch       = ['/']
            self.sCore                  = C_stringCore()
            str_treeRoot                = '/'
            self.l_cwd                  = [str_treeRoot]
            self.sbranch_root           = C_snodeBranch([str_treeRoot])
            self.snode_current          = None
            self.snode_root             = self.sbranch_root.dict_branch[str_treeRoot]
            self.snode_root.depth(0)
            self.snode_root.snode_parent = self.snode_root
            self.root()
            self.l_allPaths             = self.l_cwd[:]
            if len(al_rootBranch) and al_rootBranch != ['/']:
                self.mknode(al_rootBranch)
            self.cd('/')
            if self.b_initFromDict:
                self.initFromDict(adict)

        @staticmethod
        def flatten(d, parent_key='', sep='/'):
            items = []
            for k, v in d.items():
                new_key = parent_key + sep + k if parent_key else k
                if isinstance(v, collections.MutableMapping):
                    if v == {}: v = {'contents': None}
                    items.extend(C_stree.flatten(v, new_key, sep=sep).items())
                else:
                    items.append((sep + new_key, v))
            return dict(items)

        def initFromDict(self, adict, **kwargs):
            """
            Initialize self from dictionary.
            :param adict:
            :return:
            """
            # First, flatten the dictionary into a dictionary of paths/files
            a_flat  = C_stree.flatten(adict)

            l_dir   = []
            # Now, build a tree from this structure by generating a list of paths
            for k, v in a_flat.items():
                l_dir.append(k.split('/')[1:-1])

            # remove duplicates...
            l_dir = [list(x) for x in set(tuple(x) for x in l_dir)]

            # build sorted list of paths...
            l_path  = ['/' + '/'.join(p) for p in l_dir]
            l_path.sort()

            # build the tree
            for dir in l_path: self.mkdir(dir)

            # and now add the leaves
            for file,contents in a_flat.items(): self.touch(file, contents)

        def __str__(self):
            self.sCore.reset()
            self.sCore.write('%s' % self.snode_root)
            return self.sCore.strget()

        def __iter__(self):
            yield(dict(self.snode_root))

        def root(self):
            """
            Reset all nodes and branches to 'root'.
            """
            str_treeRoot                = '/'
            self.l_cwd                  = [str_treeRoot]
            self.snode_current          = self.snode_root
            self.sbranch_current        = self.sbranch_root


        def cwd(self):
            """
            Return a UNIX FS type string of the current working 'directory'.
            """
            l_cwd                       = self.l_cwd[:]
            str_cwd                     = '/'.join(l_cwd)
            if len(str_cwd)>1: str_cwd  = str_cwd[1:]
            return str_cwd

        def path_has(self, **kwargs):
            """
            Checks if the current path has a node spec'd by kwargs
            """
            str_node    = "/" # This node will always be "False"
            for key, val in kwargs.items():
                if key == 'node':   str_node = val
            if str_node in self.l_cwd:
                return { 'found':   True,
                         'indices': [i for i, x in enumerate(self.l_cwd) if x == str_node]}
            else:
                return { 'found':   False,
                         'indices': [-1]}

        def pwd(self, **kwargs):
            """
            Returns the cwd

            Optional kwargs:

                node = <node>
                If specified, return only the directory name at depth <node>.

            """

            b_node  = False
            node    = 0
            for key,val in kwargs.items():
                if key == 'node':
                    b_node  = True
                    node    = int(val)

            str_path = self.cwd()
            if b_node:
                l_path      = str_path.split('/')
                if len(l_path) >= node+1:
                    str_path    = str_path.split('/')[node]
            return str_path

        def ptree(self):
            """
            Return all the paths in the tree.
            """
            return self.l_allPaths

        def node_mustNotInclude(self, al_mustNotInclude, ab_reset=False):
            """
            Either appends or resets the <mustNotInclude> list of snode_current
            depending on <ab_reset>.
            """
            if ab_reset:
                self.snode_current.l_mustNotInclude = al_mustNotInclude[:]
            else:
                l_current   = self.snode_current.l_mustNotInclude[:]
                l_total     = l_current + al_mustNotInclude
                self.snode_current.l_mustNotInclude = l_total[:]

        def node_mustInclude(self, al_mustInclude, ab_reset=False):
            """
            Either appends or resets the <mustInclude> list of snode_current
            depending on <ab_reset>.
            """
            if ab_reset:
                self.snode_current.l_mustInclude = al_mustInclude[:]
            else:
                l_current   = self.snode_current.l_mustInclude[:]
                l_total     = l_current + al_mustInclude
                self.snode_current.l_mustInclude = l_total[:]

        def paths_update(self, al_branchNodes):
            """
            Add each node in <al_branchNodes> to the self.ml_cwd and
            append the combined list to ml_allPaths. This method is
            typically not called by a user, but by other methods in
            this module.

            Returns the list of all paths.
            """
            for node in al_branchNodes:
                #print "appending %s" % node
                l_pwd       = self.l_cwd[:]
                l_pwd.append(node)
                #print "l_pwd: %s" % l_pwd
                #print "ml_cwd: %s" % self.ml_cwd
                self.l_allPaths.append(l_pwd)
            return self.l_allPaths

        def mkdir(self, astr_dirSpec):
            """
            Given an <astr_dirSpec> in form '/a/b/c/d/.../f',
            create that path in the internal stree, creating all
            intermediate nodes as necessary

            :param astr_dirSpec:
            :return:
            """
            if astr_dirSpec != '/' and astr_dirSpec != "//":
                str_currentPath = self.cwd()
                l_pathSpec = astr_dirSpec.split('/')
                if not len(l_pathSpec[0]):
                    self.cd('/')
                    l_nodesDepth = l_pathSpec[1:]
                else:
                    l_nodesDepth = l_pathSpec
                for d in l_nodesDepth:
                    self.mkcd(d)
                self.cd(str_currentPath)

        def mknode(self, al_branchNodes):
            """
            Create a set of nodes (branches) at current node. Analogous to
            a UNIX mkdir call, however nodes can be any type (i.e. not
            just "directories" but also "files")
            """
            b_ret = True
            # First check that none of these nodes already exist in the tree
            l_branchNodes = []
            for node in al_branchNodes:
                l_path      = self.l_cwd[:]
                l_path.append(node)
                #print l_path
                #print self.ml_allPaths
                #print self.b_pathOK(l_path)
                if not self.b_pathOK(l_path):
                    l_branchNodes.append(node)
            if not len(l_branchNodes):
                return False
            snodeBranch   = C_snodeBranch(l_branchNodes)
            for node in l_branchNodes:
                depth = self.snode_current.depth()
                # if (self.msnode_current != self.msnode_root):
                snodeBranch.dict_branch[node].depth(depth+1)
                snodeBranch.dict_branch[node].snode_parent = self.snode_current
            self.snode_current.node_dictBranch(snodeBranch.dict_branch)
            # Update the ml_allPaths
            self.paths_update(al_branchNodes)
            return b_ret

        def mkcd(self, astr_node):
            """Creates a single node and cd's into that node
            """
            self.mknode([astr_node])
            return self.cdnode(astr_node)

        def isdir(self, str_path):
            """
            A convenience function, returns bool if <str_path> is
            a "dir" in the tree space
            """

            return self.b_pathInTree(str_path)[0]

        def isfile(self, str_path):
            """
            A convenience function, returns bool if <str_path> is
            a "file" in the tree space
            """

            b_isFile            = False
            if self.isdir(str_path):
                b_isFile        = False
            else:
                str_parentDir   = '/'.join(str_path.split('/')[0:-1])
                str_fileName    = str_path.split('/')[-1]
                if self.cd(str_parentDir)['status']:
                    l_files = self.lsf(str_parentDir)
                    if any(str_fileName in f for f in l_files):
                        b_isFile    = True
            return b_isFile

        def exists(self, fileDirSpec, **kwargs):
            """
            Simple returns a boolean if the <fileDirSpec>
            exists in the current dir (or dir spec'd by **kwargs)
            """

            str_path        = self.cwd()
            for k,v in kwargs.items():
                if k == 'path': str_path    = v
            if fileDirSpec in self.lstr_lsnode(str_path):
                return True
            if fileDirSpec in self.lsf(str_path):
                return True
            return False

        def cat(self, name):
            """
            Returns the contents of the 'name'd element at this level.

            If file does not exist, returns a False

            TODO: parse possible path spec in name...
            """

            origDir = self.cwd()
            # First, parse any path specs...
            ret     = None
            path    = '/'.join(name.split('/')[0:-1])
            if len(path):
                name    = name.split('/')[-1]
                ret     = self.cd(path)

            if name in self.snode_current.d_data:
                ret     =  self.snode_current.d_data[name]
            else:
                ret     = False
            self.cd(origDir)
            return ret

        def graft(self, atree, apath = '/'):
            """

            NB: THIS METHOD HAS UNEXPECTED MEMORY BEHAVIOUR!
                USE THE copy() METHOD INSTEAD!

            Attach (link) apath in a separate atree to here.

            Functionally equivalent to

                ln -s atree:/apath .

            Also updates the self tree's path list space.

            :param atree: a tree
            :param apath: a path in atree
            :return: True | False depending on successful graft
            """
            ret = False
            if atree.cd(apath)['status']:
                atree_nodes                 = atree.lstr_lsnode()
                str_self_cwd                = self.cwd()
                str_atree_cwd               = atree.cwd()

                b_childrenLink              = False
                if apath != '/':
                    l_apath = apath.split('/')
                    # No trailing '/'
                    if l_apath[-1] != '':
                        self.mkcd(apath.split('/')[-1])
                        self.snode_current.d_nodes  = atree.snode_current.d_nodes
                        self.snode_current.d_data   = atree.snode_current.d_data
                    # Trailing '/'
                    else:
                        apath = apath[0:-1]
                        if apath[-1] != '/':
                            atree.cd(apath)
                            atree_nodes     = atree.lstr_lsnode()
                            b_childrenLink  = True
                else:
                    b_childrenLink  = True
                if b_childrenLink:
                    self.mknode(atree_nodes)
                    for node in atree_nodes:
                        self.cd(node)
                        atree.cd(apath + '/' + node)
                        self.snode_current.d_nodes  = atree.snode_current.d_nodes
                        self.snode_current.d_data   = atree.snode_current.d_data
                        atree.cd('../')
                        self.cd('../')

                # Update internal space of possible paths.
                self.cd('../')
                self.pathFromHere_explore(self.cwd())
                self.cd(str_self_cwd)
                atree.cd(str_atree_cwd)
                ret = True
            return ret

        def touch(self, name, data):
            """
            Create a 'file' analog called 'name' and put 'data' to the d_data dictionary
            under key 'name'.

            The 'name' can contain a path specifier.
            """
            b_OK        = True
            str_here    = self.cwd()
            # print("here!")
            # print(self.snode_current)
            # print(self.snode_current.d_nodes)
            l_path = name.split('/')
            if len(l_path) > 1:
                self.cd('/'.join(l_path[0:-1]))
            name = l_path[-1]
            self.snode_current.d_data[name] = data
            # print(self.snode_current)
            self.cd(str_here)
            return b_OK

        def rm(self, name):
            """
            Remove a data analog called 'name'.

            The 'name' can contain a path specifier.

            Warning: see

                http://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary

            deleting from the snode_current changes dictionary contents for any other
            agents that have references to the same instance.

            This deletes either directories or files.

            """
            b_OK        = False
            str_here    = self.cwd()
            l_path = name.split('/')
            if len(l_path) > 1:
                self.cd('/'.join(l_path[0:-1]))
            name = l_path[-1]
            if name in self.snode_current.d_data:
                del self.snode_current.d_data[name]
                b_OK    = True
            if name in self.snode_current.d_nodes:
                del self.snode_current.d_nodes[name]
                b_OK    = True
            self.cd(str_here)
            return b_OK

        def append(self, name, data):
            """Append 'data' to the current node d_data

            This method appends 'data' to the current contents in the
            key named 'name'. The append assumes that the operation
            makes sense and that the data types can be appended to
            each other.

            """
            b_OK = True
            self.snode_current.d_data[name] = self.snode_current.d_data[name] + data
            return b_OK


        def b_pathOK(self, al_path):
            """
            Checks if the absolute path specified in the al_path
            is valid for current tree
            """
            b_OK  = True
            try:          self.l_allPaths.index(al_path)
            except:       b_OK    = False
            return b_OK

        def b_pathInTree(self, astr_path):
            """
            Converts a string <astr_path> specifier to a list-based
            *absolute* lookup, i.e. "/node1/node2/node3" is converted
            to ['/' 'node1' 'node2' 'node3'].

            The method also understands a paths that start with: '..' or
            combination of '../../..' and is also aware that the root
            node is its own parent.

            If the path list conversion is valid (i.e. exists in the
            space of existing paths, l_allPaths), return True and the
            destination path list; else return False and the current
            path list.
            """
            if astr_path == '/':  return True, ['/']
            al_path               = astr_path.split('/')
            # Do we have a trailing '/' and not doing a '../'? If so, strip it..!
            if astr_path != '../' and al_path[-1] == '':
                al_path = al_path[0:-2]

            # Check for absolute path
            if not len(al_path[0]):
                al_path[0]          = '/'
                # print "returning %s : %s" % (self.b_pathOK(al_path), al_path)
                return self.b_pathOK(al_path), al_path
            # Here we are in relative mode...
            # First, resolve any leading '..'
            l_path        = self.l_cwd[:]
            if al_path[0] == '..':
                while al_path[0] == '..' and len(al_path):
                    l_path    = l_path[0:-1]
                    if len(al_path) >= 2: al_path   = al_path[1:]
                    else: al_path[0] = ''
                    # print "l_path  = %s" % l_path
                    # print "al_path = %s (%d)" % (al_path, len(al_path[0]))
                if len(al_path[0]):
                    # print "extending %s with %s" % (l_path, al_path)
                    l_path.extend(al_path)
            else:
                l_path      = self.l_cwd
                l_path.extend(al_path)
            # print "final path list = %s (%d)" % (l_path, len(l_path))
            if len(l_path)>=1 and l_path[0] != '/':      l_path.insert(0, '/')
            if len(l_path)>1:            l_path[0]       = ''
            if not len(l_path):          l_path          = ['/']
            str_path      = '/'.join(l_path)
            # print "final path str  = %s" % str_path
            b_valid, al_path = self.b_pathInTree(str_path)
            return b_valid, al_path

        def cdnode(self, astr_path):
            """Change working node to astr_path.

            The path is converted to a list, split on '/'. By performing a 'cd'
            all parent and derived nodes need to be updated relative to
            new location.

            Args:
                astr_path (string): The path to cd to.

            Returns:
                {"status" : True/False , "path": l_cwd -- the path as list}

            """

            # Start at the root and then navigate to the
            # relevant node
            l_absPath             = []
            b_valid, l_absPath    = self.b_pathInTree(astr_path)
            if b_valid:
                #print "got cdpath = %s" % l_absPath
                self.l_cwd              = l_absPath[:]
                self.snode_current      = self.snode_root
                self.sbranch_current    = self.sbranch_root
                #print l_absPath
                for node in l_absPath[1:]:
                    self.snode_current = self.snode_current.d_nodes[node]
                self.sbranch_current.dict_branch = self.snode_current.snode_parent.d_nodes
                return {"status": True, "path": self.l_cwd}
            return {"status": False, "path": []}

        def cd(self, astr_path):
            """Alias for cdnode()

            """
            return self.cdnode(astr_path)

        def ls(self, astr_path="", **kwargs):
            b_lsData    = True
            b_lsNodes   = True
            str_cwd       = self.cwd()
            if len(astr_path): self.cdnode(astr_path)
            str_nodes   = self.str_lsnode(astr_path)
            d_data      = self.snode_current.d_data
            for key, val in kwargs.items():
                if key == 'data':   b_lsData    = val
                if key == 'nodes':  b_lsNodes   = val
            if len(astr_path): self.cdnode(str_cwd)
            if b_lsData and b_lsNodes:
                return str_nodes, d_data
            if b_lsData:
                return d_data
            if b_lsNodes:
                return str_nodes
            return str_nodes, d_data

        def lsf(self, astr_path=""):
            """
            List only the "files" in the astr_path.

            :param astr_path: path to list
            :return: "files" in astr_path, empty list if no files
            """
            d_files = self.ls(astr_path, nodes=False, data=True)
            l_files = d_files.keys()
            return l_files

        def str_lsnode(self, astr_path=""):
            """
            Print/return the set of nodes branching from current node as string
            """
            self.sCore.reset()
            str_cwd       = self.cwd()
            if len(astr_path): self.cdnode(astr_path)
            for node in self.snode_current.d_nodes.keys():
                self.sCore.write('%s\n' % node)
            str_ls = self.sCore.strget()
            if len(astr_path): self.cdnode(str_cwd)
            return str_ls

        def lstr_lsnode(self, astr_path=""):
            """
            Return the string names of the set of nodes branching from
            current node as list of strings
            """
            self.sCore.reset()
            str_cwd       = self.cwd()
            if len(astr_path): self.cdnode(astr_path)
            lst = self.snode_current.d_nodes.keys()
            if len(astr_path): self.cdnode(str_cwd)
            return lst

        def lsbranch(self, astr_path=""):
            """
            Print/return the set of nodes in current branch
            """
            self.sCore.reset()
            str_cwd       = self.cwd()
            if len(astr_path): self.cdnode(astr_path)
            self.sCore.write('%s' % self.sbranch_current.dict_branch.keys())
            str_ls = self.sCore.strget()
            if len(astr_path): self.cdnode(str_cwd)
            return str_ls

        def lstree(self, astr_path=""):
            """
            Print/return the tree from the current node.
            """
            self.sCore.reset()
            str_cwd       = self.cwd()
            if len(astr_path): self.cdnode(astr_path)
            str_ls        = '%s' % self.snode_current
            print(str_ls)
            if len(astr_path): self.cdnode(str_cwd)
            return str_ls

        def lsmeta(self, astr_path=""):
            """
            Print/return the "meta" information of the node, i.e.
                o mustInclude
                o mustNotInclude
                o hitCount
            """
            self.sCore.reset()
            str_cwd       = self.cwd()
            if len(astr_path): self.cdnode(astr_path)
            b_contentsFlag        = self.snode_current.b_printContents
            self.snode_current.b_printContents = False
            str_ls        = '%s' % self.snode_current
            print(str_ls)
            if len(astr_path): self.cdnode(str_cwd)
            self.snode_current.b_printContents  = b_contentsFlag
            return str_ls

        def tree_metaData_print(self, aval):
            self.metaData_print(aval)
            self.treeRecurse(self.treeNode_metaSet)

        def treeNode_metaSet(self, astr_path, **kwargs):
            """
            Sets the metaData_print bit on node at <astr_path>.
            """
            self.cdnode(astr_path)
            self.snode_current.metaData_print(self.b_printMetaData)
            return {'status': True}

        def node_save(self, astr_pathInTree, **kwargs):
            """
            Typically called by the explore()/recurse() methods and of form:

                f(pathInTree, **kwargs)

            and returns dictionary of which one element is

                'status':   True|False

            recursion continuation flag is returned:

                'continue': True|False

            to signal calling parent whether or not to continue with tree
            transversal.

            Save the node specified by a path in the data tree to disk.

            Given a "root" on the disk storage, create the path relative
            to that root, and in that location, save the contents of the internal
            node's d_data at that tree path location.

            :param kwargs:
            :return:
            """
            str_pathDiskRoot    = '/tmp'
            str_pathDiskOrig    = os.getcwd()
            srt_pathDiskFull    = ''
            str_pathTree        = ''
            str_pathTreeOrig    = self.pwd()
            b_failOnDirExist    = True
            b_saveJSON          = True
            b_savePickle        = False
            for key, val in kwargs.items():
                if key == 'startPath':      str_pathTree        = val
                if key == 'pathDiskRoot':   str_pathDiskRoot    = val
                if key == 'failOnDirExist': b_failOnDirExist    = val
                if key == 'saveJSON':       b_saveJSON          = val
                if key == 'savePickle':     b_savePickle        = val

            str_pathDiskFull    = str_pathDiskRoot + str_pathTree
            # print('\n')
            # print('In self.node_save():')
            # print('memTree:  %s' % (str_pathTree))
            # print('diskRoot: %s' % str_pathDiskRoot)
            # print('distPath: %s' % str_pathDiskFull)
            # print(kwargs.keys())
            # print(kwargs.values())
            # print('\n')

            if len(str_pathDiskRoot):
                if not os.path.isdir(str_pathDiskRoot):
                    # print('Processing path: %s' % str_pathDiskRoot)
                    try:
                        # print('mkdir %s' % str_pathDiskRoot)
                        os.makedirs(str_pathDiskRoot)
                    except OSError as exception:
                        return {'status' :      False,
                                'continue':     False,
                                'message':      'unable to create pathDiskRoot: %s' % str_pathDiskRoot,
                                'exception':    exception}
                # print('cd to %s' % str_pathDiskRoot)
                os.chdir(str_pathDiskRoot)
                if self.cd(str_pathTree)['status']:
                    if str_pathTree != '/':
                        # print('mkdir %s' % str_pathDiskFull)
                        try:
                            os.makedirs(str_pathDiskFull)
                        except OSError as exception:
                            if b_failOnDirExist:
                                return {'status' :      False,
                                        'continue':     False,
                                        'message':      'unable to create pathDiskRoot: %s' % str_pathDiskRoot,
                                        'exception':    exception}

                    os.chdir(str_pathDiskFull)
                    for str_filename, contents in self.snode_current.d_data.items():
                        # print("str_filename = %s; contents = %s" % (str_filename, contents))
                        if b_saveJSON:
                            with open(str_filename, 'w')    as f: json.dump(contents,     f)
                            f.close()
                        if b_savePickle:
                            with open(str_filename, 'wb')   as f: json.dump(contents,     f)
                            f.close()
                else:
                    return{'status':    False,
                           'continue':  False,
                           'message':   'pathTree invalid'}
                self.cd(str_pathTreeOrig)
                os.chdir(str_pathDiskOrig)
                return {'status':   True,
                        'continue': True}
            return {'status':   False,
                    'continue': False,
                    'message':  'pathDisk not specified'}

        def node_copy(self, astr_pathInTree, **kwargs):
            """
            Typically called by the explore()/recurse() methods and of form:

                f(pathInTree, **kwargs)

            and returns dictionary of which one element is

                'status':   True|False

            recursion continuation flag is returned:

                'continue': True|False

            to signal calling parent whether or not to continue with tree
            transversal.

            Save the node specified by a path in the data tree of self
            (the astr_pathInTree) to the passed data tree, relative to a
            passed 'pathDiskRoot', i.e.

                S.node_copy('/', destination = T, pathDiskRoot = '/some/path/in/T')

            Will copy the items and "folders" in (source) S:/ to
            (target) T:/some/path/in/T

            :param kwargs:
            :return:
            """

            # Here, 'T' is the target 'disk'.
            T                   = None
            str_pathDiskRoot    = ''
            str_pathDiskFull    = ''
            str_pathTree        = ''
            str_pathTreeOrig    = self.pwd()
            for key, val in kwargs.items():
                if key == 'startPath':      str_pathTree        = val
                if key == 'pathDiskRoot':   str_pathDiskRoot    = val
                if key == 'destination':    T                   = val
            str_pathDiskOrig    = T.pwd()
            str_pathDiskFull    = str_pathDiskRoot + str_pathTree

            # self.debug('In node_copy... str_pathDiskfull = %s\n' % str_pathDiskFull)

            if len(str_pathDiskFull):
                if not T.isdir(str_pathDiskFull):
                    try:
                        T.mkdir(str_pathDiskFull)
                    except:
                        return {'status' :      False,
                                'continue':     False,
                                'message':      'unable to create pathDiskFull: %s' % str_pathDiskFull,
                                'exception':    exception}
                if T.cd(str_pathDiskFull)['status']:
                    if self.cd(str_pathTree)['status']:
                        T.cd(str_pathDiskFull)
                        for str_filename, contents in self.snode_current.d_data.items():
                            # print("str_filename = %s; contents = %s" % (str_filename, contents))
                            T.touch(str_filename, contents)
                    else:
                        return{'status':    False,
                               'continue':  False,
                               'message':   'source pathTree invalid'}
                    self.cd(str_pathTreeOrig)
                    T.cd(str_pathDiskOrig)
                    return {'status':   True,
                            'continue': True}
                else:
                    return{'status':    False,
                           'continue':  False,
                           'message':   'target pathDiskFull invalid'}
            return {'status':   False,
                    'continue': False,
                    'message':  'pathDiskFull not specified'}

        def copy(self, **kwargs):
            """

            Convenience function/alias for tree_copy()

            :param kwargs:
            :return:
            """
            return self.tree_copy(**kwargs)

        def tree_copy(self, **kwargs):
            """
            Deep copy "self" to a target <destination = T>.

            Essentially, this creates/copies this self tree to
            a target tree.

            For kwargs, see node_save()

            :param kwargs:
            :return:
            """
            # pudb.set_trace()
            kwargs['f']         = self.node_copy
            return self.treeExplore(**kwargs)

        def tree_save(self, **kwargs):
            """
            Save a tree to disk.

            Essentially, this creates a mirror of the internal tree
            structure on disk.

            For kwargs, see node_save()

            :param kwargs:
            :return:
            """

            kwargs['f']         = self.node_save
            self.treeExplore(**kwargs)

        @staticmethod
        def tree_load(**kwargs):
            """
            Load a tree from disk.

            Essentially, this reads a disk filetree into an snode tree.

            :param kwargs:
            :return:
            """
            str_pathDiskRoot    = ''
            b_loadJSON          = True
            b_loadPickle        = False
            for key, val in kwargs.items():
                if key == 'pathDiskRoot':   str_pathDiskRoot    = val
                if key == 'loadJSON':       b_loadJSON          = val
                if key == 'loadPickle':     b_loadPickle        = val

            l_dir   = []
            l_file  = []
            for str_root, l_directories, l_filenames in os.walk(str_pathDiskRoot):
                for str_dir in l_directories:
                    l_dir.append(os.path.join(str_root, str_dir))
                for str_file in l_filenames:
                    l_file.append(os.path.join(str_root, str_file))
            stree_dirs  = [d.replace(str_pathDiskRoot, '') for d in l_dir]
            stree_files = [f.replace(str_pathDiskRoot, '') for f in l_file]

            # Create the tree
            rtree       = C_stree()
            # Build the directory structures
            for d in stree_dirs:
                # print(d)
                rtree.mkdir(d)
            # Now read any files
            for f in stree_files:
                dirname     = os.path.dirname(f)
                filename    = os.path.basename(f)
                # print(f)
                if b_loadJSON:
                    with open(str_pathDiskRoot + '/' + f, 'r') as fp:
                        contents = json.load(fp)
                        fp.close()
                if b_loadPickle:
                    with open(str_pathDiskRoot + '/' + f, 'rb') as fp:
                        contents = pickle.load(fp)
                        fp.close()

                if rtree.cd(dirname)['status']:
                    rtree.touch(filename, contents)

            return rtree


        def treeExplore(self, **kwargs):
            """
            Recursively walk through a C_stree, applying a passed function
            at each node. The actual "walk" uses individual nodes' internal
            child dictionaries.

            It is assumed that the start origin of exploration can in fact
            be reached by a 'cd()' call. Directories are added to the internal
            l_allPaths list variable as they are discovered.

            kwargs:
                startPath=<startPath> :     The starting point in the tree
                func=<f> :                  The function to apply at each node

                Additional kwargs are passed to <f>

            <f> is a function that is called on a node path. It is of form:

                f(path, **kwargs)

            where path is a node in the tree space.

            <f> must return a dictionary containing at least one field:

                { "status": True | False }

            This same dictionary is also returned out to the caller of this
            function.

            """

            str_recursePath = ''
            str_startPath   = '/'
            f               = None
            ret             = {}

            for key,val in kwargs.items():
                if key == 'startPath':  str_startPath   = val
                if key == 'f':          f               = val

            # print 'processing node: %s' % str_startPath
            if self.cd(str_startPath)['status']:
                ret = f(str_startPath, **kwargs)
                if ret['status']:
                    for node in self.lstr_lsnode(str_startPath):
                        if str_startPath == '/': str_recursePath = "/%s" % node
                        else: str_recursePath = '%s/%s' % (str_startPath, node)
                        l_recursePath       = str_recursePath.split('/')
                        l_recursePath[0]    = '/'
                        if not l_recursePath in self.l_allPaths:
                            self.l_allPaths.append(l_recursePath)
                        kwargs['startPath'] = str_recursePath
                        self.treeExplore(**kwargs)
            else: ret['status']  = False
            return ret

        def treeWalk(self, **kwargs):
            """
            Recursively walk through a C_stree, applying a passed function
            at each node. The actual "walk" depends on using the 'cd' function
            which will only descend into paths that already exist in the
            internal path database.

            To flush this and explore the pathspace de novo, use treeExplore()
            instead.

            kwargs:
                --startPath=<startPath> :   The starting point in the tree
                --func=<f> :                The function to apply at each node

                Additional kwargs are passed to <f>

            <f> is a function that is called on a node path. It is of form:

                f(path, **kwargs)

            where path is a node in the tree space.

            <f> must return a dictionary containing at least one field:

                { "status": True | False }

            This same dictionary is also returned out to the caller of this
            function.

            """

            str_recursePath = ''
            str_startPath   = '/'
            f               = None
            ret             = {}

            for key,val in kwargs.items():
                if key == 'startPath':  str_startPath   = val
                if key == 'f':          f               = val

            # print 'processing node: %s' % str_startPath
            if self.cd(str_startPath)['status']:
                ret = f(str_startPath, **kwargs)
                if ret['status']:
                    for node in self.lstr_lsnode(str_startPath):
                        if str_startPath == '/': str_recursePath = "/%s" % node
                        else: str_recursePath = '%s/%s' % (str_startPath, node)
                        self.treeWalk(f = f, startPath = str_recursePath)
            return ret

        def treeRecurse(self, afunc_nodeEval = None, astr_startPath = '/'):
            """
            Recursively walk through the C_stree, starting from node
            <astr_startPath> and using the internal l_allPaths space
            as verifier.

            To self-discover tree structure based on internal node links,
            use treeExplore() instead.

            The <afunc_nodeEval> is a function that is called on a node
            path. It is of form:

                afunc_nodeEval(astr_startPath, **kwargs)

            and must return a dictionary containing at least one field:

                { "status": True | False }

            This same dictionary is also returned out to the caller of this
            function.

            """
            ret = {'status': False}
            [b_valid, l_path ] = self.b_pathInTree(astr_startPath)
            if b_valid and afunc_nodeEval:
                ret = afunc_nodeEval(astr_startPath)
            b_OK = ret['status']
            #print 'processing node: %s' % astr_startPath
            if b_OK:
                for node in self.lstr_lsnode(astr_startPath):
                    if astr_startPath == '/': recursePath = "/%s" % node
                    else: recursePath = '%s/%s' % (astr_startPath, node)
                    self.treeRecurse(afunc_nodeEval, recursePath)
            return ret

        def lwd(self, astr_startPath, **kwargs):
            """
            Return the cwd in treeRecurse compatible format.
            :return: Return the cwd in treeRecurse compatible format.
            """
            if self.cd(astr_startPath)['status']:
                self.l_lwd.append(self.cwd())

            return {'status': True, 'cwd': self.cwd()}

        def fwd(self, astr_startPath, **kwargs):
            """
            Return the files-in-working-directory in treeRecurse
            compatible format.
            :return: Return the cwd in treeRecurse compatible format.
            """
            status = self.cd(astr_startPath)['status']
            if status:
                l = self.lsf()
                if len(l):
                    lf = [self.cwd() + '/' + f for f in l]
                    for entry in lf:
                        self.l_fwd.append(entry)

            return {'status': status, 'cwd': self.cwd()}

        def filesFromHere_explore(self, astr_startPath = '/'):
            """
            Return a list of path/files from "here" in the stree, using
            the child explore access.

            :param astr_startPath: path from which to start
            :return:
            """
            self.l_fwd  = []
            self.treeExplore(startPath = astr_startPath, f=self.fwd)
            self.l_allFiles = [f.split('/') for f in self.l_fwd]
            for i in range(0, len(self.l_allFiles)):
                self.l_allFiles[i][0] = '/'
            return self.l_fwd

        def pathFromHere_walk(self, astr_startPath = '/'):
            """
            Return a list of paths from "here" in the stree, using
            the internal cd() to walk the path space.

            :return: a list of paths from "here"
            """

            self.l_lwd  = []
            self.treeWalk(startPath = astr_startPath, f=self.lwd)
            return self.l_lwd

        def pathFromHere_explore(self, astr_startPath = '/'):
            """
            Return a list of paths from "here" in the stree, using the
            child explore access.

            :param astr_startPath: path from which to start
            :return: a list of paths from "here"
            """

            self.l_lwd  = []
            self.treeExplore(startPath = astr_startPath, f=self.lwd)
            return self.l_lwd

        #
        # Simple error handling
        def error_exit(self, astr_action, astr_error, astr_code):
            print("%s: FATAL error occurred" % self.str_obj)
            print("While %s," % astr_action)
            print("%s" % astr_error)
            print("\nReturning to system with code %s\n" % astr_code)
            sys.exit(astr_code)

if __name__ == "__main__":


    aTree = C_stree()
    bTree = C_stree()
    ATree = C_stree()

    aTree.cd('/')
    aTree.mkcd('a')
    aTree.mknode(['b', 'c'])
    aTree.cd('b')
    aTree.touch('file1', 10)
    aTree.touch('file2', "Rudolph Pienaar")
    aTree.touch('file3', ['this', 'is', 'a', 'list'])
    aTree.touch('file4', ('this', 'is', 'a', 'tuple'))
    aTree.touch('file5', {'name': 'rudolph', 'address': '505 Washington'})

    aTree.mknode(['d', 'e'])
    aTree.cd('d')
    aTree.mknode(['h', 'i'])
    aTree.cd('/a/b/e')
    aTree.mknode(['j', 'k'])
    aTree.cd('/a/c')
    aTree.mknode(['f', 'g'])
    aTree.cd('f')
    aTree.mknode(['l', 'm'])
    aTree.cd('/a/c/g')
    aTree.mknode(['n', 'o'])

    ATree.cd('/')
    ATree.mkcd('A')
    ATree.mknode(['B', 'C'])
    ATree.cd('B')
    ATree.mknode(['D', 'E'])
    ATree.cd('D')
    ATree.mknode(['H', 'I'])
    ATree.cd('/A/B/E')
    ATree.mknode(['J', 'K'])
    ATree.cd('/A/B/E/K')
    ATree.touch('file1', 11)
    ATree.touch('file2', "Reza Pienaar")
    ATree.touch('file3', ['this', 'is', 'another', 'list'])
    ATree.touch('file4', ('this', 'is', 'another', 'tuple'))
    ATree.touch('file5', {'name': 'reza', 'address': '505 Washington'})
    ATree.cd('/A/C')
    ATree.mknode(['F', 'G'])
    ATree.cd('F')
    ATree.mknode(['L', 'M'])
    ATree.cd('/A/C/G')
    ATree.mknode(['N', 'O'])

    bTree.cd('/')
    bTree.mkcd('1')
    bTree.mknode(['2', '3'])
    bTree.cd('2')
    bTree.mknode(['4', '5'])
    bTree.cd('4')
    bTree.mknode(['8', '9'])
    bTree.cd('/1/2/5')
    bTree.mknode(['10', '11'])
    bTree.cd('/1/3')
    bTree.mknode(['6', '7'])
    bTree.cd('6')
    bTree.mknode(['12', '13'])
    bTree.cd('/1/3/7')
    bTree.mknode(['14', '15'])

    aTree.tree_metaData_print(False)
    ATree.tree_metaData_print(False)
    bTree.tree_metaData_print(False)

    print('aTree = %s' % aTree)
    # print(aTree.pathFromHere_walk('/'))
    print('ATree = %s' % ATree)
    # print(ATree.pathFromHere_walk('/'))
    print('bTree = %s' % bTree)
    # print(bTree.pathFromHere_walk('/'))

    aTree.cd('/')
    aTree.graft(bTree, '/1/2/')
    aTree.tree_metaData_print(False)
    print('aTree = %s' % aTree)
    # print(aTree.pathFromHere_walk('/'))
    # print(aTree.l_allPaths)

    bTree.cd('/1/2/4/9')
    bTree.graft(ATree, '/A/B')
    bTree.tree_metaData_print(False)
    print('bTree = %s' % bTree)
    # print(bTree.pathFromHere_walk('/'))
    # print(bTree.l_allPaths)

    print('aTree = %s' % aTree)
    # print(aTree.pathFromHere_explore('/'))
    # print(aTree.l_allPaths)
    # print(aTree.filesFromHere_explore('/'))
    # print(aTree.l_allFiles)

    print('Saving bTree...')
    bTree.tree_save(startPath       = '/',
                    pathDiskRoot    = '/tmp/bTree',
                    failOnDirExist  = True,
                    saveJSON        = True,
                    savePickle      = False)

    print('Saving aTree...')
    aTree.tree_save(startPath       = '/',
                    pathDiskRoot    = '/tmp/aTree',
                    failOnDirExist  = True,
                    saveJSON        = True,
                    savePickle      = False)

    print('Reading aTree into cTree...')
    cTree = C_stree.tree_load(
                    pathDiskRoot    = '/tmp/aTree',
                    loadJSON        = True,
                    loadPickle      = False)
    cTree.tree_metaData_print(False)
    print('cTree = %s' % cTree)
    cTree.rm('/4/9/B/E/K/file1')
    print('cTree = %s' % cTree)
    cTree.rm('/4/9/B/E/K/file2')
    print('cTree = %s' % cTree)
    cTree.rm('/4/9/B/E/K')
    print('cTree = %s' % cTree)

    dTree   = C_stree()
    cTree.tree_copy(startPath   = '/a/b/file5',
                    destination = dTree)
    print('dTree = %s' % dTree)
