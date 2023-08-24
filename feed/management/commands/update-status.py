from django.core.management.base import BaseCommand

import environ
import pymysql
import time

from library import debug, shopify

PROCESS = "Status"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.status()
                    processor.noImage()

                print("Finished process. Waiting for next run. {}:{}".format(
                    PROCESS, options['functions']))
                time.sleep(3600)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def status(self):
        con = self.con
        csr = con.cursor()

        csr.execute(
            "SELECT ProductID FROM PendingUpdatePublish ORDER BY ProductID ASC")
        products = csr.fetchall()
        for product in products:
            productID = product[0]
            try:
                debug.debug(
                    PROCESS, 0, f"Updated Pending Publishment Status of Product: {productID}")
                shopify.UpdatePublishToShopify(productID, con)
            except:
                continue

        csr.close()

    def noImage(self):
        con = self.con
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
                    f"UPDATE Product SET Published = 0 WHERE ProductID = {productID}")
                con.commit()

                debug.debug(
                    PROCESS, 0, f"Unpublished Product: {productID} because it doesn't have image.")
            except:
                continue

        csr.close()
