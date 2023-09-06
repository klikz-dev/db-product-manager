from django.core.management.base import BaseCommand
from feed.models import Pindler

import os
import environ
import pymysql
import xlrd
import time
import csv
import codecs
import requests

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Pindler"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            processor.downloadFeed()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(
                formatPrice=True, private=True)

        if "update" in options['functions']:
            processor = Processor()
            products = Pindler.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True, private=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=False)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Pindler)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def downloadFeed(self):
        try:
            r = requests.get(
                "https://trade.pindler.com/dataexport/DecoratorBest/DECORBEST.csv", auth=("decorbest", "pnp$7175"))

            with open(f"{FILEDIR}/pindler-master.csv", "wb") as out:
                for bits in r.iter_content():
                    out.write(bits)

            debug.debug(
                BRAND, 0, "Pindler FTP Master CSV File Download Completed")
        except Exception as e:
            debug.debug(BRAND, 1, str(e))

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        f = open(f"{FILEDIR}/pindler-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        for row in cr:
            try:
                if row[0] == "Inventory Number" or row[0] == "Text":
                    continue

                # Primary Keys
                mpn = row[0]
                sku = f"PDL {row[20]}-{row[18]}".replace("'", "")

                pattern = common.formatText(row[19])
                color = common.formatText(row[18])

                # Categorization
                brand = BRAND
                collection = row[1] or row[3]

                if "T" in row[20]:
                    type = "Trim"
                else:
                    type = "Fabric"

                manufacturer = f"{BRAND} {type}"

                # Main Information
                width = common.formatText(row[26])
                repeatV = common.formatFloat(row[24])
                repeatH = common.formatFloat(row[9])

                # Additional Information
                content = common.formatText(row[4])

                # Pricing
                cost = common.formatFloat(row[25])

                # Measurement
                uom = "Per Yard"

                # Tagging
                colors = row[12]
                tags = " ".join(
                    [row[12], row[13], row[14], row[15], row[16], row[17]])

                # Image
                thumbnail = common.formatText(row[10])

                # Status
                statusP = True
                statusS = False

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'width': width,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'content': content,

                'cost': cost,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products
