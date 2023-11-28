from django.core.management.base import BaseCommand
from feed.models import JamieYoung

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

BRAND = "Jamie Young"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
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
            processor.databaseManager.createProducts(formatPrice=False)

        if "update" in options['functions']:
            processor = Processor()
            products = JamieYoung.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=True)

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires()

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "best-seller" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="bestSeller", tag="Best Selling")

        if "white-glove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove", logic=True)

        if "outlet" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="outlet", tag="Outlet", logic=True)

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/jamieyoung", dst=f"{FILEDIR}/jamieyoung-inventory.csv", fileSrc=False, delete=False)

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
            con=self.con, brand=BRAND, Feed=JamieYoung)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Available Items
        available_mpns = []
        f = open(f"{FILEDIR}/jamieyoung-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))
        for row in cr:
            available_mpns.append(row[1])

        # Outlet
        outletMPNs = [
            "9CASPWHD131C",
            "5SHOR-PENA",
            "20KAI-BECA",
            "20SHEL-BEDO",
            "20WATE-CODG",
            "7LONG-BOGR",
            "7LONG-BOWH",
            "7LOTU-SMWH",
            "7MARB-XLWH"
        ]

        # Best Selling
        bestSellingPatterns = [
            "Rectangle Audrey",
            "Daybreak",
            "Chester Round Side Table",
            "Coco Pedestal",
            "Masonry",
            "Landslide",
            "Vapor",
            "Capital Rectangle",
            "Audrey Beaded",
            "Riviera Framed",
            "Maldives Framed",
            "Organic Round",
            "Watercolor",
            "Gilbert",
            "Serai",
            "Vapor Vase",
            "Kaya",
            "Agate Slice",
            "Evergreen Rectangle",
            "Lagoon",
            "Basketweave",
            "Kain Console",
            "Arch",
            "Mortar",
            "Willow",
            "Studio",
            "Flowering Lotus",
            "Oceane Gourd",
            "Batik",
            "Napa",
            "Barley Twist",
            "Amphora",
            "Farmhouse Bench",
            "Concentric",
            "Mirage Abstract",
            "Kain Side Table",
            "Vapor Single",
        ]

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/jamieyoung-master-new.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(2, sh.nrows):
            # Primary Keys
            mpn = common.formatText(sh.cell_value(i, 0))
            sku = f"JY {mpn}"
            pattern = common.formatText(sh.cell_value(i, 2))
            color = common.formatText(
                sh.cell_value(i, 35)).replace(",", " /")

            # Categorization
            brand = BRAND
            type = common.formatText(sh.cell_value(i, 7)).title()
            manufacturer = BRAND
            collection = str(sh.cell_value(i, 4))

            # Main Information
            description = common.formatText(sh.cell_value(i, 26))
            disclaimer = common.formatText(sh.cell_value(i, 36))
            upc = common.formatInt(sh.cell_value(i, 1))

            width = common.formatFloat(sh.cell_value(i, 16))
            height = common.formatFloat(sh.cell_value(i, 14))
            depth = common.formatFloat(sh.cell_value(i, 18))
            dimension = common.formatText(sh.cell_value(i, 19))

            weight = common.formatFloat(sh.cell_value(i, 12))
            specs = [
                ("Weight", f"{weight} lbs"),
            ]

            # Additional Information
            material = common.formatText(sh.cell_value(i, 34))
            care = common.formatText(sh.cell_value(i, 37))
            country = common.formatText(sh.cell_value(i, 46))

            features = [str(sh.cell_value(i, id)).strip()
                        for id in range(28, 33) if sh.cell_value(i, id)]
            features.extend([str(sh.cell_value(i, id)).strip()
                            for id in range(38, 45) if sh.cell_value(i, id)])

            # Measurement
            uom = "Per Item"

            # Pricing
            cost = common.formatFloat(sh.cell_value(i, 8))
            map = common.formatFloat(sh.cell_value(i, 9))
            msrp = common.formatFloat(sh.cell_value(i, 10))

            # Tagging
            tags = f"{sh.cell_value(i, 19)}, {','.join(features)}, {collection}, {description}"
            colors = color

            # Shipping
            shippingWidth = common.formatFloat(sh.cell_value(
                i, 58)) + common.formatFloat(sh.cell_value(i, 62))
            shippingLength = common.formatFloat(sh.cell_value(
                i, 57)) + common.formatFloat(sh.cell_value(i, 61))
            shippingHeight = common.formatFloat(sh.cell_value(
                i, 59)) + common.formatFloat(sh.cell_value(i, 63))
            shippingWeight = common.formatFloat(sh.cell_value(
                i, 56)) + common.formatFloat(sh.cell_value(i, 60))

            if shippingWidth > 107 or shippingLength > 107 or shippingHeight > 107 or shippingWeight > 40:
                whiteGlove = True
            else:
                whiteGlove = False

            # Stock
            stockNote = "3 days"

            # Image
            thumbnail = common.formatText(
                sh.cell_value(i, 69)).replace("dl=0", "dl=1")
            roomsets = []
            for id in range(70, 83):
                roomset = common.formatText(
                    sh.cell_value(i, id)).replace("dl=0", "dl=1")
                if roomset:
                    roomsets.append(roomset)

            # Pattern Name
            ptypeTmp = type
            if ptypeTmp[len(ptypeTmp) - 1] == "s":
                ptypeTmp = ptypeTmp[:-1]

            for typeword in ptypeTmp.split(" "):
                pattern = pattern.replace(typeword, "")

            pattern = pattern.replace(
                "**MUST SHIP COMMON CARRIER**", "").replace("  ", " ").strip()
            ##############

            # Status
            statusS = False

            if "Sideboard" in pattern or "Console" in pattern or mpn not in available_mpns:
                statusP = False
            else:
                statusP = True

            if pattern in bestSellingPatterns:
                bestSeller = True
            else:
                bestSeller = False

            if mpn in outletMPNs:
                outlet = True
            else:
                outlet = False

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
                'disclaimer': disclaimer,
                'width': width,
                'height': height,
                'depth': depth,
                'dimension': dimension,
                'specs': specs,
                'features': features,

                'material': material,
                'care': care,
                'country': country,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'statusP': statusP,
                'statusS': statusS,
                'bestSeller': bestSeller,
                'outlet': outlet,

                'whiteGlove': whiteGlove,

                'weight': shippingWeight,

                'stockNote': stockNote,

                'thumbnail': thumbnail,
                'roomsets': roomsets,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def hires(self):
        images = os.listdir(f"{FILEDIR}/images/jamie-young")

        for image in images:
            mpn = image.split(".")[0]

            try:
                product = JamieYoung.objects.get(mpn=mpn)
                if not product.productId:
                    continue

            except JamieYoung.DoesNotExist:
                continue

            copyfile(f"{FILEDIR}/images/jamie-young/{image}",
                     f"{FILEDIR}/../../../images/hires/{product.productId}_20.png")

            debug.debug(
                BRAND, 0, f"Copied {image} to {product.productId}_20.png")

            os.remove(f"{FILEDIR}/images/jamie-young/{image}")

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/jamieyoung-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))
        for row in cr:
            try:
                mpn = row[1]
                quantity = int(row[2])

                product = JamieYoung.objects.get(mpn=mpn)
            except JamieYoung.DoesNotExist:
                continue
            except Exception as e:
                print(str(e))
                continue

            stock = {
                'sku': product.sku,
                'quantity': quantity,
                'note': product.stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
