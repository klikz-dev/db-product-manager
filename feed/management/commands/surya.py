from django.core.management.base import BaseCommand

import os
import environ
import pymysql
import xlrd

from library import database, debug

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Surya"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()
        if "feed" in options['functions']:
            processor.feed()

        if "sync" in options['functions']:
            processor.sync()

        if "add" in options['functions']:
            processor.add()

        if "update" in options['functions']:
            processor.update()

        if "tag" in options['functions']:
            processor.tag()

        if "sample" in options['functions']:
            processor.sample()

        if "shipping" in options['functions']:
            processor.shipping()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(self.con)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(FILEDIR + 'surya-master.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = str(sh.cell_value(i, 1)).strip()
                debug.debug(BRAND, 0, "Fetching Product MPN: {}".format(mpn))

                sku = "SR {}".format(mpn)
                try:
                    upc = int(sh.cell_value(i, 5))
                except:
                    upc = ""
                pattern = str(sh.cell_value(i, 4)).strip()
                color = str(sh.cell_value(i, 2)).strip()

                # Categorization
                brand = BRAND

                typeText = str(sh.cell_value(i, 0)).strip().title()
                if typeText == "Bedding":
                    type = "Furniture"
                elif typeText == "Accent And Lounge Chairs":
                    type = "Accents"
                elif typeText == "Ceiling Lighting":
                    type = "Lighting"
                elif typeText == "Rugs":
                    type = "Rug"
                elif typeText == "Wall Art - Stock":
                    type = "Wall Art"
                else:
                    type = typeText

                manufacturer = BRAND
                collection = str(sh.cell_value(i, 4))

                # Main Information
                description = str(sh.cell_value(i, 3)).strip()
                try:
                    width = round(float(sh.cell_value(i, 16)), 2)
                except:
                    width = 0
                try:
                    length = round(float(sh.cell_value(i, 15)), 2)
                except:
                    length = 0
                try:
                    height = round(float(sh.cell_value(i, 17)), 2)
                except:
                    height = 0
                size = str(sh.cell_value(i, 13)).strip()

                # Additional Information
                material = str(sh.cell_value(i, 10)).strip()
                try:
                    weight = float(sh.cell_value(i, 18))
                except:
                    weight = 5
                specs = [
                    {
                        "key": "Construction",
                        "value": str(sh.cell_value(i, 21)).strip()
                    }
                ]

                # Measurement
                uom = "Per Item"

                # Pricing
                try:
                    cost = round(float(sh.cell_value(i, 6)), 2)
                except:
                    debug.debug(BRAND, 1, "Produt Cost error {}".format(mpn))
                    continue

                try:
                    map = round(float(sh.cell_value(i, 7)), 2)
                except:
                    debug.debug(BRAND, 1, "Produt MAP error {}".format(mpn))
                    map = 0

                try:
                    msrp = round(float(sh.cell_value(i, 8)), 2)
                except:
                    debug.debug(BRAND, 1, "Produt MSRP error {}".format(mpn))
                    msrp = 0

                # Tagging
                tags = str(sh.cell_value(i, 11)).strip()
                if str(sh.cell_value(i, 23)).strip() == "Yes":
                    tags = "{}, Outdoor".format(tags)
                colors = str(sh.cell_value(i, 9)).strip()

                statusP = True
                statusS = False
                whiteShip = False
                if "white glove" in str(sh.cell_value(i, 17)).lower() or "ltl" in str(sh.cell_value(i, 17)).lower():
                    whiteShip = True

                # Image
                thumbnail = str(sh.cell_value(i, 25)).strip()
                roomsets = []
                for id in range(26, 31):
                    roomset = str(sh.cell_value(i, id)).strip()
                    if roomset != "":
                        roomsets.append(roomset)

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
                'height': height,
                'weight': weight,
                'size': size,

                'material': material,
                'specs': specs,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'statusP': statusP,
                'statusS': statusS,
                'whiteShip': whiteShip,

                'thumbnail': thumbnail,
                'roomsets': roomsets,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def feed(self):
        products = self.fetchFeed()
        self.databaseManager.writeFeed(BRAND, products)

    def sync(self):
        self.databaseManager.statusSync(BRAND)

    def add(self):
        self.databaseManager.createProducts(BRAND)

    def update(self):
        self.databaseManager.updateProducts(BRAND)

    def tag(self):
        self.databaseManager.updateTags(BRAND, False)

    def image(self):
        self.databaseManager.downloadImages(BRAND)

    def sample(self):
        self.databaseManager.customTags(BRAND, "statusS", "NoSample")

    def shipping(self):
        self.databaseManager.customTags(BRAND, "whiteShip", "White Glove")