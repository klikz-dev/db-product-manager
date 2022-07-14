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

key = ["f9082681e6acd5bd8a8c2978ba532069", "4bdf9e51ed7f0f19ee085389a0f9a80e", "a78bf3ad26d7658a90372ccb27bb2d37", "1ae43619d655ce6c5ac4028b8e599856",
       "d3939b7a7b6bc395162a2fa7f6f42b90", "8214a8348537e4182f301b0335d154fc", "f94b3da7a1d912fcadb9bbf4fa07988e", "47d3703d18c0336d5870da407c7bc775"]
pwd = ["b1a65ad943d8fe9af823a5873bc2e9c2", "6661c4aff9f6b49181c7978399ac3c85", "1b3010cb679ad4675f43ad3fdb392db1", "89e14eb8b2eb5cb42e1bbb625c71afff",
       "56510a0fcc0bf5cf2054f522304ca4a1", "14a81c69bd8b994a534cef122f10cb33", "d6214de72b2319ecb75e031a35832823", "447810ad2fc57d8db9909d307ebab734"]


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
                idx = random.randrange(0, len(key))
                shopify.UpdateProductToShopify(
                    productID, key[idx], pwd[idx], con)
                debug("Shopify", 0,
                      "Updated Pending Product : {}".format(productID))
            except Exception as e:
                print(e)
                debug("Shopify", 2,
                      "Failed Updating Pending Product : {}".format(productID))
                continue

        csr.close()
        con.close()
