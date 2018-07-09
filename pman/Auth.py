# A naive Class that implements basic token based auth
import pudb
import configparser

class Auth:
    # Params:
    #       server          : 'socket' | 'http'     --> used to determine how the request needs to be parsed
    #       configLocation: default = "" --> in working directory | otherwise, the path to the .cfg file
    def __init__(self, serverType, configLocation=''):
        self.__tokens    = {}
        self.serverType  = serverType.lower().strip()       # lowercase and no extraneous whitespace
        self.config      = configparser.ConfigParser()
        path             = configLocation
        self.errorMessages = {
400: "Bad Request.",
401: "Unauthorized.",
403: "Forbidden.",
403.1: "Execute access forbidden.",
403.2: "Read access forbidden.",
403.3: "Write access forbidden.",
403.4: "SSL required.",
403.5: "SSL 128 required.",
403.6: "IP address rejected.",
403.7: "Client certificate required.",
403.8: "Site access denied.",
403.9: "Too many users.",
403.10: "Invalid configuration.",
403.11: "Password change.",
403.12: "Invalid configuration.",
403.13: "Client certificate revoked.",
403.14: "Directory listing denied.",
403.15: "Client Access Licenses exceeded.",
403.16: "Client certificate is not trusted or invalid.",
403.17: "Client certificate has expired or is not yet valid.",
403.18: "Cannot execute request from that application pool.",
403.19: "Cannot execute CGIs for the client in this application pool.",
403.20: "Passport logon failed.",
403.21: "Source access denied.",
403.22: "Infinite depth is denied.",
403.502: "Too many requests from the same client IP; Dynamic IP Restriction limit reached."}


        config_key_error = '''
The config file is incorrectly formatted! A key value pair with the following syntax 
must be included in the [AUTH TOKENS] section of your config file:
token = yourToken
'''

        config_section_error = '''
The config file is incorrectly formatted! The config file must have a section named [AUTH TOKENS]
in order to use token authentication.
'''

        server_value_error = '''
%s is not a valid value for the server parameter. Please use one of the following values:
    http
    socket
''' % self.serverType

        if self.serverType != 'http' and self.serverType != 'socket':
            raise ValueError(server_value_error)
            exit(1)
        
        # default case: look for pman_config.cfg or pfioh_config.cfg in the current working directory
        if path == '':
            path = '%s_config.cfg' % self.serverType

        if '.cfg' in path:
            # Read a config file
            self.config.read(path)
            if 'AUTH TOKENS' in self.config:
                if self.config.items('AUTH TOKENS'):
                    for key in self.config['AUTH TOKENS']:
                        token = self.config['AUTH TOKENS'][key].strip()
                        self.__tokens[token] = 'active'
                else:
                    raise ValueError(config_key_error)
                    exit(1)
            else:
                raise ValueError(config_section_error)
                exit(1)
        else:
            # Read an openshift secret
            tokenFile = open(path, 'r')
            for token in tokenFile.readlines():
                self.__tokens[token.strip()] = 'active'
            tokenFile.close()


    def authorizeClientRequest(self, request):
        """
        Checks the authorization permissions of the bearer token passed, and determines whether the sender is permitted to make the request housed in the payload.
        Usage:
            request = The header object from pfioh, or the whole request from pman. This is parsed for the bearer token
        """
        token = ''
        if self.serverType == 'socket':
            token = self.getSocketServerToken(request)
        elif self.serverType == 'http':
            token = self.getHttpServerToken(request)
        if token != '' and token != None:
            if token in self.__tokens:
                if self.__tokens[token] == 'active':
                    return True, ()
                elif self.__tokens[token] == 'revoked':
                    # token has been revoked
                    return False, (401, self.errorMessages[401], "This token has been revoked!")
            else:
                # token is untrusted/invalid
                return False, (401, self.errorMessages[401], "")
        else:
            # token is required, but none was provided
            return False, (400, self.errorMessages[400], "Authentication required! Client did not provide authentication.")

    def getSocketServerToken(self, request):
        # pman's socket server will give you the entire http request as a String
        # parse by newline and strip leading and trailing whitespace
        for line in request.split('\n'):
            if 'Authorization' in line:
                authHeader = line.strip().split()
                return authHeader[-1]
        
        # returns None object if no authorization header
        return None
    
    def getHttpServerToken(self, request):
        # pfioh's httpServer parses the header before hand, it gives you a dictionary of the arguments
        # where the values to the left of the colon in the headers are keys
        if 'Authorization' in request:
            authBody = request['Authorization'].strip()
            return authBody.split()[-1]
        else:
            # returns None object if no authorization header
            return None

