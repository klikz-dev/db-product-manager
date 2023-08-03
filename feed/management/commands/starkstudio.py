from django.core.management.base import BaseCommand
from feed.models import StarkStudio

import os
import environ
import pymysql
import xlrd
import csv
import codecs
import time
from shutil import copyfile

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Stark Studio"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=False)

        if "update" in options['functions']:
            processor = Processor()
            products = StarkStudio.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.image()

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "shipping" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/stark/DecoratorsBestInventoryFeed.CSV", dst=f"{FILEDIR}/stark-studio-inventory.csv")

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
            con=self.con, brand=BRAND, Feed=StarkStudio)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Price Update Manual
        prices = {}
        wb = xlrd.open_workbook(f"{FILEDIR}/stark-studio-price.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(2, sh.nrows):
            # Primary Keys
            mpn = common.formatText(sh.cell_value(i, 3))

            # Pricing
            cost = common.formatFloat(sh.cell_value(i, 4))
            map = common.formatFloat(sh.cell_value(i, 5))

            prices[mpn] = {
                'cost': cost,
                'map': map
            }

        # Stock
        stocks = {}

        f = open(f"{FILEDIR}/stark-studio-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Item Number":
                continue

            try:
                mpn = common.formatText(row[0])
                stockP = common.formatInt(row[1])
                stockNote = common.formatText(row[4])

                if common.formatInt(row[5]) == 0:
                    statusP = True
                else:
                    statusP = False

                if common.formatInt(row[7]) == 0:
                    statusS = True
                else:
                    statusS = False

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            stocks[mpn] = {
                'stockP': stockP,
                'stockNote': stockNote,
                'statusP': statusP,
                'statusS': statusS,
            }

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/stark-studio-master.xlsx")
        for index in [0, 1, 2]:
            sh = wb.sheet_by_index(index)
            for i in range(2, sh.nrows):
                try:
                    # Primary Keys
                    mpn_origin = common.formatText(sh.cell_value(i, 3))
                    mpn = common.formatText(sh.cell_value(i, 4))

                    if not mpn_origin:
                        mpn_origin = mpn

                    sku = "SS {}".format(mpn)
                    try:
                        upc = int(sh.cell_value(i, 2))
                    except:
                        upc = ""

                    if "-" in sh.cell_value(i, 0):
                        pattern = common.formatText(
                            str(sh.cell_value(i, 0)).split("-")[0])
                        color = common.formatText(
                            str(sh.cell_value(i, 0)).split("-")[1])
                    else:
                        pattern = common.formatText(sh.cell_value(i, 0))
                        color = common.formatText(sh.cell_value(i, 1))

                    # Categorization
                    brand = BRAND
                    type = "Rug"
                    manufacturer = f"{brand} {type}"

                    if index == 0:
                        collection = "Essentials Machinemades"
                    if index == 1:
                        collection = "Essentials Handmades"
                    if index == 2:
                        collection = "Fabricated Rug Program"

                    # Main Information
                    description = common.formatText(sh.cell_value(i, 11))

                    width = common.formatFloat(sh.cell_value(i, 8))
                    length = common.formatFloat(sh.cell_value(i, 9))
                    if width > 0 and length > 0:
                        size = f"{common.formatInt(width / 12)}' x {common.formatInt(length / 12)}'"
                    else:
                        size = ""

                    # Additional Information
                    material = common.formatText(sh.cell_value(i, 19))
                    country = common.formatText(sh.cell_value(i, 20))

                    weight = common.formatFloat(sh.cell_value(i, 12))
                    if weight == 0:
                        weight = 5

                    # Pricing
                    cost = common.formatFloat(sh.cell_value(i, 5))
                    map = common.formatFloat(sh.cell_value(i, 6))

                    if cost == 0:
                        debug.debug(BRAND, 1, f"Price Error for MPN: {mpn}")
                        continue

                    # Measurement
                    uom = "Per Item"

                    # Tagging
                    tags = description
                    colors = common.formatText(sh.cell_value(i, 1))

                    # Status
                    statusP = False
                    statusS = False
                    stockP = 0
                    stockNote = ""

                    # Store ItemID in thumbnail field
                    thumbnail = mpn_origin

                    if "white glove" in str(sh.cell_value(i, 17)).lower() or "ltl" in str(sh.cell_value(i, 17)).lower():
                        whiteGlove = True
                    else:
                        whiteGlove = False

                    # Custom Stock and Price data
                    if mpn_origin in prices:
                        cost = prices[mpn_origin]['cost']
                        map = prices[mpn_origin]['map']

                    if mpn_origin in stocks:
                        statusS = stocks[mpn_origin]['statusS']
                        statusP = stocks[mpn_origin]['statusP']
                        stockP = stocks[mpn_origin]['stockP']
                        stockNote = stocks[mpn_origin]['stockNote']

                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    continue

                product = {
                    'mpn': mpn,
                    'sku': sku,
                    'upc': upc,
                    'pattern': pattern,
                    'color': color,

                    'brand': brand,
                    'type': type,
                    'manufacturer': manufacturer,
                    'collection': collection,

                    'description': description,
                    'width': width,
                    'length': length,
                    'size': size,

                    'material': material,
                    'country': country,
                    'weight': weight,

                    'uom': uom,

                    'tags': tags,
                    'colors': colors,

                    'cost': cost,
                    'map': map,

                    'statusP': statusP,
                    'statusS': statusS,

                    'stockP': stockP,
                    'stockNote': stockNote,
                    'whiteGlove': whiteGlove,

                    'thumbnail': thumbnail
                }
                products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        images = []
        imageDir = f"{FILEDIR}/images/stark"

        files = os.listdir(imageDir)
        for file in files:
            newFile = file.split(" ")[0]
            newFile = newFile.replace("A53_", "A53").replace(
                "B17_", "B17").replace("D18_", "D18").replace("WW1_", "WW1")

            imageIndex = 1
            if "_" in newFile:
                mpn = newFile.split("_")[0]
                imageType = newFile.split("_")[1]

                if imageType == "CL":
                    imageIndex = 2
                elif imageType == "ALT1":
                    imageIndex = 3
                elif imageType == "ALT2":
                    imageIndex = 4
                elif imageType == "RM":
                    imageIndex = 5
                elif imageType == "RUNNER":
                    imageIndex = 6
                else:
                    imageIndex = 7

            else:
                mpn = newFile

            image = (mpn, imageIndex, file)
            images.append(image)

        products = StarkStudio.objects.all()
        for product in products:
            for image in images:
                mpn, imageIndex, file = image

                print(mpn)

                if len(mpn) > 8 and mpn in product.thumbnail:
                    if imageIndex == 1:
                        debug.debug(
                            BRAND, 0, f"Copying {file} to {product.productId}.jpg")
                        copyfile(
                            f"{imageDir}/{file}", f"{FILEDIR}/../../../images/product/{product.productId}.jpg")
                    else:
                        debug.debug(
                            BRAND, 0, f"Copying {file} to {product.productId}_{imageIndex}.jpg")
                        copyfile(
                            f"{imageDir}/{file}", f"{FILEDIR}/../../../images/roomset/{product.productId}_{imageIndex}.jpg")

    def inventory(self):
        stocks = []

        products = StarkStudio.objects.all()

        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': product.stockP,
                'note': product.stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks, 1)
