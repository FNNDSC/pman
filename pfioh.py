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

    `pfioh.py' is a simple http-based file I/O handler/server, usually started
    by `pman.py'.

    `pfioh.py' handles HTTP REST-like requests on a given port -- it can accept
    incoming file data from a client, and can also return server-side filetrees
    to a client.

    The script assumes that file data is zip'd and base64 encoded.

"""

import  os

from    io              import BytesIO as IO
from    http.server     import BaseHTTPRequestHandler, HTTPServer
from    socketserver    import ThreadingMixIn
import  socket
import  argparse
import  cgi
from    _colors         import Colors
import  zipfile
import  json
import  base64
import  zipfile
import  uuid
import  urllib
import  ast


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
        self.pprint(*args, **kwargs)

    def pprint(self, *args, **kwargs):
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


class StoreHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        """
        """
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

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
            if not self.b_quiet:
                print(Colors.YELLOW + "\nZipping target '%s'..." % str_serverPath + Colors.NO_COLOUR)
            d_ret   = zip_process(
                action  = 'zip',
                path    = str_serverPath,
                arcroot = str_serverPath
            )
            if not d_ret['status']:
                if not self.b_quiet:
                    print(Colors.RED + "An error occurred during the zip operation:\n%s" % d_ret['stdout'])
                return d_ret

            str_fileToProcess   = d_ret['fileProcessed']
            str_zipFile         = str_fileToProcess
            if not self.b_quiet:
                print(Colors.YELLOW + "\nZip file: '%s'..." % str_zipFile + Colors.NO_COLOUR)

        # Encode possible binary filedata in base64 suitable for text-only
        # transmission.
        if 'encoding' in d_compress: str_encoding    = d_compress['encoding']
        if str_encoding     == 'base64':
            if not self.b_quiet:
                print(Colors.YELLOW + "base64 encoding target '%s'..." % str_fileToProcess + Colors.NO_COLOUR)
            d_ret   = base64_process(
                action      = 'encode',
                payloadFile = str_fileToProcess,
                saveToFile  = str_fileToProcess + ".b64"
            )
            str_fileToProcess   = d_ret['fileProcessed']
            str_base64File      = str_fileToProcess

        with open(str_fileToProcess, 'rb') as fh:
            filesize    = os.stat(str_fileToProcess).st_size
            if not self.b_quiet:
                print(Colors.YELLOW + "Transmitting %d target bytes from %s..." %
                      (filesize, str_fileToProcess) + Colors.NO_COLOUR)
            self.send_response(200)
            # self.send_header('Content-type', 'text/json')
            self.end_headers()
            # try:
            #     self.wfile.write(fh.read().encode())
            # except:
            self.wfile.write(fh.read())

        if b_cleanup:
            if b_zip:
                if not self.b_quiet:
                    print(Colors.GREEN + "Removing '%s'..." % (str_zipFile) + Colors.NO_COLOUR)
                if os.path.isfile(str_zipFile):     os.remove(str_zipFile)
            if str_encoding == 'base64':
                if not self.b_quiet:
                    print(Colors.GREEN + "Removing '%s'..." % (str_base64File) + Colors.NO_COLOUR)
                if os.path.isfile(str_base64File):  os.remove(str_base64File)

        return {'status' : True}

    def do_GET(self):

        d_server            = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
        self.b_quiet        = False
        d_meta              = ast.literal_eval(d_server['meta'])

        d_msg               = {}
        d_msg['action']     = d_server['action']
        d_msg['meta']       = d_meta
        d_transport         = d_meta['transport']
        if 'compress' in d_transport: self.do_GET_withCompression(d_msg)


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

        print("\n")
        print(Colors.LIGHT_PURPLE + str(self.headers) + Colors.NO_COLOUR)

        length              = self.headers['content-length']
        data                = self.rfile.read(int(length))

        form                = self.form_get('POST', data)
        d_form              = {}
        for key in form:
            d_form[key]     = form.getvalue(key)

        d_meta              = json.loads(d_form['d_meta'])
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
            data        = base64.b64decode(fileContent)
            try:
                with open(str_localFile, 'wb') as fh:
                    fh.write(data)
            except:
                self.ret_client(
                    {
                        "status":       False,
                        "User-agent":   self.headers['user-agent'],
                        "d_meta":       d_meta,
                        "stderr":       "Could not access server path!"
                    }
                )
                return

        else:
            # print(d_meta)
            with open(str_localFile, 'wb') as fh:
                try:
                    fh.write(fileContent.decode())
                except:
                    fh.write(fileContent)
        fh.close()
        if b_unpack and d_compress['archive'] == 'zip':
            zip_process(action          = 'unzip',
                        path            = str_unpackPath,
                        payloadFile     = str_localFile)
            os.remove(str_localFile)

        self.send_response(200)
        self.end_headers()

        self.ret_client(
            {
                "status":       True,
                "User-agent":   self.headers['user-agent'],
                "d_meta":       d_meta
            }
        )

        return

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
                    'stdout':   json.dumps({"msg": "No file or directory found for '%s'" % str_localPath}),
                    'status':   False
                }
    if str_mode     == 'r':
        ziphandler.extractall(str_localPath)
    ziphandler.close()
    return {
        'stdout':           '',
        'fileProcessed':    str_zipFileName,
        'status':           True,
        'path':             str_localPath,
        'zipmode':          str_mode
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
            'stdout':           'Encode successful',
            'fileProcessed':    str_fileToSave,
            'status':           True,
            'encodedBytes':     data_b64
        }

    if str_action       == "decode":
        bytes_decoded     = base64.b64decode(data)
        with open(str_fileToSave, 'wb') as f:
            f.write(bytes_decoded)
            f.close()
        return {
            'stdout':           'Decode successful',
            'fileProcessed':    str_fileToSave,
            'status':           True,
            'decodedBytes':     bytes_decoded
        }


def main():
    str_defIP = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

    parser  = argparse.ArgumentParser(description = str_desc)

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
        default = '5055',
        help    = 'Port to use.'
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
    parser.add_argument(
        '--forever',
        help    = 'if specified, serve forever, otherwise terminate after single service.',
        dest    = 'b_forever',
        action  = 'store_true',
        default = False
    )

    args            = parser.parse_args()
    args.port       = int(args.port)

    print(vars(args))
    server          = ThreadedHTTPServer((args.ip, args.port), StoreHandler)
    server.setup(args = vars(args))

    if args.b_forever:
        server.serve_forever()
    else:
        server.handle_request()
    
if __name__ == "__main__":
    main()
        
