from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import JaipurLiving

import os
import environ
import pymysql
import xlrd
import csv
import codecs
import time

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


BRAND = "Jaipur Living"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            processor.databaseManager.downloadFileFromSFTP(
                src="/jaipur/Jaipur Living Master Data Template.xlsx", dst=f"{FILEDIR}/jaipur-living-master.xlsx")
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = JaipurLiving.objects.filter(
                Q(type="Throws") | Q(type="Rug Pad"))
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=False)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)

        if "sample" in options['functions']:
            processor.databaseManager.customTags(key="statusS", tag="NoSample")

        if "shipping" in options['functions']:
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "inventory" in options['functions']:
            while True:
                processor.databaseManager.downloadFileFromFTP(
                    src="Jaipur inventory feed.csv", dst=f"{FILEDIR}/jaipur-living-inventory.csv")
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
            con=self.con, brand=BRAND, Feed=JaipurLiving)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/jaipur-living-master.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 7))
                sku = f"JL {mpn}"

                pattern = common.formatText(sh.cell_value(i, 13))
                if common.formatText(sh.cell_value(i, 53)):
                    pattern = f"{pattern} {common.formatText(sh.cell_value(i, 53))}"

                color = common.formatText(sh.cell_value(i, 56))
                if common.formatText(sh.cell_value(i, 57)):
                    color = f"{color} / {common.formatText(sh.cell_value(i, 57))}"

                upc = common.formatInt(sh.cell_value(i, 6))

                title = common.formatText(sh.cell_value(i, 9)).title()
                title = title.replace(BRAND, "").strip()

                # Categorization
                manufacturer = BRAND

                type = common.formatText(sh.cell_value(i, 0)).title()
                if type == "Accent Furniture":
                    type = "Accents"
                if type == "Décor":
                    type = "Decor"
                if type == "Pillow":
                    type = "Throw Pillows"
                if "Throw" in title:
                    type = "Throws"

                collection = common.formatText(sh.cell_value(i, 12))

                # Main Information
                description = sh.cell_value(i, 25)
                width = common.formatFloat(sh.cell_value(i, 21))
                height = common.formatFloat(sh.cell_value(i, 22))
                depth = common.formatFloat(sh.cell_value(i, 24))

                # Additional Information
                features = []
                for id in range(26, 32):
                    feature = common.formatText(sh.cell_value(i, id))
                    if feature:
                        features.append(feature)

                front = common.formatText(sh.cell_value(i, 35))
                back = common.formatText(sh.cell_value(i, 36))
                filling = common.formatText(sh.cell_value(i, 37))

                material = f"Front: {front}"
                if back:
                    material += f", Back: {back}"
                if filling:
                    material += f", Filling: {filling}"

                care = common.formatText(sh.cell_value(i, 39))
                country = common.formatText(sh.cell_value(i, 32))

                weight = common.formatFloat(sh.cell_value(i, 88))
                if weight == 0:
                    weight = 5

                # Measurement
                uom = "Per Item"

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 15))
                map = common.formatFloat(sh.cell_value(i, 16))
                msrp = common.formatFloat(sh.cell_value(i, 17))

                # Tagging
                tags = ", ".join((sh.cell_value(i, 50), sh.cell_value(
                    i, 51), pattern, description, type))
                colors = color

                # Image
                thumbnail = sh.cell_value(i, 89)
                if thumbnail == "http://cdn1-media.s3.us-east-1.amazonaws.com/product_links/Product_Images/":
                    thumbnail = f"{thumbnail}{str(sh.cell_value(i, 8)).strip()}.jpg"

                roomsets = []
                for id in range(90, 104):
                    roomset = sh.cell_value(i, id)
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True
                statusS = False

                if width > 107 or height > 107 or depth > 107 or weight > 149:
                    whiteGlove = True
                else:
                    whiteGlove = False

                pass

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                'upc': upc,
                'title': title,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'width': width,
                'height': height,
                'depth': depth,

                'features': features,
                'material': material,
                'care': care,
                'country': country,
                'weight': weight,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
                'whiteGlove': whiteGlove,

            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/jaipur-living-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = common.formatText(row[1])
            sku = f"JL {mpn}"

            stockP = common.formatInt(row[5])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
