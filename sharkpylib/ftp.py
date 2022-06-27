import ftplib
import pathlib
import socket


class FtpConnectionError(Exception):
    pass


class Ftp:

    def __init__(self, host=None, user=None, passwd=None, status_callback=None):
        self.cred = dict(host=host,
                         user=user,
                         passwd=passwd)

        self.files_to_send = []
        self.subdirs = []
        self.status_callback = status_callback

    @property
    def destination(self):
        try:
            with ftplib.FTP(**self.cred) as ftp:
                for subdir in self.subdirs:
                    ftp.cwd(subdir)
                return ftp.pwd()
        except socket.gaierror:
            return 'Not able to connect to ftp'

    @property
    def server_files(self):
        try:
            with ftplib.FTP(**self.cred) as ftp:
                for subdir in self.subdirs:
                    ftp.cwd(subdir)
                return ftp.nlst()
        except socket.gaierror:
            return []

    def change_directory(self, *args):
        self.subdirs = args

    def add_files_to_send(self, *args):
        if len(args) == 1 and isinstance(args[0], list):
            args = args[0]
        self.files_to_send.extend([pathlib.Path(path) for path in args])

    def send_files(self, files_to_send=None, subdirs=None):
        if files_to_send:
            self.add_files_to_send(*files_to_send)
        if subdirs:
            self.change_directory(*subdirs)
        self._send_files()
        files_to_send = self.files_to_send[:]
        self.files_to_send = []
        return files_to_send

    def _send_files(self):
        tot = len(self.files_to_send)
        try:
            with ftplib.FTP(**self.cred) as ftp:
                for subdir in self.subdirs:
                    ftp.cwd(subdir)
                for i, path in enumerate(self.files_to_send):
                    with open(path, 'rb') as fid:
                        ftp.storbinary(f'STOR {path.name}', fid)
                    if self.status_callback:
                        self.status_callback([i+1, tot])
        except socket.gaierror:
            raise FtpConnectionError 
        except:
            raise 
