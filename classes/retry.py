from paramiko.ssh_exception import SSHException

class retry:
    def __init__(self, exceptions=None):
        self.exceptions = exceptions or (SSHException,)
    
    def __call__(self, f):
        def wrapped_f(*args):
            try:
                f(*args)
            except self.exceptions as e:
                print("Caught expected exception: " + e)
        return wrapped_f