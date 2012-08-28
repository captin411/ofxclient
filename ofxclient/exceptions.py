class LoginException(Exception):
    def __init__(self,message,code=None,bank=None):
        self.message = message
        self.code = code
        self.bank = bank

    def __str__(self):
        message = "%s : %s" % (self.message,self.bank)
        return message
    
