from django.core.management.base import BaseCommand

from library import debug, common

import time

debug = debug.debug
backup = common.backup


class Command(BaseCommand):
    help = 'Backup Database'

    def handle(self, *args, **options):
        self.main()

        print("Finished Process. Waiting for Next run")
        time.sleep(86400)

    def main(self):
        backup()
