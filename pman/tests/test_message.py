from unittest import TestCase

from pman import Message
from pman import Colors

class TestMessage(TestCase):
    def test_message_constructor(self):
        message1 = Message()
        message2 = Message()

        message1.syslog(True)
        message1(Colors.RED + Colors.WHITE_BCKGRND + 'hello world!\n' + Colors.NO_COLOUR)

        # Send message via datagram to 'pangea' on port '1701'.
        # message1.to('pangea:1701')
        # message1('hello, pangea!\n');
        # message1('this has been sent over a datagram socket...\n')

        # Now for some column width specs and 'debug' type messages
        # These will all display on the console since debug=5 and the
        # message1.verbosity(10) means that all debug tagged messages with
        # level less-than-or-equal-to 10 will be passed.
        message1.to('stdout')
        message1.verbosity(10)
        message1('starting process 1...', lw=90, debug=5)
        message1('[ ok ]\n', rw=20, syslog=False, debug=5)
        message1('parsing process 1 outputs...', lw=90, debug=5)
        message1('[ ok ]\n', rw=20, syslog=False, debug=5)
        message1('preparing final report...', lw=90, debug=5)
        message1('[ ok ]\n', rw=20, syslog=False, debug=5)

        message2.to('/tmp/message2.log')
        message2.tee(True)
        # A verbosity level of message2.verbosity(1) and a
        # message2.to(sys.stdout) will not output any of the 
        # following since the debug level for each message 
        # is set to '5'. The verbosity should be at least
        # message2.verbosity(5) for output to appear on the
        # console.
        # 
        # If message2.tee(True) and message2.to('/tmp/message2.log')
        # then all messages will be displayed regardless
        # of the internal verbosity level.
        message2.verbosity(1)   
        message2('starting process 1...', lw=90, debug=5)
        message2('[ ok ]\n', rw=20, syslog=False, debug=5)
        message2('parsing process 1 outputs...', lw=90, debug=5)
        message2('[ ok ]\n', rw=20, syslog=False, debug=5)
        message2('preparing final report...', lw=90, debug=5)
        message2('[ ok ]\n', rw=20, syslog=False, debug=5)

        message1.to('/tmp/test.log')
        message1('and now to /tmp/test.log\n')

        message2.to(open('/tmp/test2.log', 'a'))
        message2('another message to /tmp/test2.log\n')
        message2.tagstring('MARK-->')
        message2('this text is tagged\n')
        message2('and so is this text\n')
        
        message1.clear()
        message1.append('this is message ')
        message1.append('that is constructed over several ')
        message1.append('function calls...\n')
        message1.to('stdout')
        message1()

        message2.tag(False)
        message2('goodbye!\n')

        # didn't crash
        self.assertTrue(True)
