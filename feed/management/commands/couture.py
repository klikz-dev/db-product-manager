from django.core.management.base import BaseCommand
from feed.models import Couture

import os
import environ
import pymysql
import xlrd
from shutil import copyfile
import datetime
import time

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Couture"


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
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = Couture.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.image()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/couture", dst=f"{FILEDIR}/couture-inventory.xlsm", fileSrc=False)
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
            con=self.con, brand=BRAND, Feed=Couture)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/couture-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 0))
                sku = f"CL {mpn}"

                pattern = common.formatText(
                    sh.cell_value(i, 2)).split("-")[0].strip()
                pattern = pattern.replace("Lamp", "").replace(
                    "Table", "").replace("  ", "").strip()

                color = common.formatText(sh.cell_value(i, 7))

                # Categorization
                brand = BRAND
                collection = common.formatText(sh.cell_value(i, 3)).title()
                manufacturer = BRAND

                if collection == "":
                    continue
                if collection == "Accent Lamp":
                    type = "Accent Lamps"
                if collection == "Accent Table":
                    type = "Accent Tables"
                if collection == "Decorative Accessories":
                    type = "Decorative Accents"
                if collection == "Table Lamp":
                    type = "Table Lamps"
                else:
                    type = collection

                # Main Information
                description = common.formatText(sh.cell_value(i, 4))
                width = common.formatFloat(sh.cell_value(i, 13))
                height = common.formatFloat(sh.cell_value(i, 16))
                depth = common.formatFloat(sh.cell_value(i, 15))

                # Additional Information
                material = common.formatText(sh.cell_value(i, 6))
                care = common.formatText(sh.cell_value(i, 5))
                country = common.formatText(sh.cell_value(i, 1))
                weight = common.formatFloat(sh.cell_value(i, 12))
                upc = sh.cell_value(i, 38)

                features = [common.formatText(sh.cell_value(i, 8))]

                specs = []
                for j in [17, 19, 20, 24, 25, 26]:
                    if sh.cell_value(i, 21):
                        specs.append((common.formatText(sh.cell_value(
                            1, j)).title(), common.formatText(sh.cell_value(i, j))))

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 9))
                map = common.formatFloat(sh.cell_value(i, 10))
                uom = "Per Item"

                # Measurement

                # Tagging
                tags = description
                colors = color

                # Image

                # Status
                statusP = True
                statusS = False

                # Stock
                stockNote = common.formatText(sh.cell_value(i, 37))

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
                'width': width,
                'height': height,
                'depth': depth,

                'material': material,
                'care': care,
                'weight': weight,
                'upc': upc,
                'country': country,
                'features': features,
                'specs': specs,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'statusP': statusP,
                'statusS': statusS,

                'stockNote': stockNote,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        products = Couture.objects.all()

        for product in products:
            for fname in os.listdir(f"{FILEDIR}/images/couture/"):
                if ".jpg" in fname.lower() and product.mpn in fname:
                    copyfile(f"{FILEDIR}/images/couture/{fname}",
                             f"{FILEDIR}/../../../images/product/{product.productId}.jpg")

    def inventory(self):
        stocks = []

        wb = xlrd.open_workbook(f"{FILEDIR}/couture-inventory.xlsm")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            mpn = common.formatText(sh.cell_value(i, 0))
            sku = f"CL {mpn}"
            stockP = int(sh.cell_value(i, 1))

            stockNote = sh.cell_value(i, 2)
            if stockNote:
                date_tuple = xlrd.xldate_as_tuple(stockNote, wb.datemode)
                date_obj = datetime.datetime(*date_tuple)
                stockNote = date_obj.date()

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
