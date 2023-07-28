from django.core.management.base import BaseCommand
from feed.models import Surya
from django.db.models import Q

import os
import environ
import pymysql
import xlrd
import csv
import codecs
import time

from library import database, debug, common

formatText = common.formatText
formatInt = common.formatInt
formatFloat = common.formatFloat

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Surya"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
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

        if "shipping" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/surya/inventory_dbest.csv", dst=f"{FILEDIR}/surya-inventory.csv")
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
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Invalid images
        unavailable = []
        wb = xlrd.open_workbook(f'{FILEDIR}/surya-unavailable.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            mpn = formatText(sh.cell_value(i, 0))
            unavailable.append(mpn)

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f'{FILEDIR}/surya-master.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = formatText(sh.cell_value(i, 1))
                debug.debug(BRAND, 0, "Fetching Product MPN: {}".format(mpn))

                sku = f"SR {mpn}"
                pattern = formatText(sh.cell_value(i, 4))
                color = formatText(sh.cell_value(i, 2))

                if sh.cell_value(i, 3):
                    name = formatText(sh.cell_value(i, 3))
                else:
                    name = ""

                # Categorization
                brand = BRAND

                typeText = formatText(sh.cell_value(i, 0)).title()
                if typeText == "Bedding":
                    type = "Furniture"
                elif typeText == "Accent And Lounge Chairs":
                    type = "Accents"
                elif typeText == "Ceiling Lighting":
                    type = "Lighting"
                elif typeText == "Rugs":
                    type = "Rug"
                elif typeText == "Wall Art - Stock":
                    type = "Wall Art"
                else:
                    type = typeText

                manufacturer = BRAND
                collection = formatText(sh.cell_value(i, 4))

                # Main Information
                description = formatText(sh.cell_value(i, 3))
                usage = typeText
                width = formatFloat(sh.cell_value(i, 16))
                height = formatFloat(sh.cell_value(i, 17))
                depth = formatFloat(sh.cell_value(i, 15))

                if height == 0 and depth != 0:
                    height = depth
                    depth = 0

                if "D" in sh.cell_value(i, 13):
                    size = ""
                    dimension = formatText(sh.cell_value(i, 13))
                else:
                    size = formatText(sh.cell_value(i, 13))
                    dimension = ""

                # Additional Information
                material = formatText(sh.cell_value(i, 10))
                weight = formatFloat(sh.cell_value(i, 18)) or 5
                specs = [
                    ("Color", formatText(sh.cell_value(i, 9))),
                    ("Construction", formatText(sh.cell_value(i, 21))),
                ]
                upc = formatInt(sh.cell_value(i, 5))

                # Measurement
                uom = "Per Item"

                # Pricing
                cost = formatFloat(sh.cell_value(i, 6))
                map = formatFloat(sh.cell_value(i, 7))
                msrp = formatFloat(sh.cell_value(i, 8))

                if cost == 0:
                    debug.debug(BRAND, 1, "Produt Cost error {}".format(mpn))
                    continue

                # Tagging
                tags = f"{formatText(sh.cell_value(i, 11))}, {formatText(sh.cell_value(i, 12))}"
                if formatText(sh.cell_value(i, 23)) == "Yes":
                    tags = "{}, Outdoor".format(tags)
                tags = f"{tags}, {type}, {collection}, {pattern}"

                colors = formatText(sh.cell_value(i, 9))

                # Status
                statusP = True
                statusS = False

                if mpn in unavailable:
                    debug.debug(
                        BRAND, 1, "Product Image is unavailable for MPN: {}".format(mpn))
                    statusP = False

                whiteGlove = False
                if "white glove" in str(sh.cell_value(i, 17)).lower() or "ltl" in str(sh.cell_value(i, 17)).lower():
                    whiteGlove = True

                # Image
                thumbnail = sh.cell_value(i, 25)

                roomsets = []
                for id in range(26, 31):
                    if sh.cell_value(i, id) != "":
                        roomsets.append(sh.cell_value(i, id))

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'upc': upc,
                'pattern': pattern,
                'color': color,
                'name': name,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'usage': usage,
                'width': width,
                'height': height,
                'depth': depth,
                'weight': weight,
                'size': size,
                'dimension': dimension,

                'material': material,
                'specs': specs,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'statusP': statusP,
                'statusS': statusS,
                'whiteGlove': whiteGlove,

                'thumbnail': thumbnail,
                'roomsets': roomsets,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
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

            hiresImage = product.thumbnail.replace("512x512", "RAW")

            common.hiresdownload(hiresImage, f"{product.productId}_20.jpg")

            debug.debug(
                BRAND, 0, f"Copied {hiresImage} to {product.productId}_20.png")
