from django.core.management.base import BaseCommand

import environ
import pymysql
import time

from library import debug, shopify

PROCESS = "Product"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.product()

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

    def product(self):
        con = self.con
        csr = con.cursor()

        csr.execute(
            "SELECT ProductID FROM PendingUpdateProduct ORDER BY ProductID ASC")
        products = csr.fetchall()

        for product in products:
            productID = product[0]

            try:
                handle = shopify.UpdateProductToShopify(productID, con)

                csr.execute(
                    "UPDATE Product SET Handle = %s WHERE ProductID = %s", (handle, productID))
                con.commit()

                debug.debug(
                    PROCESS, 0, f"Updated Pending Product : {productID}")
            except Exception as e:
                print(e)
                debug.debug(
                    PROCESS, 1, f"Failed Updating Pending Product : {productID}")
                continue

        csr.close()
