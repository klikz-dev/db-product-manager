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
            self.UpdatePublish()
            self.UnpublishProductNoImage()

            debug("Shopify", 0, "Finished Process. Waiting for next run.")
            time.sleep(60)

    def UpdatePublish(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "SELECT ProductID FROM PendingUpdatePublish ORDER BY ProductID ASC")
        products = csr.fetchall()
        for product in products:
            productID = product[0]
            try:
                debug("Shopify",
                      0, "Updated Pending Publishment Status of Product: {}".format(productID))
                shopify.UpdatePublishToShopify(productID, con)
            except:
                continue

        csr.close()
        con.close()

    def UnpublishProductNoImage(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "SELECT ProductID FROM Product WHERE ProductID NOT IN (SELECT ProductID FROM ProductImage WHERE ImageIndex = 1) AND Published = 1")
        products = csr.fetchall()
        for product in products:
            productID = product[0]
            try:
                shopify.UpdateProductByProductID(
                    productID, {"id": productID, "published": False})

                csr.execute(
                    "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                con.commit()

                debug("Shopify",
                      0, "Unpublished Product: {} because it doesn't have image.".format(productID))
            except:
                continue

        csr.close()
        con.close()
