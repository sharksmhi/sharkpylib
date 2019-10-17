# ==============================================================================
class SharkpylibException(Exception):
    """
    Created     20190930
    Updated

    Blueprint for error message.
    code is for external mapping of exceptions. For example if a GUI wants to
    handle the error text for different languages.
    """
    code = None
    message = ''

    def __init__(self, message='', code=''):
        self.message = '{}: {}'.format(self.message, message)
        if code:
            self.code = code


# ==============================================================================
class MissingInformation(SharkpylibException):
    """
    Created     20190930
    """
    code = ''
    message = ''


# ==============================================================================
class NonMatchingInformation(SharkpylibException):
    """
    Created     20191001
    """
    code = ''
    message = ''


# ==============================================================================
class NonMatchingData(SharkpylibException):
    """
    Created     20191001
    """
    code = ''
    message = ''


# ==============================================================================
class MissingMappingFile(SharkpylibException):
    """
    Created     20191001
    """
    code = ''
    message = ''