from django.core.management.base import BaseCommand
from feed.models import ExquisiteRugs
from django.db.models import Q

import os
import environ
import pymysql
import openpyxl
import time
import csv
import codecs

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Exquisite Rugs"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadFileFromSFTP(
                src="/exquisiterugs/datasheets/exquisiterugs-master.xlsx", dst=f"{FILEDIR}/exquisiterugs-master.xlsx", fileSrc=True, delete=False)
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
            products = ExquisiteRugs.objects.filter(Q(collection="Antique Loom") | Q(
                collection="Legacy") | Q(collection="Vintage Looms"))
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

        if "white-glove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove", logic=True)

        if "quick-ship" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="quickShip", tag="Quick Ship")

        if "image" in options['functions']:
            processor = Processor()
            processor.image()
            processor.hires()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/exquisiterugs/decoratorsbestam.csv", dst=f"{FILEDIR}/exquisiterugs-inventory.csv", fileSrc=True, delete=False)
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
            con=self.con, brand=BRAND, Feed=ExquisiteRugs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/exquisiterugs-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[2]).replace("'", "")
                sku = f"ER {mpn}"

                pattern = common.toInt(row[3])
                color = common.toText(row[4])

                name = common.toText(row[6])

                # Categorization
                brand = BRAND
                type = "Rug"
                manufacturer = BRAND
                collection = common.toText(row[1])

                # Main Information
                description = common.toText(row[19])

                width = common.toFloat(row[15])
                length = common.toFloat(row[16])
                height = common.toFloat(row[17])

                size = f"{common.toFloat(width / 12)}' x {common.toFloat(length / 12)}'"

                # Additional Information
                material = common.toText(row[12])
                care = common.toText(row[25])
                disclaimer = common.toText(row[24])
                country = common.toText(row[35])
                upc = common.toInt(row[13])
                weight = common.toFloat(row[14])

                specs = [
                    ("Dimension", common.toText(row[18])),
                ]

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[7])
                map = common.toFloat(row[8])

                # Tagging
                keywords = f"{row[11]}, {material}"
                colors = color

                # Image
                thumbnail = common.toText(row[51])

                roomsets = []
                for id in range(52, 58):
                    if row[id]:
                        roomsets.append(row[id])

                # Status
                statusP = True
                statusS = False

                # Shipping
                shippingWidth = common.toFloat(row[44])
                shippingLength = common.toFloat(row[43])
                shippingHeight = common.toFloat(row[45])
                shippingWeight = common.toFloat(row[42])

                if shippingWidth > 95 or shippingLength > 95 or shippingHeight > 95 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Fine-tuning
                name = f"{name.replace('Area Rug', '')}{size} Area Rug".replace(
                    color, f"{pattern} {color}")

                # Exceptions
                if cost == 0 or not pattern or not color or not type:
                    continue

            except Exception as e:
                debug.warn(BRAND, str(e))
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
                'disclaimer': disclaimer,

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
            }
            products.append(product)

        return products

    def image(self):
        csr = self.con.cursor()
        hasImage = []
        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = '{}'".format(BRAND))
        for row in csr.fetchall():
            hasImage.append(str(row[0]))
        csr.close()

        products = ExquisiteRugs.objects.all()
        for product in products:
            if product.productId in hasImage:
                continue

            self.databaseManager.downloadFileFromSFTP(
                src=f"/exquisiterugs/images/{product.thumbnail}",
                dst=f"{FILEDIR}/../../../images/product/{product.productId}.jpg",
                fileSrc=True,
                delete=False
            )

            for index, roomset in enumerate(product.roomsets):
                self.databaseManager.downloadFileFromSFTP(
                    src=f"/exquisiterugs/images/{roomset}",
                    dst=f"{FILEDIR}/../../../images/roomset/{product.productId}_{index + 2}.jpg",
                    fileSrc=True,
                    delete=False
                )

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/exquisiterugs-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = common.formatText(row[1]).replace("'", "")

            try:
                product = ExquisiteRugs.objects.get(mpn=mpn)
            except ExquisiteRugs.DoesNotExist:
                continue

            sku = product.sku
            stockP = common.formatInt(row[2])
            stockNote = common.formatText(row[3])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)

    def hires(self):
        csr = self.con.cursor()
        hasImage = []
        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 20 AND M.Brand = '{}'".format(BRAND))
        for row in csr.fetchall():
            hasImage.append(str(row[0]))
        csr.close()

        products = ExquisiteRugs.objects.all()
        for product in products:
            if product.productId in hasImage:
                continue

            self.databaseManager.downloadFileFromSFTP(
                src=f"/exquisiterugs/images/{product.thumbnail}",
                dst=f"{FILEDIR}/../../../images/hires/{product.productId}_20.jpg",
                fileSrc=True,
                delete=False
            )
