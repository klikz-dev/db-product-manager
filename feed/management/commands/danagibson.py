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
        processor = Processor()

        if "feed" in options['functions']:
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "validate" in options['functions']:
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = DanaGibson.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "image" in options['functions']:
            processor.image()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=DanaGibson)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/dana-gibson-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 1))
                sku = f"DG {mpn}"

                title = common.formatText(sh.cell_value(i, 4)).title()
                if "Lumbar" in title:
                    title = f"{title} Pillow"

                color = common.formatText(sh.cell_value(i, 3)).title()

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 2)).title()
                manufacturer = BRAND
                collection = common.formatText(sh.cell_value(i, 2))

                # Reconfigure
                pattern = title.replace(color, "").replace(
                    type, "").replace("Lamp", "").replace("  ", " ").strip()

                if type == "Bowl":
                    type = "Bowls"

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
                upc = sh.cell_value(i, 0)

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

                # Stock
                stockNote = f"{int(int(sh.cell_value(i, 34)) / 24)} days"

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                'title': title,

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
                    if "_bak" in fname:
                        copyfile(f"{FILEDIR}/images/danagibson/{fname}",
                                 f"{FILEDIR}/../../../images/roomset/{product.productId}_2.jpg")
                    else:
                        copyfile(f"{FILEDIR}/images/danagibson/{fname}",
                                 f"{FILEDIR}/../../../images/product/{product.productId}.jpg")
