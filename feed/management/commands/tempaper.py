from django.core.management.base import BaseCommand
from feed.models import Tempaper

import os
import environ
import pymysql
import xlrd
import time
from shutil import copyfile

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Tempaper"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadFileFromSFTP(
                src="/tempaper/datasheets/tempaper-master.xlsx", dst=f"{FILEDIR}/tempaper-master.xlsx", fileSrc=True, delete=False)
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(
                formatPrice=True, private=True)

        if "update" in options['functions']:
            processor = Processor()
            products = Tempaper.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True, private=True)

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

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=False)

        if "roomset" in options['functions']:
            processor = Processor()
            processor.roomset()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/tempaper/datasheets/tempaper-master.xlsx", dst=f"{FILEDIR}/tempaper-master.xlsx", fileSrc=True, delete=False)
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
            con=self.con, brand=BRAND, Feed=Tempaper)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/tempaper-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 3))
                sku = f"TP {mpn}"

                pattern = common.formatText(sh.cell_value(i, 4))
                color = common.formatText(sh.cell_value(i, 5))

                name = common.formatText(sh.cell_value(i, 8))

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 0))
                manufacturer = brand
                collection = common.formatText(
                    sh.cell_value(i, 2).replace("Tempaper", ""))

                # Main Information
                description = common.formatText(sh.cell_value(i, 9))
                width = common.formatFloat(sh.cell_value(i, 17))
                length = common.formatFloat(sh.cell_value(i, 18)) * 12
                coverage = common.formatText(sh.cell_value(i, 21))

                specs = [
                    ("Width", f"{round(width / 36, 2)} yd ({width} in)"),
                    ("Length", f"{round(length / 36, 2)} yd ({length} in)"),
                    ("Coverage", coverage),
                ]

                if type == "Rug":
                    specs = []
                    dimension = coverage
                else:
                    width = 0
                    length = 0
                    dimension = ""

                # Additional Information
                yards = common.formatInt(sh.cell_value(i, 14))
                weight = common.formatFloat(sh.cell_value(i, 22))
                match = common.formatText(sh.cell_value(i, 25))
                material = common.formatText(sh.cell_value(i, 27))
                care = common.formatText(sh.cell_value(i, 32))
                country = common.formatText(sh.cell_value(i, 33))
                features = []
                for id in range(28, 30):
                    feature = common.formatText(sh.cell_value(i, id))
                    if feature:
                        features.append(feature)

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 10))
                map = common.formatFloat(sh.cell_value(i, 11))

                # Measurement
                uom = f"Per {common.formatText(sh.cell_value(i, 13))}"

                # Tagging
                colors = color
                tags = f"{material}, {match}, {sh.cell_value(i, 28)}, {sh.cell_value(i, 29)}, {collection}, {pattern}, {description}"

                # Image
                thumbnail = sh.cell_value(i, 34).replace("dl=0", "dl=1")

                roomsets = []
                for id in range(35, 39):
                    roomset = sh.cell_value(i, id).replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True
                statusS = False

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
                'specs': specs,
                'width': width,
                'length': length,
                'dimension': dimension,

                'material': material,
                'yards': yards,
                'weight': weight,
                'country': country,
                'match': match,
                'care': care,
                'features': features,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def roomset(self):
        mpn_map = {
            "BB14034": "BB4034",
            "BB14035": "BB4035",
            "BR14137": "BR4137",
            "BR14138": "BR4138",
            "BU10633": "BU663",
            "BU10664": "BU664",
            "DI534": "DI10534",
            "DI543": "DI10543",
            "FE4023": "FE411",
            "FN14164": "FN4164",
            "FS14159": "FS4159",
            "FS14160": "FS4160",
            "GM10564": "GM564",
            "GM10565": "GM565",
            "GR10505": "GR505",
            "GR10533": "GR533",
            "GR10589": "GR589",
            "HG5225": "HG15225",
            "HG5226": "HG15226",
            "HG5227": "HG15227",
            "HG5228": "HG15228",
            "HG5229": "HG15229",
            "HG5230": "HG15230",
            "HG5231": "HG15231",
            "HG5232": "HG15232",
            "IN10412": "IN412",
            "IN14024": "IN4024",
            "MA10083": "MA083",
            "MP14163": "MP4163",
            "MS10579": "MS579",
            "PE10042": "PE042",
            "PE10508": "PE508",
            "PE633": "PE10633",
            "QE14161": "QE4161",
            "QE14162": "QE4162",
            "TR562": "TR529",
        }

        products = Tempaper.objects.all()
        images = os.listdir(f"{FILEDIR}/images/tempaper/")

        for product in products:
            mpn = product.mpn
            productId = product.productId

            if mpn in mpn_map and mpn_map[mpn]:
                mpn = mpn_map[mpn]

            roomsets = []
            for image in images:
                if mpn.lower() in image.lower() and image.lower() not in product.thumbnail.lower():
                    roomsets.append(image)

            for index, roomset in enumerate(roomsets):
                copyfile(f"{FILEDIR}/images/tempaper/{roomset}",
                         f"{FILEDIR}/../../../images/roomset/{productId}_{index + 2}.jpg")

                debug.debug(BRAND, 0, "Roomset Image {}_{}.jpg".format(
                    productId, index + 2))

    def inventory(self):
        stocks = []

        wb = xlrd.open_workbook(f"{FILEDIR}/tempaper-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 3))
                sku = f"TP {mpn}"

                stockP = common.formatInt(sh.cell_value(i, 6))

                stock = {
                    'sku': sku,
                    'quantity': stockP,
                    'note': "",
                }
                stocks.append(stock)
            except Exception as e:
                print(e)
                continue

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
