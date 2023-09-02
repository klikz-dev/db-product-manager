from django.core.management.base import BaseCommand
from feed.models import Tempaper

import os
import environ
import pymysql
import xlrd
import time
import csv
import codecs

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Tempaper"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadFileFromSFTP(
                src="/tempaper/datasheets/Decorators Best_083123.xlsx", dst=f"{FILEDIR}/tempaper-master.xlsx", fileSrc=True, delete=False)
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
            products = Tempaper.objects.all()
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

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/tempaper/inventory/Tempaper_INV.csv", dst=f"{FILEDIR}/tempaper-inventory.csv", fileSrc=True, delete=False)
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
            con=self.con, brand=BRAND, Feed=Tempaper)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/tempaper-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 3))
                sku = f"TP {mpn}"

                pattern = common.formatText(sh.cell_value(i, 4))
                color = common.formatText(sh.cell_value(i, 5))

                name = common.formatText(sh.cell_value(i, 7))

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 0))
                manufacturer = brand
                collection = common.formatText(sh.cell_value(i, 2))

                # Main Information
                description = common.formatText(sh.cell_value(i, 8))

                width = common.formatFloat(sh.cell_value(i, 16))
                length = common.formatFloat(sh.cell_value(i, 17)) * 12
                dimension = common.formatText(sh.cell_value(i, 20))

                # Additional Information
                weight = common.formatFloat(sh.cell_value(i, 21))
                match = common.formatText(sh.cell_value(i, 24))
                material = common.formatText(sh.cell_value(i, 26))
                country = common.formatText(sh.cell_value(i, 32))
                features = []
                for id in range(27, 29):
                    feature = common.formatText(sh.cell_value(i, id))
                    if feature:
                        features.append(feature)

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 9))
                map = common.formatFloat(sh.cell_value(i, 10))

                # Measurement
                uom = f"Per {common.formatText(sh.cell_value(i, 12))}"

                # Tagging
                colors = color
                tags = f"{material}, {match}, {sh.cell_value(i, 27)}, {sh.cell_value(i, 28)}, {collection}, {pattern}, {description}"

                # Image
                thumbnail = sh.cell_value(i, 33).replace("dl=0", "dl=1")

                roomsets = []
                for id in range(34, 38):
                    roomset = sh.cell_value(i, id).replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True

                if type == "Wallpaper":
                    statusS = True
                else:
                    statusS = False

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                'name': name,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'width': width,
                'length': length,
                'dimension': dimension,

                'material': material,
                'weight': weight,
                'country': country,
                'match': match,
                'features': features,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/tempaper-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        for row in cr:
            if row[0] == "Item #":
                continue

            mpn = common.formatText(row[0])
            sku = f"TP {mpn}"

            stockP = common.formatInt(row[2])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': "",
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
