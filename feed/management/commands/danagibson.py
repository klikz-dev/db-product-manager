from django.core.management.base import BaseCommand
from feed.models import DanaGibson

import os
import environ
import pymysql
import xlrd
from shutil import copyfile

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Dana Gibson"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

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
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = DanaGibson.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.image()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=DanaGibson)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        blockMPNs = ['110-BlZ']
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/dana-gibson-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 1))
                sku = f"DG {mpn}"

                name = common.formatText(sh.cell_value(i, 4)).title()
                if "Lumbar" in name:
                    name = f"{name} Pillow"

                color = common.formatText(sh.cell_value(i, 3)).title()

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 2)).title()
                manufacturer = BRAND
                collection = common.formatText(sh.cell_value(i, 2))

                # Reconfigure
                pattern = name.replace(color, "").replace(
                    type, "").replace("Lamp", "").replace("  ", " ").strip()

                if type == "Bowl":
                    type = "Bowls"
                elif type == "Wastebasket":
                    type = "Wastebaskets"
                elif type == "Pendant":
                    type = "Pendants"
                elif type == "Tray":
                    type = "Trays"

                if not pattern or not color or not type:
                    continue
                #############

                # Main Information
                description = common.formatText(sh.cell_value(i, 17))
                width = common.formatFloat(sh.cell_value(i, 12))
                height = common.formatFloat(sh.cell_value(i, 10))
                depth = common.formatFloat(sh.cell_value(i, 14))

                # Additional Information
                specs = []
                for j in [21, 22, 26, 27, 28, 29]:
                    if sh.cell_value(i, 21):
                        specs.append((common.formatText(sh.cell_value(
                            1, j)).title(), common.formatText(sh.cell_value(i, j))))

                material = common.formatText(sh.cell_value(i, 19))
                finish = common.formatText(sh.cell_value(i, 20))
                country = common.formatText(sh.cell_value(i, 32))
                weight = common.formatFloat(sh.cell_value(i, 9))

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 5))
                map = common.formatFloat(sh.cell_value(i, 6))

                # Measurement
                uom = "Per Item"

                # Tagging
                tags = f"{sh.cell_value(i, 18)}, {pattern}, {type}"
                colors = color

                # Image
                thumbnail = sh.cell_value(i, 46)
                roomsets = []
                for id in range(52, 54):
                    if sh.cell_value(i, id):
                        roomsets.append(sh.cell_value(i, id))

                # Status
                statusP = True
                statusS = False

                if mpn in blockMPNs:
                    statusP = False

                # Stock
                if sh.cell_value(i, 34):
                    stockNote = f"{int(common.formatInt(sh.cell_value(i, 34)) / 24)} days"
                else:
                    stockNote = ""

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
                'width': width,
                'height': height,
                'depth': depth,

                'material': material,
                'finish': finish,
                'country': country,
                'specs': specs,
                'weight': weight,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,

                'stockNote': stockNote,
            }
            products.append(product)

        wb = xlrd.open_workbook(f"{FILEDIR}/dana-gibson-lamps-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 1))
                sku = f"DG {mpn}"

                name = common.formatText(sh.cell_value(i, 4)).title()
                color = common.formatText(sh.cell_value(i, 3)).title()

                pattern = name.replace(color, "").replace(
                    "Lamp", "").replace("  ", " ").strip()

                # Categorization
                brand = BRAND
                type = "Lighting"
                manufacturer = BRAND
                collection = "Lighting"

                # Main Information
                description = common.formatText(sh.cell_value(i, 22))
                width = common.formatFloat(sh.cell_value(i, 13))
                height = common.formatFloat(sh.cell_value(i, 12))

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 5))
                map = common.formatFloat(sh.cell_value(i, 6))

                # Measurement
                uom = "Per Item"

                # Tagging
                colors = color

                # Status
                statusP = True
                statusS = False

                # Stock
                stockNote = f"{int(int(sh.cell_value(i, 35)) / 24)} days"

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
                'width': width,
                'height': height,

                'cost': cost,
                'map': map,

                'uom': uom,

                'colors': colors,

                'statusP': statusP,
                'statusS': statusS,

                'stockNote': stockNote,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        products = DanaGibson.objects.all()

        for product in products:
            for fname in os.listdir(f"{FILEDIR}/images/danagibson/"):
                if product.mpn.replace("-", "").lower() in fname.lower():
                    print(f"{FILEDIR}/images/danagibson/{fname}")

                    if "_bak" in fname:
                        copyfile(f"{FILEDIR}/images/danagibson/{fname}",
                                 f"{FILEDIR}/../../../images/roomset/{product.productId}_2.jpg")
                    else:
                        copyfile(f"{FILEDIR}/images/danagibson/{fname}",
                                 f"{FILEDIR}/../../../images/product/{product.productId}.jpg")
