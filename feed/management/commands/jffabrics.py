from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import JFFabrics

import os
import environ
import pymysql
import xlrd
import time

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


BRAND = "JF Fabrics"


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
            products = JFFabrics.objects.filter(Q(productId='6880928137262'))
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)

        if "inventory" in options['functions']:
            while True:
                processor.databaseManager.downloadFileFromSFTP(
                    src="Decorating Best Inventory.xlsx", dst=f"{FILEDIR}/jffabrics-inventory.xlsx")
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
            con=self.con, brand=BRAND, Feed=JFFabrics)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Disco Books
        discoBooks = []
        wb = xlrd.open_workbook(f"{FILEDIR}/jffabrics-disco-books.xls")
        sh = wb.sheet_by_index(0)
        for i in range(3, sh.nrows):
            book = common.formatText(sh.cell_value(i, 0))
            discoBooks.append(book)

        # Disco Skus
        discoMPNs = []
        wb = xlrd.open_workbook(f"{FILEDIR}/jffabrics-disco-skus.xls")
        sh = wb.sheet_by_index(0)
        for i in range(9, sh.nrows):
            book = common.formatText(sh.cell_value(i, 3))
            pattern = common.formatText(sh.cell_value(i, 0))
            color = common.formatInt(sh.cell_value(i, 1))

            mpn = f"{pattern}_{color}{book}"
            discoMPNs.append(mpn)

        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/jffabrics-master.xls")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                book = common.formatText(sh.cell_value(i, 1))
                pattern = common.formatText(sh.cell_value(i, 2))
                color = common.formatInt(sh.cell_value(i, 3))

                mpn = f"{pattern}_{color}{book}"
                sku = f"JF {common.formatInt(sh.cell_value(i, 4))}"

                if book in discoBooks or mpn in discoMPNs:
                    continue

                # Categorization
                type = common.formatText(sh.cell_value(i, 8))
                if type == "Wallcovering":
                    type = "Wallpaper"

                manufacturer = f"{BRAND} {type}"

                collection = book

                # Main Information
                description = common.formatText(sh.cell_value(i, 59))
                usage = common.formatText(sh.cell_value(i, 13))
                width = common.formatFloat(sh.cell_value(i, 24))
                repeatH = common.formatFloat(sh.cell_value(i, 30))
                repeatV = common.formatFloat(sh.cell_value(i, 31))

                # Additional Information
                content = common.formatText(sh.cell_value(i, 10))
                yards = common.formatFloat(sh.cell_value(i, 25))
                country = common.formatText(sh.cell_value(i, 23))
                weight = common.formatFloat(sh.cell_value(i, 34))

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 76))
                map = common.formatFloat(sh.cell_value(i, 74))

                # Measurement
                if common.formatText(sh.cell_value(i, 73)) == "DR":
                    uom = "Per Roll"
                else:
                    uom = "Per Yard"

                # Tagging
                tags = f"{sh.cell_value(i, 14)} {sh.cell_value(i, 22)} {description}"
                colors = common.formatText(sh.cell_value(i, 6))

                # Image
                thumbnail = sh.cell_value(i, 78)

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
                'usage': usage,
                'width': width,
                'repeatH': repeatH,
                'repeatV': repeatV,

                'content': content,
                'yards': yards,
                'country': country,
                'weight': weight,

                'cost': cost,
                'map': map,
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

    def inventory(self):
        stocks = []

        wb = xlrd.open_workbook(f"{FILEDIR}/jffabrics-inventory.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(2, sh.nrows):
            sku = f"JF {common.formatInt(sh.cell_value(i, 0))}"
            stockP = common.formatInt(sh.cell_value(i, 3))

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
