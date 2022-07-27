import time
from django.core.management.base import BaseCommand
from django.db.models import Max
import os

from library import debug, shopify, common

from shopify.models import Order

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

debug = debug.debug

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Sync Mysql and Shopify'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "main" in options['functions']:
            while True:
                self.main()
                print("Completed process. Waiting for next run.")
                time.sleep(300)

    def main(self):
        lastOrderId = Order.objects.aggregate(Max('shopifyOrderId'))[
            'shopifyOrderId__max']

        ordersRes = shopify.getNewOrders(lastOrderId)

        for order in ordersRes['orders']:
            common.importOrder(order)
