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

    def do_GET(self):
        if self.path == '/':
            with open(self.store_path) as fh:
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                self.wfile.write(fh.read().encode())

    def do_POST(self):

        # Parse the form data posted


        print("\n")
        print(Colors.LIGHT_PURPLE + str(self.headers) + Colors.NO_COLOUR)

        str_contentType     = self.headers['content-type']
        length              = self.headers['content-length']
        data                = self.rfile.read(int(length))
        l_contentType       = str_contentType.split()
        str_boundary        = l_contentType[1]
        str_boundaryOnly    = str_boundary.split("=")[1]
        print(str_boundaryOnly)

        form = cgi.FieldStorage(
            IO(data),
            headers =   self.headers,
            environ =
                {
                    'REQUEST_METHOD':'POST',
                    'CONTENT_TYPE':    self.headers['Content-Type'],
                }
            )

        d_form          = {}
        for key in form:
            d_form[key] = form.getvalue(key)
        print(d_form.keys())
        print(d_form['d_meta'])


        print(self.headers['Content-Type'])
        d_meta          = json.loads(d_form['d_meta'])
        fileContent     = d_form['file']
        str_fileName    = d_meta['file']['path']
        str_encoding    = d_form['encoding']

        str_fileOnly    = os.path.split(str_fileName)[-1]
        str_fileSuffix  = ""
        if 'file' in d_meta: d_file = d_meta['file']
        if d_file['compress'] == "zip":
            str_fileSuffix = ".zip"

        str_localFile   = "%s%s%s" % (self.server.str_fileBase, str_fileOnly, str_fileSuffix)

        if str_encoding == "base64":
            data        = base64.b64decode(fileContent)
            with open(str_localFile, 'wb') as fh:
                fh.write(data)
        else:
            # print(d_meta)
            with open(str_localFile, 'wb') as fh:
                try:
                    fh.write(fileContent.decode())
                except:
                    fh.write(fileContent)
        fh.close()
        self.send_response(200)
        self.end_headers()

        d_ret = {
            "status":       True,
            "User-agent":   self.headers['user-agent'],
            "d_meta":       d_meta
        }

        self.wfile.write(json.dumps(d_ret).encode())
        return

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

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            try:
                ziph.write(os.path.join(root, file))
            except:
                print("Skipping %s" % os.path.join(root, file))

def zip_process(**kwargs):
    """
    Process zip operations.

    :param kwargs:
    :return:
    """

    str_sourcePath  = ""
    str_action      = "zip"
    for k,v in kwargs.items():
        if k == 'path':   str_sourcePath  = v
        if k == 'action': str_action      = v

    if str_action       == 'zip':
        str_mode        = 'w'
    else:
        str_mode        = 'r'
    str_zipFileName     = '%s.zip' % uuid.uuid4()
    ziphandler          = zipfile.ZipFile(str_zipFileName, str_mode, zipfile.ZIP_DEFLATED)
    if os.path.isdir(str_sourcePath):
        zipdir(str_sourcePath, ziphandler)
    else:
        try:
            ziphandler.write(str_sourcePath)
        except:
            ziphandler.close()
            os.remove(str_zipFileName)
            return {
                'stdout':   json.dumps({"msg": "No file or directory found for '%s'" % str_sourcePath}),
                'status':   False
            }
    ziphandler.close()
    return {
        'stdout':           '',
        'fileProcessed':    str_zipFileName,
        'status':           True
    }

def base64_process(**kwargs):
    """
    Process base64 file io
    """

    str_fileToProcess   = ""
    str_action          = "encode"

    for k,v in kwargs.items():
        if k == 'path':   str_fileToProcess   = v
        if k == 'action': str_action          = v

    # Now encode the zip as ASCII for transmission
    with open(str_fileToProcess, 'rb') as f:
        data            = f.read()
        f.close()
    data_b64            = base64.b64encode(data)
    str_fileToProcess   = '%s.b64' % str_fileToProcess
    with open(str_fileToProcess, 'wb') as f:
        f.write(data_b64)
        f.close()
    return {
        'stdout':           '',
        'fileProcessed':    str_fileToProcess,
        'status':           True
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
        
