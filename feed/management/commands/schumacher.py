from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import Schumacher

import os
import environ
import pymysql
import csv
import codecs
import time
import requests

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Schumacher"


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
            products = Schumacher.objects.filter(pattern="Chiang Mai Dragon")
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

        if "pillow" in options['functions']:
            processor = Processor()
            processor.databaseManager.linkPillowSample()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.downloadFeed()
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
            con=self.con, brand=BRAND, Feed=Schumacher)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def downloadFeed(self):
        url = "https://schumapi.azurewebsites.net/api/products/get-product-assort-byid?type=1"

        headers = {
            'apiKey': '69ab187b-9cc8-4d07-8b09-23b1699d4d23'
        }

        response = requests.request("GET", url, headers=headers)

        if response.status_code == 200:
            with open(f"{FILEDIR}/schumacher-master.csv", 'w', encoding='utf-8') as csv_file:
                csv_file.write(response.text)
        else:
            print(f"Failed to fetch data: {response.status_code}")

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Sample Status
        discontinuedSamples = []
        f = open(f"{FILEDIR}/schumacher-sample-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = str(row[0]).strip().replace("'", "")
            stockS = common.formatInt(row[1])
            if stockS < 1:
                discontinuedSamples.append(mpn)

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
                if type == "Fabric":
                    type = "Fabric"
                if type == "Furniture & Accessories":
                    type = "Pillow"
                if type == "Rugs & Carpets":
                    type = "Rug"
                if "Throw" in pattern:
                    type = "Throws"

                if type == "Pillow" or type == "Rug" or type == "Throws":
                    name = pattern
                else:
                    name = ""

                pattern = pattern.replace(type, "").strip()

                # Categorization
                manufacturer = f"{BRAND} {type}"
                collection = str(row[2]).replace("Collection Name", "").strip()

                if "STAPETER" in collection:
                    manufacturer = f"BORÃSTAPETER {type}"
                    collection = "BORÃSTAPETER"

                # Main Information
                description = common.formatText(row[17])

                specs = [
                    ("Width", f"{common.formatText(row[11])}"),
                    ("Length", f"{common.formatText(row[21])}"),
                    ("Vertical Repeat", f"{common.formatText(row[15])}"),
                    ("Horizontal Repeat", f"{common.formatText(row[16])}"),
                ]

                # Additional Information
                match = str(row[14]).strip()

                yards = common.formatFloat(row[8])

                content = ""
                if row[12]:
                    content = f"{common.formatText(row[12])}"
                if row[13]:
                    content = f"{common.formatText(row[12])}, {common.formatText(row[13])}"

                # Measurement
                uom = str(row[9]).strip().upper()
                if "YARD" in uom or "REPEAT" in uom or "YD" in uom:
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
                if cost == 0:
                    continue

                # Tagging
                tags = ", ".join((collection, row[6], pattern, description))

                # Image
                thumbnail = str(row[18]).strip()
                roomsets = str(row[22]).split(",")

                # Status
                statusP = True

                if type == "Rug":
                    if cost == 15:
                        statusP = False
                        statusS = True
                    else:
                        statusP = True
                        statusS = False
                elif type == "Wallpaper" or type == "Fabric" or type == "Trim":
                    statusS = True
                else:
                    statusS = False

                if mpn in discontinuedSamples:
                    statusS = False

                # Stock
                stockP = int(float(row[19]))

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                'name': name,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'specs': specs,

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
