from django.core.management.base import BaseCommand
from brands.models import Feed

import os
import environ
import pymysql
import xlrd
from shutil import copyfile

from library import database, debug, shopify, common

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Stark Studio"


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

        wb = xlrd.open_workbook(FILEDIR + 'stark-studio-master.xlsx')
        for index in [0, 1, 2]:
            sh = wb.sheet_by_index(index)
            for i in range(2, sh.nrows):
                try:
                    # Primary Keys
                    mpn = str(sh.cell_value(i, 4)).strip()
                    sku = "SS {}".format(mpn)
                    try:
                        upc = int(sh.cell_value(i, 2))
                    except:
                        upc = ""
                    pattern = str(sh.cell_value(i, 0)).split("-")[0].strip()
                    color = str(sh.cell_value(i, 1)).strip()

                    # Categorization
                    brand = BRAND
                    type = "Rug"
                    manufacturer = "{} {}".format(brand, type)
                    if index == 0:
                        collection = "Essentials Machinemades"
                    if index == 1:
                        collection = "Essentials Handmades"
                    if index == 2:
                        collection = "Fabricated Rug Program"

                    # Main Information
                    description = str(sh.cell_value(i, 11)).strip()
                    try:
                        width = int(sh.cell_value(i, 8))
                    except:
                        width = 0
                    try:
                        length = int(sh.cell_value(i, 9))
                    except:
                        length = 0

                    # Additional Information
                    material = str(sh.cell_value(i, 19)).strip()
                    country = str(sh.cell_value(i, 20)).strip()
                    try:
                        weight = float(sh.cell_value(i, 12))
                    except:
                        weight = 5

                    # Measurement
                    uom = "Per Item"

                    # Pricing
                    try:
                        cost = round(
                            float(str(sh.cell_value(i, 5)).replace("$", "")), 2)
                    except:
                        debug("StarkStudio", 1,
                              "Produt Cost error {}".format(mpn))
                        continue

                    try:
                        map = round(
                            float(str(sh.cell_value(i, 6)).replace("$", "")), 2)
                    except:
                        debug("StarkStudio", 1, "Produt MAP error {}".format(mpn))
                        continue

                    # Tagging
                    tags = description
                    colors = color

                    statusP = True
                    statusS = False
                    try:
                        stockNote = str(sh.cell_value(
                            i, 21)).strip().capitalize()
                    except:
                        stockNote = ""

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
                    'weight': weight,

                    'material': material,
                    'country': country,

                    'uom': uom,

                    'tags': tags,
                    'colors': colors,

                    'cost': cost,
                    'map': map,

                    'statusP': statusP,
                    'statusS': statusS,
                    'stockNote': stockNote
                }
                products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        imageDir = FILEDIR + "images/starkstudio/"

        products = Feed.objects.filter(brand=BRAND)
        for product in products:
            productStr = "{} {}".format(product.pattern, product.color).replace(
                ",", "").replace("/", " ").lower()

            for fname in os.listdir(imageDir):
                try:
                    imageStr = fname.lower().replace(
                        ".jpg", "").split(" ", 1)[1]
                except:
                    imageStr = fname.lower().replace(".jpg", "")

                if productStr in imageStr or imageStr in productStr:
                    if "_CL" in fname:
                        print("Roomset 2: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/roomset/{}_2.jpg".format(product.productId))

                    elif "_ALT1" in fname:
                        print("Roomset 3: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/roomset/{}_3.jpg".format(product.productId))

                    elif "_ALT2" in fname:
                        print("Roomset 4: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/roomset/{}_4.jpg".format(product.productId))

                    elif "_RM" in fname:
                        print("Roomset 5: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/roomset/{}_5.jpg".format(product.productId))

                    else:
                        print("Product: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/product/{}.jpg".format(product.productId))

    def feed(self):
        products = self.fetchFeed()
        self.databaseManager.writeFeed(BRAND, products)

    def sync(self):
        self.databaseManager.statusSync(BRAND)

    def add(self):
        products = Feed.objects.filter(brand=BRAND)

        for product in products:
            try:
                createdInDatabase = self.databaseManager.createProduct(
                    BRAND, product)
                if not createdInDatabase:
                    continue
            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            try:
                product.productId = shopify.NewProductBySku(
                    product.sku, self.con)
                product.save()

                self.downloadImages(
                    product.productId, product.thumbnail, product.roomsets)

                debug.debug(BRAND, 0, "Created New product ProductID: {}, SKU: {}".format(
                    product.productId, product.sku))

            except Exception as e:
                debug.debug(BRAND, 1, str(e))

    def update(self):
        products = Feed.objects.filter(brand=BRAND)

        for product in products:
            try:
                createdInDatabase = self.databaseManager.createProduct(
                    BRAND, product)
                if not createdInDatabase:
                    continue
            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            try:
                self.csr.execute(
                    "CALL AddToPendingUpdateProduct ({})".format(product.productId))
                self.con.commit()

                debug.debug(BRAND, 0, "Updated the product ProductID: {}, SKU: {}".format(
                    product.productId, product.sku))

            except Exception as e:
                debug.debug(BRAND, 1, str(e))

    def tag(self):
        self.databaseManager.updateTags(BRAND, False)

    def sample(self):
        self.databaseManager.sample(BRAND)

    def shipping(self):
        self.databaseManager.shipping(BRAND)

    def inventory(self, mpn):
        stockNote = ""
        try:
            product = Feed.objects.get(mpn=mpn)
            stockNote = product.stockNote
        except Exception as e:
            debug.debug(BRAND, 1, str(e))

        return {
            'stock': 5,
            'leadtime': stockNote
        }
