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
aws_access_key = env('aws_access_key')
aws_secret_key = env('aws_secret_key')

debug = debug.debug
backup = common.backup


class Command(BaseCommand):
    help = 'Update Pending Price'

    def handle(self, *args, **options):
        while True:
            self.updatePrice()

            debug("Shopify", 0, "Finished Process. Waiting for next run.")
            time.sleep(60)

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        productIDs = []
        csr.execute("SELECT ProductID FROM ProductVariant WHERE Price < 19.99 AND ProductID IS NOT NULL AND IsDefault = 1 AND ProductID IN (SELECT ProductID FROM Product WHERE Published = 1)")
        for row in csr.fetchall():
            productIDs.append(str(row[0]))

        for productID in productIDs:
            csr.execute(
                "UPDATE ProductVariant SET Price = 19.99 WHERE ProductID = {} AND IsDefault = 1".format(productID))
            csr.execute(
                "UPDATE ProductVariant SET Price = 16.99 WHERE ProductID = {} AND Name LIKE 'Trade - %'".format(productID))
            con.commit()
            try:
                csr.execute(
                    "Call AddToPendingUpdatePrice ()".format(productID))
                con.commit()
            except:
                continue

        variantIDs = []
        csr.execute("SELECT VariantID FROM Product P JOIN ProductVariant PV ON P.ProductID = PV.ProductID WHERE PV.Name LIKE 'Trade - %' AND PV.Published = 1 AND P.IsOutlet = 1 AND P.Published = 1")
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
                debug("Shopify", 0,
                      "Updated Price for Product: {}".format(productID))
            except:
                continue

        csr.close()
        con.close()
