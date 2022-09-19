from paramiko.ssh_exception import SSHException, NoValidConnectionsError
from socket import timeout

from .logger import Logger


class retry:
    """Decorator used to automatically retry operations throwing exceptions
    """
    def __init__(self, exceptions: tuple[BaseException] = None):
        """Initializing the retry decorator

        Args:
            exceptions (tuple, optional): A tuple containing exception classes
              that should be handled by the decorator. If none, handle only
              paramiko.ssh_exception.SSHException/NoValidConnectionsError and
              socket.timeout/TimeoutError. Defaults to None.
        """
        self.exceptions = exceptions or (SSHException, NoValidConnectionsError,
                                         timeout, TimeoutError)
        self._logger = Logger()
    
    def __call__(self, f):
        """Return a function through the retry decorator

        Args:
            f (function): Function to wrap in the decorator

        Returns:
            function: Function wrapping the passed function
        """
        def wrapped_f(*args, **kwargs):
            while True:
                try:
                    return f(*args, **kwargs)
                except self.exceptions as e:
                    self._logger.info("Caught expected exception: " + repr(e))

        return wrapped_f