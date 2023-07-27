from django.core.management.base import BaseCommand

import environ
import pymysql
import time

from library import debug, shopify

PROCESS = "Tag"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.tag()

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

    def tag(self):
        csr = self.con.cursor()

        csr.execute(
            "SELECT ProductID FROM PendingUpdateTagBodyHTML ORDER BY ProductID")
        rows = csr.fetchall()

        for row in rows:
            productID = row[0]

            try:
                shopify.UpdateTagBodyToShopify(productID, self.con)
                debug.debug(
                    PROCESS, 0, f"Updated Pending Product Tag : {productID}")
            except:
                debug.debug(
                    PROCESS, 1, f"Failed Updating Pending Product Tag : {productID}")
                continue

        csr.close()
