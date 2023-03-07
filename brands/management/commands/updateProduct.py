from django.core.management.base import BaseCommand

import os
import time
import pymysql
import random

from library import debug, common, shopify

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))
aws_access_key = env('aws_access_key')
aws_secret_key = env('aws_secret_key')

debug = debug.debug
backup = common.backup


class Command(BaseCommand):
    help = 'Backup Database'

    def handle(self, *args, **options):
        while True:
            self.UpdateProduct()

            debug("Shopify", 0, "Finished Process. Waiting for next run.")
            time.sleep(60)

    def UpdateProduct(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "SELECT ProductID FROM PendingUpdateProduct ORDER BY ProductID ASC")
        products = csr.fetchall()

        for product in products:
            productID = product[0]

            try:
                shopify.UpdateProductToShopify(productID, con)
                debug("Shopify", 0,
                      "Updated Pending Product : {}".format(productID))
            except Exception as e:
                print(e)
                debug("Shopify", 2,
                      "Failed Updating Pending Product : {}".format(productID))
                continue

        csr.close()
        con.close()
