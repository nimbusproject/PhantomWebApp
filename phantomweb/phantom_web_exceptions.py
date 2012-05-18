class PhantomWebException(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message


class PhantomRedirectException(Exception):

    def __init__(self, location, message):
        Exception.__init__(self, message)
        self.message = message
        self.redir = location
