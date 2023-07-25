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

        if "feed" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadFileFromSFTP(
                src="/jaipur/Jaipur Living Master Data Template.xlsx", dst=f"{FILEDIR}/jaipur-living-master.xlsx")
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = JaipurLiving.objects.filter(
                Q(type="Throws") | Q(type="Rug Pad"))
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=True)

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires()

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
                    processor.databaseManager.downloadFileFromFTP(
                        src="Jaipur inventory feed.csv", dst=f"{FILEDIR}/jaipur-living-inventory.csv")
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
            con=self.con, brand=BRAND, Feed=JaipurLiving)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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

                name = common.formatText(sh.cell_value(i, 9)).title()
                name = name.replace(BRAND, "").strip()

                # Categorization
                manufacturer = BRAND

                type = common.formatText(sh.cell_value(i, 0)).title()
                if type == "Accent Furniture":
                    type = "Accents"
                if type == "Décor":
                    type = "Decor"
                if type == "Pillow":
                    type = "Throw Pillows"
                if "Throw" in name:
                    type = "Throws"

                collection = common.formatText(sh.cell_value(i, 12))

                # Main Information
                description = sh.cell_value(i, 25)
                width = common.formatFloat(sh.cell_value(i, 21))
                length = common.formatFloat(sh.cell_value(i, 22))
                height = common.formatFloat(sh.cell_value(i, 24))

                size = common.formatText(sh.cell_value(i, 18))
                size = size.replace("X", " x ").replace(
                    "Folded", "").replace("BOX", "").replace("  ", " ").strip()

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
                featuresText = ", ".join(features)
                tags = ", ".join((sh.cell_value(i, 19), sh.cell_value(i, 50), sh.cell_value(
                    i, 51), pattern, name, description, type, featuresText))
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

                if width > 107 or length > 107 or height > 107 or weight > 149:
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
                'name': name,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'width': width,
                'length': length,
                'height': height,
                'size': size,

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

    def hires(self):
        products = JaipurLiving.objects.all()
        for product in products:
            if not product.productId:
                continue

            common.hiresdownload(str(product.thumbnail).strip().replace(
                " ", "%20"), "{}_20.jpg".format(product.productId))
