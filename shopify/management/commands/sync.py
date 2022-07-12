from django.core.management.base import BaseCommand

import os
import pymysql

from library import debug, shopify, common

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
            self.main()

    def main(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "SELECT MAX(ShopifyOrderID) FROM Orders")
        row = csr.fetchone()
        lastOrderId = row[0]

        ordersRes = shopify.getNewOrders(lastOrderId)

        for order in ordersRes['orders']:
            common.importOrder(order, con)

        csr.close()
        con.close()
