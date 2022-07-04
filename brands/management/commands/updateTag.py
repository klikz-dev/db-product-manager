from django.core.management.base import BaseCommand

import os
import time
import pymysql

from library import debug, common, shopify

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

debug = debug.debug
backup = common.backup


class Command(BaseCommand):
    help = 'Update Pending Tags'

    def handle(self, *args, **options):
        while True:
            self.updateTag()

            debug("Shopify", 0, "Finished Process. Waiting for next run.")
            time.sleep(60)

    def updateTag(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "SELECT ProductID FROM PendingUpdateTagBodyHTML ORDER BY ProductID")
        products = csr.fetchall()

        for product in products:
            productID = product[0]
            if 1 == 1:
                try:
                    shopify.UpdateTagBodyToShopify(productID, con)
                    debug("Shopify", 0,
                          "Updated Pending Product Tag : {}".format(productID))
                except:
                    debug(
                        "Shopify", 1, "Failed Updating Pending Product Tag : {}".format(productID))
                    continue

        csr.close()
        con.close()
