from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import KravetDecor

import os
import environ
import pymysql
import csv
import codecs
import zipfile
import time

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Kravet Decor"


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
            products = KravetDecor.objects.all()
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
            while True:
                processor.downloadInventory()
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
            con=self.con, brand=BRAND, Feed=KravetDecor)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        f = open(f"{FILEDIR}/kravet-decor-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "sku":
                continue

            try:
                # Primary Keys
                mpn = common.formatText(row[0])
                sku = f"KD {mpn.replace('.0', '').replace('.', '-')}"

                pattern = common.formatText(row[1]).replace(",", "")
                color = sku.split("-")[2].title()

                upc = common.formatText(row[34])

                # Categorization
                type = common.formatText(row[6]).title()
                if type == "Benches & Ottomans":
                    type = "Ottomans"

                manufacturer = BRAND
                collection = common.formatText(row[3])

                # Pattern Name
                typeSingular = type
                if type[len(type) - 1] == "s":
                    typeSingular = type[:-1]

                for typeword in typeSingular.split(" "):
                    pattern = pattern.replace(typeword, "")

                pattern = pattern.replace("  ", " ").strip()
                ##############

                if pattern == "" or color == "" or type == "":
                    continue

                # Main Information
                description = row[2]
                usage = common.formatText(row[5])

                width = common.formatFloat(row[11])
                length = common.formatFloat(row[10])
                height = common.formatFloat(row[12])

                # Set minimum to height
                def swap(a, b):
                    return b, a

                if width < height:
                    width, height = swap(width, height)

                if length < height:
                    length, height = swap(length, height)
                #######################

                # Additional Information
                material = common.formatText(row[20])
                care = common.formatText(row[24])
                country = common.formatText(row[21])

                features = []
                if row[25]:
                    features.append(row[25])

                weight = common.formatFloat(row[14])

                # Pricing
                cost = common.formatFloat(row[15])
                if cost == 0:
                    debug.debug(BRAND, 1, f"Cost error for MPN: {mpn}")

                # Measurement
                uom = "Per Item"

                # Tagging
                tags = f"{row[6]}, {usage}, {pattern}, {collection}, {description}"
                colors = row[7]

                # Image
                thumbnail = row[35]

                roomsets = []
                for id in range(36, 40):
                    if row[id]:
                        roomsets.append(row[id])

                # Status
                if row[4] == "Active":
                    statusP = True
                else:
                    statusP = False

                statusS = False

                if "White Glove" in row[17]:
                    whiteShip = True
                else:
                    whiteShip = False

                # Stock
                stockNote = common.formatText(row[18])

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                'upc': upc,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'usage': usage,
                'width': width,
                'length': length,
                'height': height,

                'material': material,
                'care': care,
                'country': country,
                'features': features,
                'weight': weight,

                'cost': cost,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
                'whiteShip': whiteShip,

                'stockNote': stockNote,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def downloadInventory(self):
        try:
            self.databaseManager.downloadFileFromFTP(
                src="curated_onhand_info.zip", dst=f"{FILEDIR}/kravet-decor-inventory.zip")
            z = zipfile.ZipFile(f"{FILEDIR}/kravet-decor-inventory.zip", "r")
            z.extractall(FILEDIR)
            z.close()
            os.rename(f"{FILEDIR}/curated_onhand_info.csv",
                      f"{FILEDIR}/kravet-decor-inventory.csv")

            debug.debug(BRAND, 0, "Download Completed")
            return True
        except Exception as e:
            debug.debug(BRAND, 1, f"Download Failed. {str(e)}")
            return False

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/kravet-decor-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            if row[0] == "Item":
                continue

            mpn = common.formatText(row[0])
            sku = f"KD {mpn.replace('.0', '').replace('.', '-')}"

            stockP = common.formatInt(row[1])
            stockNote = f"{common.formatInt(row[2])} days"

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote,
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
