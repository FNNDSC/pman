# NAME
#
#	C_mail
#
# DESCRIPTION
#
#	'C_mail' is a simple class for handling/abstracting common
#	email related activities.
#
#	Once setup with address lists, and/or subject text
#	it sends body text and inline attachments.
#
# HISTORY
#
# 11 January 2007
# o Initial development implementation.
#

# System imports
import 	os
import 	os.path
import 	sys
import	string
import	datetime
import	smtplib
from 	cgi 			import 	*
from 	email.MIMEImage 	import 	MIMEImage
from	email.MIMEText		import	MIMEText
from 	email.MIMEMultipart 	import 	MIMEMultipart

# 3rd party imports
#from 	configobj 		import 	ConfigObj

# SCIN imports
#from _common.systemMisc import *
#import	systemMisc

class C_mail :
	# 
	# Member variables
	#
	# 	- Core variables - generic
	mstr_obj	= 'C_mail';		# name of object class
        mstr_name	= 'void';		# name of object variable
	mstr_def	= 'void';		# name of function being processed
        m_id		= -1; 			# id of agent
        m_iter		= 0;			# current iteration in an
                                		# 	arbitrary processing 
						#	scheme
        m_verbosity	= 0;			# debug related value for 
						#	object
        m_warnings	= 0;              	# show warnings 
						#	(and warnings level)
	
	#
	#	- Class variables
	#	Core variables - specific
	#
	mlstr_to	= []			# recipient list
	mstr_from	= ""			# from string
	mstr_subject	= ""			# subject string
	mstr_body	= ""			# body text
	mlstr_attach	= []			# list of files to attach
	mstr_SMTPserver	= "localhost"
	
	def to_set(self, alstr_to):
		self.mlstr_to		= alstr_to
		
	def from_set(self, astr_from):
		self.mstr_from		= astr_from
		
	def subject_set(self, astr_subject):
		self.mstr_subject	= astr_subject
		
	def body_set(self, astr_body):
		self.mstr_body		= astr_body
		
	def attach_set(self, alstr_attach):
		self.mlstr_attach	= alstr_attach
		
	def SMTPserver_set(self, astr_STMPserver):
		self.mstr_SMTPserver
	
	#
	# Methods
	#
	# Core methods - construct, initialise, id
	
	def error_exit(		self,
				astr_action,
				astr_error,
				aexitCode):
	    print "%s:: FATAL ERROR" % self.mstr_obj
	    print "\tSorry, some error seems to have occurred in <%s::%s>" \
	    		% (self.mstr_obj, self.mstr_def)
	    print "\tWhile %s" 					% astr_action
	    print "\t%s"					% astr_error
	    print ""
	    print "Returning to system with error code %d"	% aexitCode
	    sys.exit(aexitCode)
	    
	def core_construct(	self,
				astr_obj	= 'C_mail',
				astr_name	= 'void',
				a_id		= -1,
				a_iter		= 0,
				a_verbosity	= 0,
				a_warnings	= 0) :
		self.mstr_obj		= astr_obj
		self.mstr_name		= astr_name
		self.m_id		= a_id
		self.m_iter		= a_iter
		self.m_verbosity	= a_verbosity
		self.m_warnings		= a_warnings
	
	def reconstruct(self, 	alstr_to	= "",
				astr_from	= "",
				astr_subject	= "",
				astr_body	= "",
				alstr_attach	= ""
		):
		mlstr_to	= alstr_to
		mstr_from	= astr_from
		mstr_subject	= astr_subject
		mstr_body	= astr_body
		mlstr_attach	= alstr_attach
	
	def __init__(self, 	 **header):
	    #
	    # PRECONDITIONS
	    # o None - all arguments are optional
	    #
	    # POSTCONDITIONS
	    # o Any arguments specified in the **header are
	    #	used to initialize internal variables.	    
	    #	
	    self.core_construct()
	    # Initialize to class definition variables
	    lstr_to	= self.mlstr_to
	    str_from	= self.mstr_from
	    str_subject	= self.mstr_subject
	    str_body	= self.mstr_body
	    lstr_attach	= self.mlstr_attach
	    # Now override any that are spec'd in the **header
	    for field in header.keys():
	    	if field == 'to':	lstr_to		= header[field]
	    	if field == 'from':	str_from	= header[field]
	    	if field == 'subject':	str_subject	= header[field]
	    	if field == 'body':	str_body	= header[field]
	    	if field == 'attach':	lstr_attach	= header[field]
	    self.reconstruct(	lstr_to,
				str_from,
				str_subject,
				str_body,
				lstr_attach)
		    
	def __str__(self):
		print 'mstr_obj\t\t= %s' 	% self.mstr_obj
		print 'mstr_name\t\t= %s' 	% self.mstr_name
		print 'm_id\t\t\t= %d' 		% self.m_id
		print 'm_iter\t\t\t= %d'	% self.m_iter
		print 'm_verbosity\t\t= %d'	% self.m_verbosity
		print 'm_warnings\t\t= %d'	% self.m_warnings
		return 'This class implements simple functionality.'
	
	def internals_check(self):
	    #
	    # POSTCONDITIONS
	    # o If mstr_SMTPserver is zero length (i.e. not set), script
	    #	will terminate
	    #
	    if not len(self.mstr_SMTPserver):
		self.error_exit('running ::internals_check()',
				'it seems that the SMTP server has not been set.',
				1)
		    		    				  
	def send(self):
	    #
	    # PRECONDITIONS
	    # o Internal components should be defined. At the very least
	    #	this include:
	    #
	    #	    - mstr_body
	    #	    - mlstr_to
	    #
	    # POSTCONDITIONS
	    # o Thin dispatching layer to smtp_process()
	    # o Is used to present a uniform API
	    #
	     
	    #self.debug_trace("Entering C_mail::send()")		
	    self.smtp_process(	self.mlstr_to, 
	    			self.mstr_from, 
				self.mstr_subject,
				self.mstr_body,
				self.mlstr_attach) 
	    #self.debug_trace("Leaving  C_mail::send()")
		    
	def send(self, **header):
	    #
	    # PRECONDITIONS
	    # 	**header:
	    #
	    #		'from', 'subject', 'body' 	: strings
	    #		'to', 'attach'			: list of strings
	    #
	    #
	    # POSTCONDITIONS
	    #  	For each non-zero length input argument in 
	    #	'header', temporarily ignore any internals and
	    #	send a message using these overrides.
	    #
	    	 
	    #self.debug_trace("Entering C_mail::send()")
	    
	    lstr_to	= self.mlstr_to
	    str_from	= self.mstr_from
	    str_subject	= self.mstr_subject
	    str_body	= self.mstr_body
	    lstr_attach	= self.mlstr_attach
	    
	    for field in header.keys():
		if field == 'to':	lstr_to		= header[field]
		if field == 'sender':	str_from	= header[field]
	    	if field == 'subject':	str_subject	= header[field]
		if field == 'body':	str_body	= header[field]
		if field == 'attach':	lstr_attach	= header[field]
		
		
	    self.smtp_process(	lstr_to, str_from, str_subject, 
	    			str_body, lstr_attach)
	    #self.debug_trace("Leaving  C_mail::send()")
	    
	def smtp_process(self, 	alstr_to,
				astr_from,
				astr_subject,
				astr_body,
				alstr_attach):
	    #
	    # PRECONDITIONS
	    # o Should only be called by one of the send() methods
	    # o Assumes that any attachments are valid files
	    #
	    # POSTCONDITIONS
	    # o Interacts with the SMTPlib module
	    #
	    
	    self.internals_check()

	    msg 		= MIMEMultipart()
	    msg['Subject'] 	= astr_subject
	    msg['From']		= astr_from
	    msg.preamble 	= "This is a mult-part message in MIME format."
	    msg.attach(MIMEText(astr_body))
	    msg.epilogue 	= ''
	
	    for file in alstr_attach:
		fp = open(file, 'rb')
		img = MIMEImage(fp.read())
		img.add_header('Content-ID', file)
		fp.close()
		msg.attach(img)
	
	    smtp 		= smtplib.SMTP()
	    smtp.connect(self.mstr_SMTPserver)
	    for str_to in alstr_to:
		msg['To']	= str_to
	    	smtp.sendmail(astr_from, str_to, msg.as_string())
	    smtp.close()	    
	        		  
	    		

	    
