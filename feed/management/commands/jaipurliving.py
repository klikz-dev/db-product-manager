from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import JaipurLiving

import os
import environ
import pymysql
import openpyxl
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
                src="/jaipur/Jaipur Living Master Data Template.xlsx", dst=f"{FILEDIR}/jaipurliving-master.xlsx", fileSrc=True, delete=False)
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

        if "white-glove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove", logic=True)

        if "quick-ship" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="quickShip", tag="Quick Ship", logic=True)

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/jaipur/Jaipur Living Master Data Template.xlsx", dst=f"{FILEDIR}/jaipur-living-master.xlsx", fileSrc=True, delete=False)
                    processor.databaseManager.downloadFileFromFTP(
                        src="Jaipur inventory feed.csv", dst=f"{FILEDIR}/jaipur-living-inventory.csv")

                    products = processor.fetchFeed()
                    processor.databaseManager.writeFeed(products=products)
                    processor.databaseManager.statusSync(fullSync=False)

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
        # Get Product Feed
        products = []

        wb = openpyxl.load_workbook(
            f"{FILEDIR}/jaipurliving-master.xlsx", data_only=True)
        sh = wb.worksheets[0]

        for row in sh.iter_rows(min_row=2, values_only=True):
            try:
                # Primary Keys
                mpn = common.toText(row[7])
                sku = f"JL {mpn}"

                pattern = common.toText(row[13])
                if common.toText(row[53]):
                    pattern = f"{pattern} {common.toText(row[53])}"

                color = common.toText(row[56])
                if common.toText(row[57]):
                    color = f"{color} / {common.toText(row[57])}"

                name = common.toText(row[9]).title().replace(BRAND, "").strip()

                # Categorization
                brand = BRAND
                manufacturer = BRAND
                type = common.toText(row[0]).title()
                collection = common.toText(row[12])

                # Main Information
                description = row[25]
                width = common.toFloat(row[21])
                length = common.toFloat(row[22])
                height = common.toFloat(row[24])

                size = common.toText(row[18]).replace("X", " x ").replace(
                    "Folded", "").replace("BOX", "").replace("  ", " ").strip()

                # Additional Information
                front = common.toText(row[35])
                back = common.toText(row[36])
                filling = common.toText(row[37])

                material = f"Front: {front}"
                if back:
                    material += f", Back: {back}"
                if filling:
                    material += f", Filling: {filling}"

                care = common.toText(row[39])
                country = common.toText(row[32])
                upc = common.toInt(row[6])
                weight = common.toFloat(row[88])

                features = []
                for id in range(26, 32):
                    if row[id]:
                        features.append(common.toText(row[id]))

                # Measurement
                uom = "Item"

                # Pricing
                cost = common.toFloat(row[15])
                map = common.toFloat(row[16])
                msrp = common.toFloat(row[17])

                # Tagging
                keywords = ", ".join(
                    (row[19], row[50], row[51], pattern, name, description, type, ", ".join(features)))
                colors = color

                # Image
                thumbnail = row[89]
                if thumbnail == "http://cdn1-media.s3.us-east-1.amazonaws.com/product_links/Product_Images/":
                    thumbnail = f"{thumbnail}{str(row[8]).strip()}.jpg"

                roomsets = []
                for id in range(90, 104):
                    if row[id]:
                        roomsets.append(row[id])

                # Status
                if row[19] == "Swatches":
                    statusP = False
                else:
                    statusP = True
                statusS = False

                # Shipping
                shippingWidth = common.toFloat(row[86])
                shippingLength = common.toFloat(row[85])
                shippingHeight = common.toFloat(row[87])
                shippingWeight = common.toFloat(row[88])
                if shippingWidth > 95 or shippingLength > 95 or shippingHeight > 95 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Fine-tuning
                name = f"{collection} {pattern} {color} {size} {type}"

                type_mapping = {
                    "Accent Furniture": "Furniture",
                    "Décor": "Throw",
                }
                if type in type_mapping:
                    type = type_mapping[type]

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

                'features': features,

                'uom': uom,

                'cost': cost,
                'map': map,
                'msrp': msrp,

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

    def hires(self):
        con = self.con
        csr = con.cursor()
        csr.execute(
            f"SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 20 AND M.Brand = '{BRAND}'")

        hasImage = []
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        csr.close()

        products = JaipurLiving.objects.all()
        for product in products:
            if not product.productId or product.productId in hasImage:
                continue

            common.hiresdownload(str(product.thumbnail).strip().replace(
                " ", "%20"), "{}_20.jpg".format(product.productId))

    def inventory(self):
        stocks = []

        products = JaipurLiving.objects.all()
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': product.stockP,
                'note': product.stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
