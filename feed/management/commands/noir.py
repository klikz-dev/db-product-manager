from django.core.management.base import BaseCommand
from feed.models import NOIR

import os
import environ
import pymysql
import xlrd
import time
import csv
import codecs

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "NOIR"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadFileFromSFTP(
                src="/noir/NOIR_MASTER.xlsx", dst=f"{FILEDIR}/noir-master.xlsx", fileSrc=True, delete=False)
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = NOIR.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

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
            processor.databaseManager.downloadImages(missingOnly=True)

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/noir/inventory/NOIR_INV.csv", dst=f"{FILEDIR}/noir-inventory.csv", fileSrc=True, delete=False)
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
            con=self.con, brand=BRAND, Feed=NOIR)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/noir-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 2))
                sku = f"NOIR {mpn}"

                name = common.formatText(sh.cell_value(i, 6))
                colors = common.formatText(sh.cell_value(i, 20))

                if "," in name:
                    pattern = name.split(",")[0].strip()
                    color = name.split(",")[1].strip()
                else:
                    pattern = name
                    color = colors

                if not color:
                    color = "N/A"

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 5)).title()
                manufacturer = brand
                collection = f"{brand} {type}"

                # Main Information
                description = common.formatText(sh.cell_value(i, 19))

                width = common.formatFloat(sh.cell_value(i, 16))
                height = common.formatFloat(sh.cell_value(i, 15))
                depth = common.formatFloat(sh.cell_value(i, 17))
                dimension = common.formatText(sh.cell_value(i, 18))

                # Additional Information
                upc = common.formatInt(sh.cell_value(i, 13))
                weight = common.formatFloat(sh.cell_value(i, 14))
                material = common.formatText(sh.cell_value(i, 12))
                country = common.formatText(sh.cell_value(i, 35))

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 7))
                map = common.formatFloat(sh.cell_value(i, 8))

                # Measurement
                uom = "Per Item"

                # Tagging
                tags = f"{colors}, {material}, {description}, {name}"

                # Image
                thumbnail = sh.cell_value(i, 51).replace("dl=0", "dl=1")

                roomsets = []
                for id in range(52, 65):
                    roomset = sh.cell_value(i, id).replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True
                statusS = False

                if width > 107 or height > 107 or depth > 107 or weight > 149:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Stock
                stockNote = f"{common.formatInt(sh.cell_value(i, 38))} days"

                # Type Mapping
                type_map = {
                    "Occasional Chairs": "Chairs",
                    "Ocassional Chairs": "Chairs",
                    "Sideboards": "Side Tables",
                    "Cocktail Table": "Cocktail Tables",
                    "Hutches": "Accessories",
                    "Bar & Counter": "Bar Stools",
                    "Bookcase": "Bookcases",
                    "Sideboard": "Side Tables",
                    "Console/Accent Tables": "Accent Tables",
                    "Sconces": "Wall Sconces",
                }
                if type in type_map:
                    type = type_map[type]

                # Rename
                name = name.replace(",", "")

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
                'height': height,
                'depth': depth,
                'dimension': dimension,

                'material': material,
                'weight': weight,
                'country': country,
                'upc': upc,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
                'whiteGlove': whiteGlove,

                'stockNote': stockNote,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/noir-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        for row in cr:
            if row[0] == "Item #":
                continue

            mpn = common.formatText(row[0])
            sku = f"NOIR {mpn}"

            stockP = common.formatInt(row[2])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': "",
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
