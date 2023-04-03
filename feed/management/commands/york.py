from django.core.management.base import BaseCommand
from feed.models import Feed

import os
import environ
import pymysql
import requests
import json
from shutil import copyfile

from library import database, debug

API_BASE_URL = "http://yorkapi.yorkwall.com:10090/pcsiapi"

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "York"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()
        if "test" in options['functions']:
            processor.test()

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

    def test(self):
        try:
            reqCollections = requests.get(
                "{}/collections.php".format(API_BASE_URL))
            resCollections = json.loads(reqCollections.text)
            collections = resCollections['results']
        except Exception as e:
            debug.debug(BRAND, 1, str(e))
            return

        print(collections)

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        try:
            reqCollections = requests.get(
                "{}/collections.php".format(API_BASE_URL))
            resCollections = json.loads(reqCollections.text)
            collections = resCollections['results']
        except Exception as e:
            debug.debug(BRAND, 1, str(e))
            return

        # Get Product Feed
        products = []

        for collection in collections:
            collectionID = collection['collectionID']
            collectionName = collection['name']

            if collectionID == "":
                continue

            debug.debug(
                BRAND, 0, "Processing Collection {}".format(collectionID))

            reqCollection = requests.get(
                "{}/collection.php/{}".format(API_BASE_URL, collectionID))
            resCollection = json.loads(reqCollection.text)

            for product in resCollection['results']:
                productID = product['productID']
                productName = product['description']

                debug.debug("York", 0, "Processing Product ID: {}, Name: {}".format(
                    productID, productName))

                try:
                    reqProduct = requests.get(
                        "{}/product.php/{}".format(API_BASE_URL, productID))
                    resProduct = json.loads(reqProduct.text)
                    row = resProduct['results'][0]
                except Exception as e:
                    print(e)
                    debug.debug("York", 1, "Error ID: {}, Name: {}".format(
                        productID, productName))
                    continue

                try:
                    # Primary Keys
                    try:
                        mpn = int(row['VendorItem#'])
                    except:
                        mpn = str(row['VendorItem#'])
                    sku = "YORK {}".format(mpn)

                    pattern = str(row['ProductName']).replace(
                        "Wallpaper", "").replace("  ", "").replace("\"", "").strip().title()
                    color = str(row['Color']).replace(
                        ", ", "/").replace("\"", "").strip().title()
                    if pattern == "" or color == "":
                        continue

                    # Categorization
                    brand = BRAND
                    type = "Wallpaper"

                    manufacturer = str(row['CategoryName']).strip()
                    collectionName = str(row['CollectionName']).strip()

                    if manufacturer == "Ron Redding Designs":
                        manufacturer = "Ronald Redding Designs"
                    if manufacturer == "Inspired by Color":
                        manufacturer = "York"
                    if manufacturer == "Florance Broadhurst":
                        manufacturer = "Florence Broadhurst"
                    if manufacturer == "York Style Makers":
                        manufacturer = "York Stylemakers"
                    if manufacturer == "YorkPa":
                        manufacturer = "York"
                    if manufacturer == "Cary Lind Designs":
                        manufacturer = "Carey Lind Designs"
                    if manufacturer == "York Designers Series":
                        manufacturer = "York Designer Series"
                    if "RoomMates" in collectionName:
                        manufacturer = "RoomMates"
                    if "Rifle Paper Co." in collectionName:  # 11/29 request from Barbara. Set Rifle collection to manufacturer
                        manufacturer = "Rifle Paper Co."
                    # 4/6/22 from Barbara. Set Dazzling Dimensions and Bohemian Luxe collections to Antonina Vella Brand
                    if "Dazzling Dimensions" in collectionName or "Bohemian Luxe" in collectionName:
                        manufacturer = "Antonina Vella"

                    manufacturer = "{} {}".format(manufacturer, type)

                    # Main Information
                    if str(row['AdvertisingCopyIII']) != "":
                        description = str(row['AdvertisingCopyIII'])
                    else:
                        description = str(row['AdvertisingCopy'])
                    description = description.replace('"', '')

                    usage = "Wallcovering"

                    # Additional Information
                    dimension = ""
                    if str(row['ProductDimension']) != "" and str(row['ProductDimension']) != "None":
                        dimension += str(row['ProductDimension'])
                    if str(row['ProductDimensionMetric']) != "" and str(row['ProductDimensionMetric']) != "None":
                        dimension += " / " + str(row['ProductDimensionMetric'])

                    repeat = ""
                    if str(row['PatternRepeat']) != "" and str(row['PatternRepeat']) != "None":
                        repeat += str(row['PatternRepeat'])
                    if str(row['PatternRepeatCM']) != "" and str(row['PatternRepeatCM']) != "None":
                        repeat += " / " + str(row['PatternRepeatCM'])

                    match = str(row['Match'])

                    features = [str(row['KeyFeatures'])]

                    # Measurement
                    uom = str(row['UOM'])
                    if "YARD" in uom:
                        uom = "Per Yard"
                    elif "EACH" in uom:
                        uom = "Per Each"
                    elif "SPOOL" in uom:
                        uom = "Per Spool"
                    elif "ROLL" in uom:
                        uom = "Per Roll"
                    else:
                        debug.debug(
                            "York", 1, "UOM error for MPN: {}".format(mpn))
                        continue

                    try:
                        minimum = int(row['OrderIncrement'])
                    except:
                        minimum = 2

                    increment = ""
                    if minimum > 1:
                        increment = ",".join([str(ii * minimum)
                                              for ii in range(1, 26)])

                    # Pricing
                    cost = float(row['DECBESTPRICE'])
                    msrp = float(row['MSRP'])
                    try:
                        map = float(row['NewMap'])
                    except:
                        map = 0

                    # Tagging
                    tags = "{}, {}, {}, {}, {}".format(str(row['Substrate']), str(
                        row['Theme']), pattern, collection, description)
                    colors = color

                    statusP = True
                    statusS = True
                    quickShip = False
                    if row['QuickShip'] == 'Y':
                        quickShip = True

                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    continue

                product = {
                    'mpn': mpn,
                    'sku': sku,
                    'pattern': pattern,
                    'color': color,

                    'brand': brand,
                    'type': type,
                    'manufacturer': manufacturer,
                    'collection': collectionName,

                    'description': description,
                    'usage': usage,

                    'dimension': dimension,
                    'repeat': repeat,
                    'match': match,
                    'features': features,

                    'uom': uom,
                    'minimum': minimum,
                    'increment': increment,

                    'tags': tags,
                    'colors': colors,

                    'cost': cost,
                    'map': map,
                    'msrp': msrp,

                    'statusP': statusP,
                    'statusS': statusS,
                    'quickShip': quickShip,
                }
                products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        fnames = os.listdir(FILEDIR + "/files/images/york/")
        for fname in fnames:
            try:
                if "_" in fname:
                    mpn = fname.split("_")[0]

                    try:
                        product = Feed.objects.get(mpn=mpn)
                    except Feed.DoesNotExist:
                        continue

                    productId = product.productId

                    idx = 2
                    if "RS2" in fname:
                        idx = 3

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "images/york/" + fname, FILEDIR +
                                 "/../../../images/roomset/{}_{}.jpg".format(productId, idx))
                else:
                    mpn = fname.split(".")[0]

                    try:
                        product = Feed.objects.get(mpn=mpn)
                    except Feed.DoesNotExist:
                        continue

                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "images/york/" + fname, FILEDIR +
                                 "/../../../images/product/{}.jpg".format(productId))

                os.remove(FILEDIR + "images/york/" + fname)
            except:
                continue

    def feed(self):
        products = self.fetchFeed()
        self.databaseManager.writeFeed(BRAND, products)

    def sync(self):
        self.databaseManager.statusSync(BRAND)

    def add(self):
        self.databaseManager.createProducts(BRAND)

    def update(self):
        self.databaseManager.updateProducts(BRAND)

    def white(self):
        self.databaseManager.whiteShip(BRAND, False)

    def quick(self):
        self.databaseManager.quickShip(BRAND, False)
