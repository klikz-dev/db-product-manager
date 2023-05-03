from django.core.management.base import BaseCommand
from feed.models import Materialworks

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

BRAND = "Materialworks"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "validate" in options['functions']:
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = Materialworks.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)

        if "inventory" in options['functions']:
            if True:
                processor.databaseManager.downloadFileFromSFTP(
                    src="materialworks", dst=f"{FILEDIR}/materialworks-inventory.csv", fileSrc=False)
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
            con=self.con, brand=BRAND, Feed=Materialworks)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/materialworks-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 0))
                sku = f"DBM {mpn}"

                pattern = common.formatText(sh.cell_value(i, 4))
                color = common.formatText(sh.cell_value(i, 5))

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 3))
                manufacturer = f"{BRAND} {type}"
                collection = common.formatText(sh.cell_value(i, 2))

                # Main Information
                description = common.formatText(sh.cell_value(i, 10))
                usage = common.formatText(
                    sh.cell_value(i, 18)).replace("/ ", "/")

                width = common.formatFloat(sh.cell_value(i, 11))
                height = common.formatFloat(sh.cell_value(i, 12))
                size = common.formatText(sh.cell_value(i, 6))

                repeatV = common.formatFloat(sh.cell_value(i, 14))
                repeatH = common.formatFloat(sh.cell_value(i, 15))

                # Additional Information
                content = common.formatText(sh.cell_value(i, 13))
                features = [common.formatText(sh.cell_value(i, 16))]

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 7))
                map = common.formatFloat(sh.cell_value(i, 8))
                msrp = common.formatFloat(sh.cell_value(i, 9))

                # Measurement
                uom = common.formatText(sh.cell_value(i, 17)).strip()
                if uom == "Yard":
                    uom = "Per Yard"
                elif uom == "Roll":
                    uom = "Per Roll"
                elif uom == "Each":
                    uom = "Per Item"

                # Tagging
                tags = f"{usage}, {sh.cell_value(i, 21)}, {sh.cell_value(i, 23)}"
                colors = str(sh.cell_value(i, 22)).strip()

                # Image

                # Status
                statusP = True

                if type == "Pillow":
                    statusS = False
                else:
                    statusS = True

                # Stock

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

                'description': description,
                'usage': usage,
                'size': size,
                'width': width,
                'height': height,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'content': content,
                'features': features,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        fnames = os.listdir(f"{FILEDIR}/images/materialworks/")

        for fname in fnames:
            try:
                mpn = fname.split(".")[0]
                product = Materialworks.objects.get(mpn=mpn)

                if product.productId:
                    copyfile(f"{FILEDIR}/images/materialworks/{fname}",
                             f"{FILEDIR}/../../../images/product/{product.productId}.jpg")

                os.remove(f"{FILEDIR}/images/materialworks/{fname}")
            except:
                continue

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/materialworks-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "ValdeseMaterial":
                continue

            mpn = common.formatText(row[0])
            sku = f"DBM {mpn}"
            stockP = common.formatInt(row[5])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)