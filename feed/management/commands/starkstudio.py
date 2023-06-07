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

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Stark Studio"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=False)

        if "update" in options['functions']:
            products = StarkStudio.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=False)

        if "image" in options['functions']:
            processor.image()

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "shipping" in options['functions']:
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "main" in options['functions']:
            while True:
                try:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/stark/DecoratorsBestInventoryFeed.CSV", dst=f"{FILEDIR}/stark-studio-inventory.csv")

                    products = processor.fetchFeed()
                    processor.databaseManager.writeFeed(products=products)

                    processor.databaseManager.statusSync(fullSync=False)

                    processor.inventory()

                    print("Finished process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(86400)

                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    print("Failed process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(3600)


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=StarkStudio)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Price Update Manual
        prices = {}
        wb = xlrd.open_workbook(FILEDIR + 'stark-studio-price.xlsx')
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

        wb = xlrd.open_workbook(FILEDIR + 'stark-studio-master.xlsx')
        for index in [0, 1, 2]:
            sh = wb.sheet_by_index(index)
            for i in range(2, sh.nrows):
                try:
                    # Primary Keys
                    mpn_origin = common.formatText(sh.cell_value(i, 3))
                    mpn = common.formatText(sh.cell_value(i, 4))
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
                    'whiteGlove': whiteGlove
                }
                products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        imageDir = f"{FILEDIR}/images/stark"

        products = StarkStudio.objects.all()
        for product in products:
            productStr = f"{product.pattern.strip()} {product.color.strip()}".replace(
                ",", "").replace("/", " ").lower()

            for fname in os.listdir(imageDir):
                if productStr in fname.lower():
                    if "_CL" in fname:
                        print("Roomset 2: {}".format(fname))
                        copyfile(
                            f"{imageDir}/{fname}", f"{FILEDIR}/../../../images/roomset/{product.productId}_2.jpg")

                    elif "_ALT1" in fname:
                        print("Roomset 3: {}".format(fname))
                        copyfile(
                            f"{imageDir}/{fname}", f"{FILEDIR}/../../../images/roomset/{product.productId}_3.jpg")

                    elif "_ALT2" in fname:
                        print("Roomset 4: {}".format(fname))
                        copyfile(
                            f"{imageDir}/{fname}", f"{FILEDIR}/../../../images/roomset/{product.productId}_4.jpg")

                    elif "_RM" in fname:
                        print("Roomset 5: {}".format(fname))
                        copyfile(
                            f"{imageDir}/{fname}", f"{FILEDIR}/../../../images/roomset/{product.productId}_5.jpg")

                    else:
                        print("Product: {}".format(fname))
                        copyfile(
                            f"{imageDir}/{fname}", f"{FILEDIR}/../../../images/product/{product.productId}.jpg")

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
