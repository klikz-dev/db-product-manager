from django.core.management.base import BaseCommand

import environ
import pymysql
import time

from library import debug, shopify

PROCESS = "Price"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.price()

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

    def price(self):
        con = self.con
        csr = con.cursor()

        productIDs = []
        csr.execute("SELECT ProductID FROM ProductVariant WHERE Price < 19.99 AND ProductID IS NOT NULL AND IsDefault = 1 AND ProductID IN (SELECT ProductID FROM Product WHERE Published = 1)")
        for row in csr.fetchall():
            productIDs.append(str(row[0]))

        for productID in productIDs:
            csr.execute(
                "UPDATE ProductVariant SET Price = 19.99 WHERE ProductID = {} AND IsDefault = 1".format(productID))
            csr.execute(
                "UPDATE ProductVariant SET Price = 16.99 WHERE ProductID = {} AND Name LIKE 'Trade%'".format(productID))
            con.commit()
            try:
                csr.execute(
                    "Call AddToPendingUpdatePrice ()".format(productID))
                con.commit()
            except:
                continue

        variantIDs = []
        csr.execute("SELECT VariantID FROM Product P JOIN ProductVariant PV ON P.ProductID = PV.ProductID WHERE PV.Name LIKE 'Trade%' AND PV.Published = 1 AND P.IsOutlet = 1 AND P.Published = 1")
        for row in csr.fetchall():
            variantIDs.append(row[0])

        for variantID in variantIDs:
            try:
                shopify.DeleteVariantByVariantID(variantID)
            except:
                continue

            csr.execute(
                "UPDATE ProductVariant SET Published = 0 WHERE VariantID = {}".format(variantID))
            con.commit()

        csr.execute(
            "SELECT ProductID FROM PendingUpdatePrice ORDER BY ProductID ASC")
        products = csr.fetchall()
        for product in products:
            productID = product[0]
            try:
                shopify.UpdatePriceToShopify(productID, con)
                debug.debug(PROCESS, 0,
                            "Updated Price for Product: {}".format(productID))
            except Exception as e:
                print(e)
                continue

        csr.close()
