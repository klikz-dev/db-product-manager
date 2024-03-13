from django.core.management.base import BaseCommand
from feed.models import Surya
from django.db.models import Q

import os
import environ
import pymysql
import openpyxl
import csv
import codecs
import time

from library import database, debug, common

formatText = common.formatText
formatInt = common.formatInt
formatFloat = common.formatFloat

FILEDIR = "{}/files".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Surya"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadFileFromSFTP(
                src="/surya/surya_masterlist_dbest.xlsx", dst=f"{FILEDIR}/surya-master.xlsx", fileSrc=True, delete=False)
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products)

        if "validate" in options['functions']:
            processor = Processor()
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=False)

        if "update" in options['functions']:
            processor = Processor()
            products = Surya.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=False)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=True)

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires(missingOnly=True)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "white-glove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "best-seller" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="bestSeller", tag="Best Selling")

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/surya/inventory_dbest.csv", dst=f"{FILEDIR}/surya-inventory.csv", fileSrc=True, delete=True)
                    processor.inventory()

                print("Finished process. Waiting for next run. {}:{}".format(
                    BRAND, options['functions']))
                time.sleep(86400)


class Processor:
    def __init__(self):
        self.env = environ.Env()

        self.con = pymysql.connect(host=self.env('MYSQL_HOST'), user=self.env('MYSQL_USER'), passwd=self.env(
            'MYSQL_PASSWORD'), db=self.env('MYSQL_DATABASE'), connect_timeout=5)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Surya)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/surya-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[2])
                sku = f"SR {mpn}"

                pattern = common.toText(row[3])
                color = ' '.join(common.toText(row[12]).split(', ')[:2])

                name = common.toText(row[4])

                # Categorization
                brand = BRAND
                type = common.toText(row[0])
                manufacturer = BRAND
                collection = common.toText(row[5])

                # Main Information
                description = common.toText(row[6])

                width = common.toFloat(row[19])
                length = common.toFloat(row[20])
                height = common.toFloat(row[18])

                if length == 0 and height != 0:
                    length = height
                    height = 0

                size = common.toText(row[16])

                # Additional Information
                material = common.toText(row[13])
                care = common.toText(row[71])
                country = common.toText(row[28])
                upc = common.toInt(row[8])
                weight = common.toFloat(row[21]) or 5

                specs = [
                    ("Colors", common.toText(row[12])),
                ]

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[9])
                map = common.toFloat(row[10])

                # Tagging
                keywords = f"{common.toText(row[14])}, {common.toText(row[41])}, {type}, {collection}, {pattern}"
                if common.toText(row[31]) == "Yes":
                    keywords = f"{keywords}, Outdoor"

                colors = common.toText(row[12])

                # Image
                thumbnail = row[92]

                roomsets = []
                for id in range(93, 99):
                    if row[id] != "":
                        roomsets.append(row[id])

                # Status
                if "Swatch" in type:
                    statusP = False
                else:
                    statusP = True
                statusS = False

                if common.toText(row[30]) == "Yes":
                    bestSeller = True
                else:
                    bestSeller = False

                # Shipping
                shippingHeight = common.toFloat(row[24])
                shippingWidth = common.toFloat(row[25])
                shippingDepth = common.toFloat(row[23])
                shippingWeight = common.toFloat(row[22])
                if shippingWidth > 95 or shippingHeight > 95 or shippingDepth > 95 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Fine-tuning
                type_mapping = {
                    "Rugs": "Rug",
                    "Wall Hangings": "Wall Hanging",
                    "Mirrors": "Mirror",
                    "Bedding": "Bed",
                    "Wall Art - Stock": "Wall Art",
                    "Throws": "Throw",
                    "Ceiling Lighting": "Lighting",
                    "Accent and Lounge Chairs": "Accent Chair",
                    "Decorative Accents": "Decorative Accent",
                    "Sofas": "Sofa",
                    "Wall Sconces": "Wall Sconce",
                    "Rug Blanket": "Rug",
                    "Bedding Inserts": "Bed",
                    "Made to Order Rugs": "Rug",
                    "Printed Rug Set (3pc)": "Rug",
                }
                if type in type_mapping:
                    type = type_mapping[type]

                name = f"{collection} {pattern} {color} {size} {type}"

                # Exceptions
                if cost == 0 or not pattern or not color or not type:
                    continue

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
                'height': height,
                'size': size,

                'material': material,
                'care': care,
                'country': country,
                'weight': weight,
                'upc': upc,

                'specs': specs,

                'uom': uom,

                'cost': cost,
                'map': map,

                'keywords': keywords,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
                'whiteGlove': whiteGlove,
                'bestSeller': bestSeller
            }
            products.append(product)

        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/surya-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Sku":
                continue

            sku = f"SR {formatText(row[0])}"
            stockP = formatInt(row[1])
            stockNote = formatText(row[2])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote,
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)

    def hires(self, missingOnly=False):
        hasImage = []

        self.csr = self.con.cursor()
        self.csr.execute(
            f"SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 20 AND M.Brand = '{BRAND}'")
        for row in self.csr.fetchall():
            hasImage.append(str(row[0]))
        self.csr.close()

        products = Surya.objects.all()
        for product in products:
            if "512x512" not in product.thumbnail:
                continue

            if not product.productId:
                continue

            if missingOnly and product.productId in hasImage:
                continue

            hiresImage = product.thumbnail.replace(
                "512x512", "RAW").replace(" ", "%20")

            common.hiresdownload(hiresImage, f"{product.productId}_20.jpg")

            debug.debug(
                BRAND, 0, f"Copied {hiresImage} to {product.productId}_20.png")
