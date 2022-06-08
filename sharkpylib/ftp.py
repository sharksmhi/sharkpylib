import ftplib
import pathlib


class Ftp:

    def __init__(self, host=None, user=None, passwd=None):
        self.cred = dict(host=host,
                         user=user,
                         passwd=passwd)

        self.files_to_send = []
        self.subdirs = []

    @property
    def destination(self):
        with ftplib.FTP(**self.cred) as ftp:
            for subdir in self.subdirs:
                ftp.cwd(subdir)
            return ftp.pwd()

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
        with ftplib.FTP(**self.cred) as ftp:
            for subdir in self.subdirs:
                ftp.cwd(subdir)
            for path in self.files_to_send:
                with open(path, 'rb') as fid:
                    ftp.storbinary(f'STOR {path.name}', fid)

