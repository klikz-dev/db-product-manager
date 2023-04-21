from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import Schumacher

import os
import environ
import pymysql
import csv
import codecs
import time

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Schumacher"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            processor.databaseManager.downloadFileFromSFTP(
                src="../daily_feed/Assortment-DecoratorsBest.csv", dst=f"{FILEDIR}/schumacher-master.csv")
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = Schumacher.objects.filter(
                Q(type='Pillow') | Q(type='Throws'))
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
                    src="../daily_feed/Assortment-DecoratorsBest.csv", dst=f"{FILEDIR}/schumacher-master.csv")
                processor.inventory()

                print("Finished process. Waiting for next run. {}:{}".format(
                    BRAND, options['functions']))
                time.sleep(86400)

        if "pillow" in options['functions']:
            processor.databaseManager.linkPillowSample()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Schumacher)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        f = open(f"{FILEDIR}/schumacher-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Category":
                continue

            try:
                # Primary Keys
                mpn = str(row[3]).strip().replace("'", "")
                sku = f"SCH {mpn}"

                pattern = common.formatText(row[4]).title()
                color = common.formatText(row[5]).title()

                type = str(row[0]).strip().title()

                if pattern == "" or color == "" or type == "":
                    continue

                if type == "Wallcovering":
                    type = "Wallpaper"
                if type == "Furniture & Accessories":
                    type = "Pillow"
                if type == "Rugs & Carpets":
                    type = "Rug"
                if "Throw" in pattern:
                    type = "Throws"

                pattern = pattern.replace(type, "").strip()

                # Categorization
                manufacturer = f"{BRAND} {type}"
                collection = str(row[2]).replace("Collection Name", "").strip()

                if "STAPETER" in collection:
                    manufacturer = f"BORÃSTAPETER {type}"
                    collection = "BORÃSTAPETER"

                # Main Information
                description = common.formatText(row[17])

                width = common.formatFloat(row[11])
                length = common.formatFloat(row[21])

                size = ""
                if (type == "Pillow" or type == "Rug" or type == "Throw") and width != "" and length != "":
                    size = f'{width}" x {length}"'

                repeatV = common.formatFloat(row[15])
                repeatH = common.formatFloat(row[16])

                # Additional Information
                match = str(row[14]).strip()

                yards = common.formatFloat(row[8])

                content = ", ".join(
                    (str(row[12]).strip(), str(row[13].strip())))

                # Measurement
                uom = str(row[9]).strip().upper()
                if "YARD" in uom or "REPEAT" in uom:
                    uom = "Per Yard"
                elif "ROLL" in uom:
                    uom = "Per Roll"
                elif "EA" in uom or "UNIT" in uom or "SET" in uom or "ITEM" in uom:
                    uom = "Per Item"
                elif "PANEL" in uom:
                    uom = "Per Panel"
                else:
                    debug.debug(BRAND, 1, f"UOM Error. mpn: {mpn}. uom: {uom}")

                minimum = common.formatInt(row[10])

                if type == "Wallpaper" and minimum > 1:
                    increment = ",".join([str(ii * minimum)
                                         for ii in range(1, 26)])
                else:
                    increment = ""

                # Pricing
                cost = common.formatFloat(row[7])

                # Tagging
                tags = ", ".join((collection, row[6], description))

                # Image
                thumbnail = str(row[18]).strip()
                roomsets = str(row[22]).split(",")

                # Status
                statusP = True

                if type == "Rug":
                    statusS = False
                else:
                    statusS = True

                if width > 107 or length > 107:
                    whiteShip = True
                else:
                    whiteShip = False

                # Stock
                stockP = int(float(row[19]))

                pass

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
                'length': length,
                'repeatV': repeatV,
                'repeatH': repeatH,
                'size': size,

                'match': match,
                'content': content,
                'yards': yards,

                'cost': cost,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'tags': tags,
                'colors': color,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
                'whiteShip': whiteShip,

                'stockP': stockP,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/schumacher-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            if row[0] == "Category":
                continue

            mpn = str(row[3]).strip().replace("'", "")
            sku = f"SCH {mpn}"
            stockP = int(float(row[19]))

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
