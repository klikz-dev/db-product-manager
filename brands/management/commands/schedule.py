from django.core.management.base import BaseCommand
from monitor.models import Schedule

import subprocess

class Command(BaseCommand):
    help = 'Check API Status'

    def handle(self, *args, **options):
        output = subprocess.run(['ls', '-l'], capture_output=True, text=True)
        output.stdout.decode('utf-8')
        # print(output)
