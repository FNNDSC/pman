#!/usr/bin/env python3.5

str_desc = """
        __ _       _
       / _(_)     | |
 _ __ | |_ _  ___ | |__
| '_ \|  _| |/ _ \| '_ \\
| |_) | | | | (_) | | | |
| .__/|_| |_|\___/|_| |_|
| |
|_|



                         A simple http file IO handler

    `pfioh' is a simple http-based file I/O handler/server allowing software
    agents to perform useful file transfers over http.

    `pfioh' handles HTTP REST-like requests on a given port -- it can accept
    incoming file data from a client, and can also return server-side file trees
    to a client.

    `pfioh' can also zip up/unzip file trees so that entire paths can be easily
    transferred.

"""

import  os
import  sys

from    io              import BytesIO as IO
from    http.server     import BaseHTTPRequestHandler, HTTPServer
from    socketserver    import ThreadingMixIn
import  socket
import  argparse
import  cgi
import  zipfile
import  json
import  base64
import  zipfile
import  uuid
import  urllib
import  ast
import  shutil
import  datetime

# pman local dependencies
from    ._colors        import Colors
from    .debug          import debug

class StoreHandler(BaseHTTPRequestHandler):

    b_quiet     = False

    def __init__(self, *args, **kwargs):
        """
        """
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def qprint(self, msg, **kwargs):

        str_comms  = ""
        for k,v in kwargs.items():
            if k == 'comms':    str_comms  = v

        if not StoreHandler.b_quiet:
            if str_comms == 'status':   print(Colors.PURPLE,    end="")
            if str_comms == 'error':    print(Colors.RED,       end="")
            if str_comms == "tx":       print(Colors.YELLOW + "<----")
            if str_comms == "rx":       print(Colors.GREEN  + "---->")
            print('%s' % datetime.datetime.now() + " | ",       end="")
            print(msg)
            if str_comms == "tx":       print(Colors.YELLOW + "<----")
            if str_comms == "rx":       print(Colors.GREEN  + "---->")
            print(Colors.NO_COLOUR, end="")

    def do_GET_remoteStatus(self, d_msg, **kwargs):
        """
        This method is used to get information about the remote
        server -- for example, is a remote directory/file valid?
        """
        d_meta              = d_msg['meta']
        d_remote            = d_meta['remote']

        str_serverPath      = d_remote['path']

        b_isFile            = os.path.isfile(str_serverPath)
        b_isDir             = os.path.isdir(str_serverPath)
        b_exists            = os.path.exists(str_serverPath)

        d_ret               = {
            'status':  b_exists,
            'isfile':  b_isFile,
            'isdir':   b_isDir
        }


        self.ret_client(d_ret)

        self.qprint(d_ret, comms = 'tx')

        return {'status': b_exists}

    def do_GET_withCompression(self, d_msg):
        """
        Process a "GET" using zip/base64 encoding

        :return:
        """

        # d_msg               = ast.literal_eval(d_server)
        d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_compress          = d_transport['compress']
        d_ret               = {}

        str_serverPath      = d_remote['path']
        str_fileToProcess   = str_serverPath

        b_cleanup           = False
        b_zip               = True

        str_encoding        = 'base64'

        if 'cleanup' in d_compress: b_cleanup = d_compress['cleanup']

        str_archive         = d_compress['archive']
        if str_archive == 'zip':    b_zip = True
        else:                       b_zip = False
        if os.path.isdir(str_serverPath):
            b_zip           = True
            str_archive    = 'zip'

        # If specified (or if the target is a directory), create zip archive
        # of the local path
        if b_zip:
            self.qprint("Zipping target '%s'..." % str_serverPath, comms = 'status')
            d_fio   = zip_process(
                action  = 'zip',
                path    = str_serverPath,
                arcroot = str_serverPath
            )
            d_ret['zip']        = d_fio
            d_ret['status']     = d_fio['status']
            d_ret['msg']        = d_fio['msg']
            d_ret['timestamp']  = '%s' % datetime.datetime.now()
            if not d_ret['status']:
                self.qprint("An error occurred during the zip operation:\n%s" % d_ret['stdout'],
                            comms = 'error')
                self.ret_client(d_ret)
                return d_ret

            str_fileToProcess   = d_fio['fileProcessed']
            str_zipFile         = str_fileToProcess
            d_ret['zip']['filesize']   = '%s' % os.stat(str_fileToProcess).st_size
            self.qprint("Zip file: " + Colors.YELLOW + "%s" % str_zipFile +
                        Colors.PURPLE + '...' , comms = 'status')

        # Encode possible binary filedata in base64 suitable for text-only
        # transmission.
        if 'encoding' in d_compress: str_encoding    = d_compress['encoding']
        if str_encoding     == 'base64':
            self.qprint("base64 encoding target '%s'..." % str_fileToProcess,
                        comms = 'status')
            d_fio   = base64_process(
                action      = 'encode',
                payloadFile = str_fileToProcess,
                saveToFile  = str_fileToProcess + ".b64"
            )
            d_ret['encode']     = d_fio
            d_ret['status']     = d_fio['status']
            d_ret['msg']        = d_fio['msg']
            d_ret['timestamp']  = '%s' % datetime.datetime.now()
            str_fileToProcess   = d_fio['fileProcessed']
            d_ret['encoding']   = {}
            d_ret['encoding']['filesize']   = '%s' % os.stat(str_fileToProcess).st_size
            str_base64File      = str_fileToProcess

        with open(str_fileToProcess, 'rb') as fh:
            filesize    = os.stat(str_fileToProcess).st_size
            self.qprint("Transmitting " + Colors.YELLOW + "{:,}".format(filesize) + Colors.PURPLE +
                        " target bytes from " + Colors.YELLOW +
                        "%s" % (str_fileToProcess) + Colors.PURPLE + '...', comms = 'status')
            self.send_response(200)
            # self.send_header('Content-type', 'text/json')
            self.end_headers()
            # try:
            #     self.wfile.write(fh.read().encode())
            # except:
            self.qprint('<transmission>', comms = 'tx')
            d_ret['transmit']               = {}
            d_ret['transmit']['msg']        = 'transmitting'
            d_ret['transmit']['timestamp']  = '%s' % datetime.datetime.now()
            d_ret['transmit']['filesize']   = '%s' % os.stat(str_fileToProcess).st_size
            d_ret['status']                 = True
            d_ret['msg']                    = d_ret['transmit']['msg']
            self.wfile.write(fh.read())

        if b_cleanup:
            if b_zip:
                self.qprint("Removing '%s'..." % (str_zipFile), comms = 'status')
                if os.path.isfile(str_zipFile):     os.remove(str_zipFile)
            if str_encoding == 'base64':
                self.qprint("Removing '%s'..." % (str_base64File), comms = 'status')
                if os.path.isfile(str_base64File):  os.remove(str_base64File)


        self.ret_client(d_ret)
        self.qprint(d_ret, comms = 'tx')

        return d_ret

    def do_GET_withCopy(self, d_msg):
        """
        Process a "GET" using copy operations

        :return:
        """

        d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_copy              = d_transport['copy']

        str_serverPath      = d_remote['path']
        str_clientPath      = d_local['path']
        str_fileToProcess   = str_serverPath

        b_copyTree          = False
        b_copyFile          = False

        d_ret               = {}
        d_ret['status']     = True

        if not d_copy['symlink']:
            if os.path.isdir(str_serverPath):
                b_copyTree      = True
                str_serverNode  = str_serverPath.split('/')[-1]
                try:
                    shutil.copytree(str_serverPath, os.path.join(str_clientPath, str_serverNode))
                except BaseException as e:
                    d_ret['status'] = False
                    d_ret['msg']    = str(e)
            if os.path.isfile(str_serverPath):
                b_copyFile      = True
                shutil.copy2(str_serverPath, str_clientPath)
        if d_copy['symlink']:
            str_serverNode  = str_serverPath.split('/')[-1]
            try:
                os.symlink(str_serverPath, os.path.join(str_clientPath, str_serverNode))
                b_symlink         = True
            except BaseException as e:
                d_ret['status'] = False
                d_ret['msg']    = str(e)
                b_symlink       = False

        d_ret['source']         = str_serverPath
        d_ret['destination']    = str_clientPath
        d_ret['copytree']       = b_copyTree
        d_ret['copyfile']       = b_copyFile
        d_ret['symlink']        = b_symlink
        d_ret['timestamp']      = '%s' % datetime.datetime.now()

        self.ret_client(d_ret)

        return d_ret

    def log_message(self, format, *args):
        """
        This silences the server from spewing to stdout!
        """
        return

    def do_GET(self):

        d_server            = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
        d_meta              = ast.literal_eval(d_server['meta'])

        d_msg               = {}
        d_msg['action']     = d_server['action']
        d_msg['meta']       = d_meta
        d_transport         = d_meta['transport']

        self.qprint(self.path, comms = 'rx')

        if 'checkRemote'    in d_transport and d_transport['checkRemote']:
            self.qprint('Getting status on server filesystem...', comms = 'status')
            d_ret = self.do_GET_remoteStatus(d_msg)
            return d_ret

        if 'compress'       in d_transport:
            d_ret = self.do_GET_withCompression(d_msg)
            return d_ret

        if 'copy'           in d_transport:
            d_ret = self.do_GET_withCopy(d_msg)
            return d_ret

    def form_get(self, str_verb, data):
        """
        Returns a form from cgi.FieldStorage
        """
        return cgi.FieldStorage(
            IO(data),
            headers =   self.headers,
            environ =
            {
                'REQUEST_METHOD':   str_verb,
                'CONTENT_TYPE':     self.headers['Content-Type'],
            }
        )

    def do_POST(self):

        # Parse the form data posted

        self.qprint(str(self.headers), comms = 'rx')

        length              = self.headers['content-length']
        data                = self.rfile.read(int(length))
        form                = self.form_get('POST', data)
        d_form              = {}
        d_ret               = {
            'msg':      'In do_POST',
            'status':   True,
            'formsize': sys.getsizeof(form)
        }

        for key in form:
            d_form[key]     = form.getvalue(key)

        # d_msg               = json.loads(ast.literal_eval(d_form['d_msg']))
        d_msg               = json.loads((d_form['d_msg']))
        d_meta              = d_msg['meta']

        if 'ctl' in d_meta:
            self.do_POST_serverctl(d_meta)

        if 'transport' in d_meta:
            d_transport     = d_meta['transport']
            if 'compress' in d_transport:
                d_ret = self.do_POST_withCompression(
                    data    = data,
                    length  = length,
                    form    = form,
                    d_form  = d_form
                )
            if 'copy' in d_transport:
                d_ret   = self.do_POST_withCopy(d_meta)

        self.ret_client(d_ret)
        return d_ret

    def do_POST_serverctl(self, d_meta):
        """
        """
        d_ctl               = d_meta['ctl']
        self.qprint('Processing server ctl...', comms = 'status')
        self.qprint(d_meta, comms = 'rx')
        if 'serverCmd' in d_ctl:
            if d_ctl['serverCmd'] == 'quit':
                self.qprint('Shutting down server', comms = 'status')
                d_ret = {
                    'msg':      'Server shut down',
                    'status':   True
                }
                self.qprint(d_ret, comms = 'tx')
                self.ret_client(d_ret)
                os._exit(0)

    def do_POST_withCopy(self, d_meta):
        """
        Process a "POST" using copy operations

        :return:
        """

        # d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_copy              = d_transport['copy']

        str_serverPath      = d_remote['path']
        str_clientPath      = d_local['path']
        str_fileToProcess   = str_serverPath

        b_copyTree          = False
        b_copyFile          = False

        d_ret               = {}
        d_ret['status']     = True

        if not d_copy['symlink']:
            if os.path.isdir(str_clientPath):
                b_copyTree      = True
                str_clientNode  = str_clientPath.split('/')[-1]
                try:
                    shutil.copytree(str_clientPath, os.path.join(str_serverPath, str_clientNode))
                except BaseException as e:
                    d_ret['status'] = False
                    d_ret['msg']    = str(e)
            if os.path.isfile(str_clientPath):
                b_copyFile      = True
                shutil.copy2(str_clientPath, str_serverPath)
            d_ret['copytree']       = b_copyTree
            d_ret['copyfile']       = b_copyFile
        if d_copy['symlink']:
            str_clientNode  = str_clientPath.split('/')[-1]
            try:
                os.symlink(str_clientPath, os.path.join(str_serverPath, str_clientNode))
            except BaseException as e:
                d_ret['status'] = False
                d_ret['msg']    = str(e)
            d_ret['symlink']    = 'ln -s %s %s' % (str_clientPath, str_serverPath)

        # d_ret['d_meta']         = d_meta
        d_ret['source']         = str_clientPath
        d_ret['destination']    = str_serverPath
        d_ret['copytree']       = b_copyTree
        d_ret['copyfile']       = b_copyFile
        d_ret['timestamp']      = '%s' % datetime.datetime.now()

        # self.ret_client(d_ret)

        return d_ret

    def do_POST_withCompression(self, **kwargs):

        # Parse the form data posted

        self.qprint(str(self.headers),              comms = 'rx')
        self.qprint('do_POST_withCompression()',    comms = 'status')

        data    = None
        length  = 0
        form    = None
        d_form  = {}
        d_ret   = {}

        for k,v in kwargs.items():
            if k == 'data':     data    = v
            if k == 'length':   length  = v
            if k == 'form':     form    = v
            if k == 'd_form':   d_form  = v


        d_msg               = json.loads((d_form['d_msg']))
        d_meta              = d_msg['meta']
        #
        # d_meta              = json.loads(d_form['d_meta'])
        fileContent         = d_form['local']
        str_fileName        = d_meta['local']['path']
        str_encoding        = d_form['encoding']

        d_remote            = d_meta['remote']
        b_unpack            = False
        # b_serverPath        = False
        str_unpackBase      = self.server.str_fileBase
        if 'path' in d_remote:
            str_unpackPath  = d_remote['path']
            str_unpackBase  = str_unpackPath + '/'

        d_transport         = d_meta['transport']
        d_compress          = d_transport['compress']
        if 'unpack' in d_compress:
            b_unpack        = d_compress['unpack']

        str_fileOnly        = os.path.split(str_fileName)[-1]
        str_fileSuffix      = ""
        if d_compress['archive'] == "zip":
            str_fileSuffix = ".zip"

        str_localFile   = "%s%s%s" % (str_unpackBase, str_fileOnly, str_fileSuffix)

        if str_encoding == "base64":
            d_ret['decode'] = {}
            data            = base64.b64decode(fileContent)
            try:
                with open(str_localFile, 'wb') as fh:
                    fh.write(data)
            except:
                d_ret['decode']['status']   = False
                d_ret['decode']['msg']      = 'base64 decode unsuccessful!'

                self.ret_client(d_ret)
                self.qprint(d_ret, comms = 'tx')
                return d_ret
        else:
            d_ret['write']   = {}
            with open(str_localFile, 'wb') as fh:
                try:
                    fh.write(fileContent.decode())
                    d_ret['write']['decode'] = True
                except:
                    fh.write(fileContent)
                    d_ret['write']['decode'] = False
            d_ret['write']['file']      = str_localFile
            d_ret['write']['status']    = True
            d_ret['write']['msg']       = 'File written successfully!'
            d_ret['write']['filesize']  = "{:,}".format(os.stat(str_localFile).st_size)
            d_ret['status']             = True
            d_ret['msg']                = d_ret['write']['msg']
        fh.close()
        if b_unpack and d_compress['archive'] == 'zip':
            d_fio   =   zip_process(action          = 'unzip',
                                    path            = str_unpackPath,
                                    payloadFile     = str_localFile)
            d_ret['unzip']  = d_fio
            d_ret['status'] = d_fio['status']
            d_ret['msg']    = d_fio['msg']
            os.remove(str_localFile)

        self.send_response(200)
        self.end_headers()

        d_ret['User-agent'] = self.headers['user-agent']

        # self.ret_client(d_ret)
        self.qprint(d_ret, comms = 'tx')

        return d_ret

    def ret_client(self, d_ret):
        """
        Simply "writes" the d_ret using json and the client wfile.

        :param d_ret:
        :return:
        """
        self.wfile.write(json.dumps(d_ret).encode())


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """
    Handle requests in a separate thread.
    """

    def col2_print(self, str_left, str_right):
        print(Colors.WHITE +
              ('%*s' % (self.LC, str_left)), end='')
        print(Colors.LIGHT_BLUE +
              ('%*s' % (self.RC, str_right)) + Colors.NO_COLOUR)

    def setup(self, **kwargs):
        self.str_fileBase   = "received-"
        self.LC             = 40
        self.RC             = 40

        self.str_unpackDir  = "/tmp/unpack"
        self.b_removeZip    = False
        self.args           = None

        self.dp             = debug(verbosity=0, level=-1)

        for k,v in kwargs.items():
            if k == 'args': self.args   = v

        print(Colors.LIGHT_CYAN + str_desc)

        self.col2_print("Listening on address:",    self.args['ip'])
        self.col2_print("Listening on port:",       self.args['port'])
        self.col2_print("Server listen forever:",   self.args['b_forever'])
        print(Colors.LIGHT_GREEN + "\n\n\tWaiting for incoming data..." + Colors.NO_COLOUR)

