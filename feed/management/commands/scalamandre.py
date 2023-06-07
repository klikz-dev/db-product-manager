from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import Scalamandre

import os
import environ
import pymysql
import requests
import time
import json
import environ

from library import database, debug

API_ADDRESS = 'http://scala-api.scalamandre.com/api'
API_USERNAME = 'Decoratorsbest'
API_PASSWORD = 'EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!'

env = environ.Env()
SHOPIFY_API_URL = "https://decoratorsbest.myshopify.com/admin/api/{}".format(
    env('shopify_api_version'))
SHOPIFY_PRODUCT_API_HEADER = {
    'X-Shopify-Access-Token': env('shopify_product_token'),
    'Content-Type': 'application/json'
}

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Scalamandre"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

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
            products = Scalamandre.objects.filter(
                Q(type='Pillow') | Q(type='Throws'))
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)

        if "sample" in options['functions']:
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "inventory" in options['functions']:
            processor.inventory()

        if "pillow" in options['functions']:
            processor.databaseManager.linkPillowSample()

        if "main" in options['functions']:
            while True:
                try:
                    products = processor.fetchFeed()
                    processor.databaseManager.writeFeed(products=products)
                    processor.databaseManager.statusSync(fullSync=False)

                    processor.inventory()
                    print("Finished process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(86400)

                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    print("Failed process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(3600)


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Scalamandre)

        r = requests.post("{}/Auth/authenticate".format(API_ADDRESS), headers={'Content-Type': 'application/json'},
                          data=json.dumps({"Username": API_USERNAME, "Password": API_PASSWORD}))
        j = json.loads(r.text)
        self.token = j['Token']

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Get Product Feed
        products = []

        try:
            r = requests.get("{}/ScalaFeedAPI/FetchProductsFeed".format(API_ADDRESS),
                             headers={'Authorization': 'Bearer {}'.format(self.token)})
            j = json.loads(r.text)
            rows = j['FEEDPRODUCTS']

        except Exception as e:
            debug.debug(BRAND, 1, str(e))
            return

        for row in rows:
            try:
                # Primary Keys
                mpn = row['ITEMID']
                sku = "SCALA {}".format(row['SKU'])
                pattern = str(row['PATTERN_DESCRIPTION']).replace(
                    "PILLOW", "").strip().title()
                color = str(row['COLOR']).strip().title()

                # Categorization
                brand = BRAND

                type = row['CATEGORY']
                if "FABR" in type:
                    type = "Fabric"
                elif "WALL" in type:
                    type = "Wallpaper"
                elif "TRIM" in type:
                    type = "Trim"
                elif "PILL" in type:
                    type = "Pillow"
                else:
                    debug.debug(BRAND, 1, f"Unknown product type: {type}")
                    continue

                manufacturer = str(row['BRAND']).strip()
                if "Scalamandre" in manufacturer or "Wallquest" in manufacturer or "Scalamandré" in manufacturer:
                    manufacturer = "Scalamandre"
                elif "Old World Weavers" in manufacturer:
                    sku = "OWW {}".format(row['SKU'])
                elif "Grey Watkins" in manufacturer:
                    sku = "GWA {}".format(row['SKU'])

                manufacturer = f"{manufacturer} {type}"

                collection = str(row.get('WEB COLLECTION NAME', '')).strip()

                # Main Information
                description = str(row['DESIGN_INSPIRATION']).strip()
                usage = str(row['WEARCODE']).title()

                try:
                    width = round(float(row['WIDTH']), 2)
                except:
                    width = 0
                try:
                    size = row['PIECE SIZE']
                except:
                    size = ""
                try:
                    repeatV = round(float(row['PATTERN REPEAT LENGTH']), 2)
                except:
                    repeatV = 0
                try:
                    repeatH = round(float(row['PATTERN REPEAT WIDTH']), 2)
                except:
                    repeatH = 0

                # Additional Information
                content = str(row.get('FIBER CONTENT', "")).strip()
                features = [str(row.get('WEARCODE', "")).strip()]
                try:
                    yards = round(float(row['YARDS PER ROLL']), 2)
                except:
                    yards = 0

                # Measurement
                try:
                    minimum = int(float(row['MIN ORDER'].split(' ')[0])) if isinstance(
                        row['MIN ORDER'], str) and ' ' in row['MIN ORDER'] else 0
                except:
                    minimum = 0

                if str(row['WEB SOLD BY']).isdigit() and int(float(row['WEB SOLD BY'])) > 1:
                    increment = ",".join(
                        [str(ii * int(float(row['WEB SOLD BY']))) for ii in range(1, 25)])
                else:
                    increment = ""

                UOM_DICT = {
                    "RL": "Per Roll",
                    "DR": "Per Roll",
                    "YD": "Per Yard",
                    "LY": "Per Yard",
                    "EA": "Per Item",
                    "PC": "Per Item",
                    "SF": "Per Square Foot",
                    "ST": "Per Set",
                    "PN": "Per Panel",
                    "TL": "Per Tile"
                }
                uom = UOM_DICT.get(row['UNITOFMEASURE'], None)
                if uom is None:
                    debug.debug(BRAND, 1, f"UOM Error. MPN: {mpn}")
                    continue

                # Pricing
                try:
                    cost = round(float(row['NETPRICE']), 2)
                except:
                    debug.debug(BRAND, 1, "Produt Cost error {}".format(mpn))
                    continue

                # Tagging
                tags = "{}, {}, {}".format(collection, row.get(
                    'WEARCODE', ""), row.get('MATERIALTYPE', ""))

                # Image
                thumbnail = str(row.get('IMAGEPATH', "")).strip()

                # Stock
                if row.get('STOCKINVENTORY') != 'N':
                    available_stock = row.get('AVAILABLE')
                    if available_stock and str(available_stock).isdigit():
                        stockP = int(float(available_stock))
                    else:
                        stockP = 0
                else:
                    stockP = 0

                stockNote = row.get('LEAD TIME', "")
                if type == "Pillow":
                    stockNote = "2-3 Weeks (Custom Order)"

                # Status
                statusP = True
                if row.get('DISCONTINUED', False) != False:
                    statusP = False
                if row.get('WEBENABLED', '') not in ["Y", "S"]:
                    statusP = False
                if row.get('IMAGEVALID', False) != True:
                    statusP = False
                if str(row['BRAND']).strip() in ["Tassinari & Chatel", "Lelievre", "Nicolette Mayer", "Jean Paul Gaultier"]:
                    statusP = False

                statusS = False
                if row['SAMPLE_STATUS'] == 1:
                    statusS = True

                # Disable all samples
                statusS = False

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
                'collection': collection,

                'description': description,
                'usage': usage,
                'width': width,
                'size': size,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'content': content,
                'features': features,
                'yards': yards,

                'minimum': minimum,
                'increment': increment,
                'uom': uom,

                'tags': tags,
                'colors': color,

                'cost': cost,

                'statusP': statusP,
                'statusS': statusS,

                'stockP': stockP,
                'stockNote': stockNote,

                'thumbnail': thumbnail,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        products = Scalamandre.objects.all()
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': product.stockP,
                'note': product.stockNote or ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
