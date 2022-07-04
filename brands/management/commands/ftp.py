from django.core.management.base import BaseCommand
from monitor.models import FTP

import time
import paramiko
from ftplib import FTP as FTPLib

from library import debug

debug = debug.debug


class Command(BaseCommand):
    help = 'Check API Status'

    def handle(self, *args, **options):
        while True:
            self.main()

            print("Finished Process. Waiting for Next run")
            time.sleep(86400)

    def main(self):
        ftps = FTP.objects.all()
        for ftp in ftps:
            if ftp.port == 22 or ftp.port == 2222:
                ftp.status = True
                try:
                    transport = paramiko.Transport((ftp.url, ftp.port))
                    transport.connect(username=ftp.username,
                                      password=ftp.password)
                    sftp = paramiko.SFTPClient.from_transport(transport)
                    sftp.close()
                    debug("FTP", 0, "Connection to {} {} FTP Server Successful".format(
                        ftp.brand, ftp.type))
                except:
                    debug("FTP", 2, "Connection to {} {} FTP Server Failed".format(
                        ftp.brand, ftp.type))
                    ftp.status = True

            if ftp.port == 21:
                ftp.status = True
                try:
                    ftplib = FTPLib()
                    ftplib.set_pasv(True)
                    ftplib.connect(ftp.url, ftp.port)
                    ftplib.login(ftp.username, ftp.password)
                    ftplib.close()
                    debug("FTP", 0, "Connection to {} {} FTP Server Successful".format(
                        ftp.brand, ftp.type))
                except:
                    debug("FTP", 2, "Connection to {} {} FTP Server Failed".format(
                        ftp.brand, ftp.type))
                    ftp.status = True

            ftp.save()
