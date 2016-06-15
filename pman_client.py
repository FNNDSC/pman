#!/usr/bin/env python

'''

Send simple messages to pman server.

'''
# Author - Kasun Herath <kasunh01 at gmail.com>
# Source - https://github.com/kasun/zeromq-client-server.git


from __future__ import print_function

import  threading
import  zmq
import  argparse
from    _colors     import  Colors

class Client(threading.Thread):
    ''' Represents an example client. '''
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)

        for key,val in kwargs.iteritems():
            if key == 'id':         self.identity       = val
            if key == 'msg':        self.str_msg        = val
            if key == 'protocol':   self.str_protocol   = val
            if key == 'ip':         self.str_IP         = val
            if key == 'port':       self.str_port       = val

        print(Colors.LIGHT_GREEN)
        print("""
        \t+---------------------------------+
        \t| Welcome to the pman client test |
        \t+---------------------------------+
        """)
        print(Colors.CYAN + """
        This program sends MSG payloads to a 'pman' listener
        """)

        print(Colors.WHITE + "\t\tWill transmit to: " + Colors.LIGHT_BLUE, end='')
        print('%s://%s:%s' % (self.str_protocol, self.str_IP, self.str_port))

        self.zmq_context = zmq.Context()

    def run(self):
        ''' Connects to server. Send message, poll for and print result to standard out. '''
        print(Colors.LIGHT_PURPLE + 'Client ID - %s. msg to transmit - %s ' % (self.identity, self.str_msg))
        socket = self.connection_get()
        
        # Poller is used to check for availability of data before reading from a socket.
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        self.send(socket, '%s' % (self.str_msg))

        # Infinitely poll for the result. 
        # Polling is used to check for sockets with data before reading because socket.recv() is blocking.
        while True:
            # Poll for 5 seconds. Return any sockets with data to be read.
            sockets = dict(poller.poll(5000))

            # If socket has data to be read.
            if socket in sockets and sockets[socket] == zmq.POLLIN:
                result = self.receive(socket)
                print('Client ID - %s. Received result - %s.' % (self.identity, result))
                break

        socket.close()
        self.zmq_context.term()

    def send(self, socket, data):
        ''' Send data through provided socket. '''
        socket.send(data)

    def receive(self, socket):
        ''' Recieve and return data through provided socket. '''
        return socket.recv()

    def connection_get(self):
        ''' Create a zeromq socket of type DEALER; set it's identity, connect to server and return socket. '''

        # Socket type DEALER is used in asynchronous request/reply patterns.
        # It prepends identity of the socket with each message.
        socket = self.zmq_context.socket(zmq.DEALER)
        socket.setsockopt(zmq.IDENTITY, self.identity)
        socket.connect('%s://%s:%s' % (self.str_protocol, self.str_IP, self.str_port))
        return socket

if __name__ == '__main__':

    parser  = argparse.ArgumentParser(description = 'simple client for talking to pman')

    parser.add_argument(
        '--msg',
        action  = 'store',
        dest    = 'msg',
        default = '',
        help    = 'Message to send to pman instance.'
    )
    parser.add_argument(
        '--id',
        action  = 'store',
        dest    = 'id',
        default = "1",
        help    = 'ID of client.'
    )
    parser.add_argument(
        '--ip',
        action  = 'store',
        dest    = 'ip',
        default = '127.0.0.1',
        help    = 'IP to connect.'
    )
    parser.add_argument(
        '--port',
        action  = 'store',
        dest    = 'port',
        default = '5010',
        help    = 'Port to use.'
    )
    parser.add_argument(
        '--protocol',
        action  = 'store',
        dest    = 'protocol',
        default = 'tcp',
        help    = 'Protocol to use.'
    )

    args    = parser.parse_args()
    client  = Client(
                        id          = args.id,
                        msg         = args.msg,
                        protocol    = args.protocol,
                        ip          = args.ip,
                        port        = args.port
                )
    client.start()

