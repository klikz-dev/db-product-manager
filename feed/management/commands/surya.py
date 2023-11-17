from django.core.management.base import BaseCommand
from feed.models import Surya
from django.db.models import Q

import os
import environ
import pymysql
import xlrd
import csv
import codecs
import time

from library import database, debug, common

formatText = common.formatText
formatInt = common.formatInt
formatFloat = common.formatFloat

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Surya"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products)

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
            products = Surya.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=False)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=True)

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires(missingOnly=True)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "white-glove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "best-seller" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="bestSeller", tag="Best Selling")

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/surya/inventory_dbest.csv", dst=f"{FILEDIR}/surya-inventory.csv", fileSrc=True, delete=True)
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
            con=self.con, brand=BRAND, Feed=Surya)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Invalid images
        unavailable = []
        wb = xlrd.open_workbook(f'{FILEDIR}/surya-unavailable.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            mpn = formatText(sh.cell_value(i, 0))
            unavailable.append(mpn)

        # Best Sellers
        bestsellingColors = []
        wb = xlrd.open_workbook(f"{FILEDIR}/surya-bestsellers.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            color = common.formatText(sh.cell_value(i, 0))
            bestsellingColors.append(color)

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f'{FILEDIR}/surya-master-new.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = formatText(sh.cell_value(i, 4))
                debug.debug(BRAND, 0, "Fetching Product MPN: {}".format(mpn))

                sku = f"SR {mpn}"
                pattern = formatText(sh.cell_value(i, 1))
                color = formatText(sh.cell_value(i, 3))

                if sh.cell_value(i, 8):
                    name = formatText(sh.cell_value(i, 8))
                else:
                    name = ""

                # Categorization
                brand = BRAND

                typeText = formatText(sh.cell_value(
                    i, 6)) or formatText(sh.cell_value(i, 5))
                typeText = typeText.title()
                if not typeText or "Swatch" in typeText:
                    continue

                type_mapping = {
                    "Decorative Object/Sculpture": "Sculpture",
                    "Vase": "Vases",
                    "Candleholder": "Candleholders",
                    "Decorative Tray": "Trays",
                    "Decorative Bowl": "Decorative Bowls",
                    "Box": "Boxes",
                    "Jar": "Ginger Jar",
                    "Planter": "Planters",
                    "Lantern": "Accents",
                    "Bookend": "Bookends",
                    "Basket": "Baskets",
                    "Coffee Table": "Coffee Tables",
                    "Ottoman": "Ottomans",
                    "End Table": "End Tables",
                    "Stool": "Stools",
                    "Bench": "Benches",
                    "Console Table": "Consoles",
                    "Dining Table": "Dining Tables",
                    "Dining Chair": "Dining Chairs",
                    "Bookcase": "Bookcases",
                    "Nightstand": "Furniture",
                    "Cabinet": "Cabinets",
                    "Swivel Chair": "Furniture",
                    "Sideboard": "Furniture",
                    "Lounger": "Furniture",
                    "Bar Cart": "Furniture",
                    "Modular Chair": "Chairs",
                    "Platform Bed": "Beds",
                    "Dining Bench": "Benches",
                    "Pendant": "Pendants",
                    "Accent Table Lamp": "Table Lamps",
                    "Accent Floor Lamp": "Floor Lamps",
                    "Chandelier": "Chandeliers",
                    "Wall Sconce": "Wall Sconces",
                    "Task Table Lamp": "Table Lamps",
                    "Buffet Table Lighting": "Lighting",
                    "Task Floor Lighting": "Lighting",
                    "Globe Table Lamp": "Table Lamps",
                    "Globe Floor Lighting": "Lighting",
                    "Tray Table Floor Lighting": "Lighting",
                    "Hand Made Rug": "Rug",
                    "Machine Woven Rug": "Rug",
                    "Rug Pad For Hard Surfaces - Roll": "Rug",
                    "Rug Pad For Hard Surfaces": "Rug",
                    "Rug Pad For Outdoor Hard Surfaces": "Rug",
                    "Rug Pad For Outdoor Hard Surfaces - Roll": "Rug",
                    "Rug Pad For Hard Surfaces And Carpet": "Rug",
                    "Rug Pad For Hard Surfaces And Carpet - Roll": "Rug",
                    "Lumbar Pillow": "Pillow",
                    "Accent Pillow": "Pillow",
                    "Sham": "Pillow",
                    "Duvet": "Accents",
                    "Throw": "Throws",
                    "Bedskirt": "Accents",
                    "Quilt": "Pillow",
                    "Floor Pillow": "Pillow",
                    "Bedding Runner": "Accents",
                    "Bolster Pillow": "Pillow",
                    "Mirror": "Mirrors",
                    "Overmantel Mirror": "Mirrors",
                    "Accent Mirror": "Mirrors",
                    "Framed Art": "Wall Art",
                    "Wall Hanging": "Wall Art",
                    "Full Length Mirror": "Mirrors",
                    "Canvas Art": "Wall Art",
                    "Sofa": "Sofas",
                    "Dresser": "Dressers",
                    "Chair And A Half": "Accent Chairs",
                    "Upholstered Bed": "Beds",
                    "Decorative Accent": "Decorative Accents",
                    "Textiles": "Pillow",
                    "Wall Decor": "Wall Art"
                }

                if typeText in type_mapping:
                    type = type_mapping[typeText]
                else:
                    type = typeText

                manufacturer = BRAND
                collection = pattern

                # Main Information
                description = formatText(sh.cell_value(i, 9))
                usage = typeText
                width = formatFloat(sh.cell_value(i, 25))
                height = formatFloat(sh.cell_value(i, 26))
                depth = formatFloat(sh.cell_value(i, 24))

                if height == 0 and depth != 0:
                    height = depth
                    depth = 0

                if "D" in sh.cell_value(i, 22):
                    size = ""
                    dimension = formatText(sh.cell_value(i, 22))
                else:
                    size = formatText(sh.cell_value(i, 22))
                    dimension = ""

                # Additional Information
                material = formatText(sh.cell_value(i, 18))
                care = f"{formatText(sh.cell_value(i, 41))}, {formatText(sh.cell_value(i, 42))}"
                country = formatText(sh.cell_value(i, 33))
                upc = formatInt(sh.cell_value(i, 11))

                weight = formatFloat(sh.cell_value(i, 27)) or 5
                specs = [
                    ("Colors", formatText(sh.cell_value(i, 15))),
                    ("Weight", f"{weight} lbs"),
                ]

                # Measurement
                uom = "Per Item"

                # Pricing
                cost = round(formatFloat(sh.cell_value(i, 13))
                             * 0.8, 2)  # Tmp: Promo
                map = round(formatFloat(sh.cell_value(i, 14))
                            * 0.8, 2)  # Tmp: Promo

                if cost == 0:
                    debug.debug(BRAND, 1, "Produt Cost error {}".format(mpn))
                    continue

                # Tagging
                tags = f"{formatText(sh.cell_value(i, 19))}, {formatText(sh.cell_value(i, 20))}"
                if formatText(sh.cell_value(i, 37)) == "Yes":
                    tags = "{}, Outdoor".format(tags)
                tags = f"{tags}, {type}, {collection}, {pattern}"

                colors = formatText(sh.cell_value(i, 15))

                # Status
                statusP = True
                statusS = False

                if mpn in unavailable:
                    debug.debug(
                        BRAND, 1, "Product Image is unavailable for MPN: {}".format(mpn))
                    statusP = False

                if color in bestsellingColors:
                    bestSeller = True
                else:
                    bestSeller = False

                # Image
                thumbnail = sh.cell_value(i, 120)

                roomsets = []
                for id in range(121, 126):
                    if sh.cell_value(i, id) != "":
                        roomsets.append(sh.cell_value(i, id))

                # Shipping
                shippingHeight = common.formatFloat(sh.cell_value(i, 30))
                shippingWidth = common.formatFloat(sh.cell_value(i, 29))
                shippingDepth = common.formatFloat(sh.cell_value(i, 28))
                shippingWeight = common.formatFloat(sh.cell_value(i, 31))
                if shippingWidth > 107 or shippingHeight > 107 or shippingDepth > 107 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'upc': upc,
                'pattern': pattern,
                'color': color,
                'name': name,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'usage': usage,
                'width': width,
                'height': height,
                'depth': depth,
                'size': size,
                'dimension': dimension,
                'specs': specs,

                'material': material,
                'care': care,
                'country': country,

                'weight': shippingWeight,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'cost': cost,
                'map': map,

                'statusP': statusP,
                'statusS': statusS,
                'whiteGlove': whiteGlove,
                'bestSeller': bestSeller,

                'thumbnail': thumbnail,
                'roomsets': roomsets,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/surya-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Sku":
                continue

            sku = f"SR {formatText(row[0])}"
            stockP = formatInt(row[1])
            stockNote = formatText(row[2])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote,
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)

    def hires(self, missingOnly=False):
        hasImage = []

        self.csr = self.con.cursor()
        self.csr.execute(
            f"SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 20 AND M.Brand = '{BRAND}'")
        for row in self.csr.fetchall():
            hasImage.append(str(row[0]))
        self.csr.close()

        products = Surya.objects.all()
        for product in products:
            if "512x512" not in product.thumbnail:
                continue

            if not product.productId:
                continue

            if missingOnly and product.productId in hasImage:
                continue

            hiresImage = product.thumbnail.replace(
                "512x512", "RAW").replace(" ", "%20")

            common.hiresdownload(hiresImage, f"{product.productId}_20.jpg")

            debug.debug(
                BRAND, 0, f"Copied {hiresImage} to {product.productId}_20.png")
