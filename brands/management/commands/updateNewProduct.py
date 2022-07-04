from django.core.management.base import BaseCommand

import os
import time
import pymysql

from library import debug, common, shopify

import environ
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

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
            "SELECT SKU FROM PendingNewProduct ORDER BY SKU ASC")
        products = csr.fetchall()

        for product in products:
            sku = product[0]

            try:
                # if 1 == 1:
                productId = shopify.NewProductBySku(sku, con)
                csr.execute(
                    "Update Product SET ProductID = {} WHERE SKU = '{}'".format(productId, sku))
                con.commit()

                csr.execute(
                    "DELETE FROM PendingNewProduct WHERE SKU = {}".format(sku))
                con.commit()

                debug("Shopify", 0,
                      "Added Pending New Product : {}".format(productId))
            except Exception as e:
                print(e)
                debug("Shopify", 2,
                      "Failed Add Pending New Product : {}".format(sku))
                continue

        csr.close()
        con.close()