def zipdir(path, ziph, **kwargs):
    """
    Zip up a directory.

    :param path:
    :param ziph:
    :param kwargs:
    :return:
    """
    str_arcroot = ""
    for k, v in kwargs.items():
        if k == 'arcroot':  str_arcroot = v

    for root, dirs, files in os.walk(path):
        for file in files:
            str_arcfile = os.path.join(root, file)
            if len(str_arcroot):
                str_arcname = str_arcroot.split('/')[-1] + str_arcfile.split(str_arcroot)[1]
            else:
                str_arcname = str_arcfile
            try:
                ziph.write(str_arcfile, arcname = str_arcname)
            except:
                print("Skipping %s" % str_arcfile)

def zip_process(**kwargs):
    """
    Process zip operations.

    :param kwargs:
    :return:
    """

    str_localPath   = ""
    str_zipFileName = ""
    str_action      = "zip"
    str_arcroot     = ""
    for k,v in kwargs.items():
        if k == 'path':             str_localPath   = v
        if k == 'action':           str_action      = v
        if k == 'payloadFile':      str_zipFileName = v
        if k == 'arcroot':          str_arcroot     = v

    if str_action       == 'zip':
        str_mode        = 'w'
        str_zipFileName = '%s.zip' % uuid.uuid4()
    else:
        str_mode        = 'r'

    ziphandler          = zipfile.ZipFile(str_zipFileName, str_mode, zipfile.ZIP_DEFLATED)
    if str_mode == 'w':
        if os.path.isdir(str_localPath):
            zipdir(str_localPath, ziphandler, arcroot = str_arcroot)
        else:
            if len(str_arcroot):
                str_arcname = str_arcroot.split('/')[-1] + str_localPath.split(str_arcroot)[1]
            else:
                str_arcname = str_localPath
            try:
                ziphandler.write(str_localPath, arcname = str_arcname)
            except:
                ziphandler.close()
                os.remove(str_zipFileName)
                return {
                    'msg':      json.dumps({"msg": "No file or directory found for '%s'" % str_localPath}),
                    'status':   False
                }
    if str_mode     == 'r':
        ziphandler.extractall(str_localPath)
    ziphandler.close()
    return {
        'msg':              '%s operation successful' % str_action,
        'fileProcessed':    str_zipFileName,
        'status':           True,
        'path':             str_localPath,
        'zipmode':          str_mode,
        'filesize':         "{:,}".format(os.stat(str_zipFileName).st_size)
    }

