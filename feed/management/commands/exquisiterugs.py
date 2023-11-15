from django.core.management.base import BaseCommand
from feed.models import ExquisiteRugs
from django.db.models import Q

import os
import environ
import pymysql
import xlrd
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
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Quick Ship
        quickships = []
        f = open(f"{FILEDIR}/exquisiterugs-quickships.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = common.formatText(row[2]).replace("'", "")
            if row[5] == "YES":
                quickships.append(mpn)

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/exquisiterugs-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 2)).replace("'", "")
                sku = f"ER {mpn}"

                pattern = common.formatInt(sh.cell_value(i, 3))
                color = common.formatText(sh.cell_value(i, 4))

                name = common.formatText(sh.cell_value(i, 6))

                # Categorization
                brand = BRAND
                type = "Rug"
                manufacturer = brand
                collection = common.formatText(sh.cell_value(i, 1))

                # Main Information
                description = common.formatText(sh.cell_value(i, 19))
                disclaimer = common.formatText(sh.cell_value(i, 24))

                width = common.formatFloat(sh.cell_value(i, 15))
                length = common.formatFloat(sh.cell_value(i, 16))
                height = common.formatFloat(sh.cell_value(i, 17))

                size = f"{round(width / 12, 2)}'X{round(length / 12, 2)}'"
                dimension = common.formatText(sh.cell_value(i, 18))

                weight = common.formatFloat(sh.cell_value(i, 14))
                specs = [
                    ("Weight", f"{weight} lbs"),
                ]

                # Additional Information
                upc = common.formatInt(sh.cell_value(i, 13))
                weight = common.formatFloat(sh.cell_value(i, 14))
                care = common.formatText(sh.cell_value(i, 25))
                material = common.formatText(sh.cell_value(i, 12))
                country = common.formatText(sh.cell_value(i, 35))

                # Pricing
                cost = round(common.formatFloat(
                    sh.cell_value(i, 7)) * 0.8, 2)  # Tmp: Promo
                map = round(common.formatFloat(sh.cell_value(i, 8))
                            * 0.8, 2)  # Tmp: Promo

                # Measurement
                uom = "Per Item"

                # Tagging
                tags = f"{sh.cell_value(i, 11)}, {material}"
                colors = color

                # Image
                thumbnail = common.formatText(sh.cell_value(i, 51))

                roomsets = []
                for id in range(52, 58):
                    roomset = sh.cell_value(i, id)
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True
                statusS = False

                if mpn in quickships:
                    quickShip = True
                else:
                    quickShip = False

                # Shipping
                shippingWidth = common.formatFloat(sh.cell_value(i, 44))
                shippingLength = common.formatFloat(sh.cell_value(i, 43))
                shippingHeight = common.formatFloat(sh.cell_value(i, 45))
                shippingWeight = common.formatFloat(sh.cell_value(i, 42))

                if shippingWidth > 107 or shippingLength > 107 or shippingHeight > 107 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Name
                name = f"{name} {size} Rug"

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
                'disclaimer': disclaimer,
                'width': width,
                'length': length,
                'height': height,
                'size': size,
                'dimension': dimension,
                'specs': specs,

                'care': care,
                'material': material,
                'weight': shippingWeight,
                'country': country,
                'upc': upc,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
                'quickShip': quickShip,
                'whiteGlove': whiteGlove,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
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
