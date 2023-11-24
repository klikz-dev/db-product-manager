from django.core.management.base import BaseCommand
from feed.models import Kasmir

import os
import environ
import pymysql
import xlrd
import time

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Kasmir"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadFileFromFTP(
                src="Current-Inventory_Int.xls", dst=f"{FILEDIR}/kasmir-master.xls")
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(
                formatPrice=True, private=False)

        if "update" in options['functions']:
            processor = Processor()
            products = Kasmir.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True, private=False)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=True)

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromFTP(
                        src="Current-Inventory_Int.xls", dst=f"{FILEDIR}/kasmir-master.xls")
                    products = processor.fetchFeed()
                    processor.databaseManager.writeFeed(products=products)
                    processor.databaseManager.statusSync(fullSync=False)
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
            con=self.con, brand=BRAND, Feed=Kasmir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/kasmir-master.xls")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                pattern = common.formatText(sh.cell_value(i, 0))
                if "BOOKPATTERN" == pattern.upper() or "ALCANTARA" in pattern.upper():
                    continue
                color = common.formatText(sh.cell_value(i, 1))

                mpn = f"{pattern}/{color}"
                sku = f"KM {mpn}"

                # Categorization
                brand = BRAND
                type = "Fabric"
                manufacturer = f"{brand} {type}"
                collection = common.formatInt(sh.cell_value(i, 25))

                # Main Information
                width = common.formatFloat(sh.cell_value(i, 3))
                repeatV = common.formatFloat(sh.cell_value(i, 5))
                repeatH = common.formatFloat(sh.cell_value(i, 6))

                # Additional Information
                usage = common.formatText(sh.cell_value(i, 56))
                content = common.formatText(sh.cell_value(i, 26))
                specs = [
                    "Construction", common.formatText(sh.cell_value(i, 55))
                ]

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 2)) / 2

                # Measurement
                uom = "Per Yard"

                # Tagging
                colors = color
                tags = f"{sh.cell_value(i, 54)}, {sh.cell_value(i, 55)}"

                # Images
                thumbnail = f"https://www.kasmirfabricsonline.com/sampleimages/Large/{common.formatText(sh.cell_value(i, 57))}"
                if thumbnail == "ImageComingSoon.jpg":
                    thumbnail = ""

                # Status
                statusP = True
                statusS = True

                if "TEST" in pattern or cost < 8:
                    statusP = False

                # Stock
                stockP = common.formatInt(sh.cell_value(i, 58))

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

                'width': width,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'content': content,
                'usage': usage,
                'specs': specs,

                'cost': cost,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,

                'stockP': stockP
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        products = Kasmir.objects.all()
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': product.stockP,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