def base64_process(**kwargs):
    """
    Process base64 file io
    """

    str_fileToSave      = ""
    str_action          = "encode"
    data                = None

    for k,v in kwargs.items():
        if k == 'action':           str_action          = v
        if k == 'payloadBytes':     data                = v
        if k == 'payloadFile':      str_fileToRead      = v
        if k == 'saveToFile':       str_fileToSave      = v
        if k == 'sourcePath':       str_sourcePath      = v

    if str_action       == "encode":
        # Encode the contents of the file at targetPath as ASCII for transmission
        if len(str_fileToRead):
            with open(str_fileToRead, 'rb') as f:
                data            = f.read()
                f.close()
        data_b64            = base64.b64encode(data)
        with open(str_fileToSave, 'wb') as f:
            f.write(data_b64)
            f.close()
        return {
            'msg':              'Encode successful',
            'fileProcessed':    str_fileToSave,
            'status':           True
            # 'encodedBytes':     data_b64
        }

    if str_action       == "decode":
        bytes_decoded     = base64.b64decode(data)
        with open(str_fileToSave, 'wb') as f:
            f.write(bytes_decoded)
            f.close()
        return {
            'msg':              'Decode successful',
            'fileProcessed':    str_fileToSave,
            'status':           True
            # 'decodedBytes':     bytes_decoded
        }