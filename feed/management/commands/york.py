from django.core.management.base import BaseCommand
from feed.models import York

import os
import environ
import pymysql
import requests
import json
from shutil import copyfile

from library import database, debug

API_BASE_URL = "http://yorkapi.yorkwall.com:10090/pcsiapi"

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "York"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "test" in options['functions']:
            processor = Processor()
            processor.test()

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)
            processor.databaseManager.validateFeed()

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
            products = York.objects.all()
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
            processor.image()

        if "image-ftp" in options['functions']:
            processor = Processor()
            processor.imageFTP()

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires()

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "whiteglove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "quick-ship" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="quickShip", tag="Quick Ship")


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=York)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def test(self):
        try:
            # Test Collection
            # reqProduct = requests.get(
            #     "{}/collections.php".format(API_BASE_URL))
            # resProduct = json.loads(reqProduct.text)
            # print(resProduct)

            # Test Product
            reqProduct = requests.get(
                "{}/product.php/{}".format(API_BASE_URL, "SW7430"))
            resProduct = json.loads(reqProduct.text)
            print(resProduct)

            # Test Inventory
            reqProduct = requests.get(
                "{}/stock.php/{}".format(API_BASE_URL, "SW7430"))
            resProduct = json.loads(reqProduct.text)
            print(resProduct)
        except Exception as e:
            debug.debug(BRAND, 1, str(e))
            return

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

                    manufacturer_map = {
                        "Ronald Redding": "Ronald Redding Designs",
                        "Ron Redding Designs": "Ronald Redding Designs",
                        "Roommates": "RoomMates",
                        "CatCoq": "RoomMates",
                        "Rose Lindo": "RoomMates",
                        "Waverly": "RoomMates",
                        "Jane Dixon": "RoomMates",
                        "Nikki Chu": "RoomMates",
                        "Rifle": "Rifle Paper Co.",
                        "Cary Lind Designs": "Carey Lind Designs",
                    }

                    manufacturer = manufacturer_map.get(
                        manufacturer, manufacturer)
                    manufacturer = f"{manufacturer} {type}"

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
                    if cost == 0:
                        continue

                    msrp = float(row['MSRP'])
                    try:
                        map = float(row['NewMap'])
                    except:
                        map = 0

                    # Tagging
                    tags = "{}, {}, {}, {}, {}".format(str(row['Substrate']), str(
                        row['Theme']), pattern, collection, description)
                    colors = color

                    if row['SKUStatus'] == "Active":
                        statusP = True
                        statusS = True
                    elif row['SKUStatus'] == "Retired":
                        statusP = False  # To Confirm with York team
                        statusS = False
                    else:
                        statusP = False
                        statusS = False

                    if row['QuickShip'] == 'Y':
                        quickShip = True
                    else:
                        quickShip = False

                    statusS = False  # BK: Disable all Brewster and York Samples 2/1/24

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
        fnames = os.listdir(f"{FILEDIR}/images/york/")
        for fname in fnames:
            try:
                if "_" in fname:
                    mpn = fname.split("_")[0]

                    try:
                        product = York.objects.get(mpn=mpn)
                    except York.DoesNotExist:
                        continue

                    productId = product.productId

                    idx = 2
                    if "RS2" in fname:
                        idx = 3

                    if productId != None and productId != "":
                        copyfile(f"{FILEDIR}/images/york/{fname}",
                                 f"{FILEDIR}/../../../images/roomset/{productId}_{idx}.jpg")
                else:
                    mpn = fname.split(".")[0]

                    try:
                        product = York.objects.get(mpn=mpn)
                    except York.DoesNotExist:
                        continue

                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(f"{FILEDIR}/images/york/{fname}",
                                 f"{FILEDIR}/../../../images/product/{productId}.jpg")

                os.remove(f"{FILEDIR}/images/york/{fname}")
            except:
                continue

    def imageFTP(self):
        con = self.con
        csr = con.cursor()
        csr.execute(
            f"SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = '{BRAND}'")

        hasImage = []
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        csr.close()

        dnames = self.databaseManager.browseSFTP(src=f"/york/")

        for dname in dnames:
            fnames = self.databaseManager.browseSFTP(src=f"/york/{dname}")
            for fname in fnames:

                if "_" in fname:
                    mpn = fname.split("_")[0]

                    try:
                        product = York.objects.get(mpn=mpn)
                    except York.DoesNotExist:
                        continue

                    if not product.productId or product.productId in hasImage:
                        continue

                    idx = 13

                    keyword_mapping = {
                        "Detail": 2,
                        "Detail2": 3,
                        "Detail3": 4,
                        "Detail4": 5,
                        "Room": 6,
                        "Room2": 7,
                        "Room3": 8,
                        "Room4": 9,
                        "Dims": 10,
                        "Peel": 11,
                        "Stick": 12,
                    }

                    for keyword, value in keyword_mapping.items():
                        if keyword in fname:
                            idx = value
                            break

                    self.databaseManager.downloadFileFromSFTP(
                        src=f"/york/{dname}/{fname}",
                        dst=f"{FILEDIR}/../../../images/roomset/{product.productId}_{idx}.jpg",
                        delete=False
                    )

                else:
                    mpn = fname.split(".")[0]

                    try:
                        product = York.objects.get(mpn=mpn)
                    except York.DoesNotExist:
                        continue

                    if not product.productId or product.productId in hasImage:
                        continue

                    self.databaseManager.downloadFileFromSFTP(
                        src=f"/york/{dname}/{fname}",
                        dst=f"{FILEDIR}/../../../images/product/{product.productId}.jpg",
                        delete=False
                    )

    def hires(self):
        con = self.con
        csr = con.cursor()
        csr.execute(
            f"SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 20 AND M.Brand = '{BRAND}'")

        hasImage = []
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        csr.close()

        dnames = self.databaseManager.browseSFTP(src=f"/york/")

        for dname in dnames:
            fnames = self.databaseManager.browseSFTP(src=f"/york/{dname}")
            for fname in fnames:
                if "_" not in fname:
                    mpn = fname.split(".")[0]

                    try:
                        product = York.objects.get(mpn=mpn)
                    except York.DoesNotExist:
                        continue

                    if not product.productId or product.productId in hasImage:
                        continue

                    self.databaseManager.downloadFileFromSFTP(
                        src=f"/york/{dname}/{fname}",
                        dst=f"{FILEDIR}/../../../images/hires/{product.productId}_20.jpg",
                        delete=False
                    )
