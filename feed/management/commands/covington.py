from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import Covington

import os
import environ
import pymysql
import xlrd
import csv
import codecs
import time
from shutil import copyfile

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Covington"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "validate" in options['functions']:
            processor = Processor()
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
            products = Covington.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True, private=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.image()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.inventory()

                    print("Finished process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(86400)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Covington)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/covington-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 0))
                if "MG-" not in mpn:
                    continue

                sku = f"DBC {mpn}"
                pattern = common.formatText(sh.cell_value(i, 4))
                color = common.formatText(sh.cell_value(i, 5))

                # Categorization
                brand = BRAND
                type = "Fabric"
                manufacturer = f"{brand} {type}"
                collection = common.formatText(sh.cell_value(i, 2))

                # Main Information
                description = common.formatText(sh.cell_value(i, 9))
                width = common.formatFloat(sh.cell_value(i, 10))
                repeatH = common.formatFloat(sh.cell_value(i, 14))
                repeatV = common.formatFloat(sh.cell_value(i, 15))

                # Additional Information
                usage = common.formatText(sh.cell_value(i, 21))
                content = common.formatText(sh.cell_value(i, 13))
                upc = common.formatInt(sh.cell_value(i, 12))

                features = []
                for id in range(16, 19):
                    feature = common.formatText(sh.cell_value(i, id))
                    if feature:
                        features.append(feature)

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 6))

                # Measurement
                uom = "Per Yard"
                minimum = common.formatInt(sh.cell_value(i, 22))

                # Tagging
                tags = f"{sh.cell_value(i, 24)}, {','.join(features)}"
                colors = common.formatText(sh.cell_value(i, 25))

                # Status
                statusP = True
                statusS = True

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'width': width,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'content': content,
                'usage': usage,
                'upc': upc,
                'features': features,

                'cost': cost,

                'uom': uom,
                'minimum': minimum,

                'tags': tags,
                'colors': colors,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        fnames = os.listdir(f"{FILEDIR}/images/covington/")
        for fname in fnames:
            mpn = fname.split(".")[0]

            try:
                product = Covington.objects.get(mpn=mpn)

                if product.productId:
                    copyfile(f"{FILEDIR}/images/covington/{fname}",
                             f"{FILEDIR}/../../../images/product/{product.productId}.jpg")
                    debug.debug(
                        BRAND, 0, f"Copied {fname} to {product.productId}.jpg")

                os.remove(
                    f"{FILEDIR}/images/covington/{fname}")
            except Covington.DoesNotExist:
                continue

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/covington-inventory.CSV", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            if row[0] == "STYCOL":
                continue

            mpn = common.formatText(row[0])
            sku = f"DBC {mpn}"

            stockP = common.formatInt(row[5])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
