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
from shutil import copyfile

from library import database, debug, common

API_ADDRESS = 'http://scala-api.scalamandre.com/api'
API_USERNAME = 'Decoratorsbest'
API_PASSWORD = 'EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!'

env = environ.Env()

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Scalamandre"


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
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = Scalamandre.objects.filter(
                Q(type='Pillow') | Q(type='Throws'))
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
            processor.image(missingOnly=True)

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires()

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "pillow" in options['functions']:
            processor = Processor()
            processor.databaseManager.linkPillowSample()

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    products = processor.fetchFeed()
                    processor.databaseManager.writeFeed(products=products)
                    processor.databaseManager.statusSync(fullSync=False)
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
            con=self.con, brand=BRAND, Feed=Scalamandre)

        r = requests.post("{}/Auth/authenticate".format(API_ADDRESS), headers={'Content-Type': 'application/json'},
                          data=json.dumps({"Username": API_USERNAME, "Password": API_PASSWORD}))
        j = json.loads(r.text)
        self.token = j['Token']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Sale items
        onSaleMPNs = [
            "SC 0001RZEBRAPIL",
            "BI 0003FLURRPILL",
            "AL 0005BOHEPILL",
            "EA 0001LSIBERPIL",
            "A9 0007LLEOPILL",
            "SC 0001LZEBRAPIL",
            "BI 0004FLURRPILL",
            "SC 0001ZEBRAPILL",
            "SC 0005ZEBRAPILL",
            "SC 0003TIGRPILL",
            "AL 0001BOHEPILL",
            "AL 0001LBOHEPILL",
            "AL 0004BOHEPILL",
            "BI 0001FLURRPILL",
            "SC 0002ALLEPILL",
            "SC 0001KELMPILL",
            "SC 0002LTIGRPILL",
            "SC 0003ANKAPILL",
            "BI 0005FLURRPILL",
            "EA 0001SIBERPILL",
            "SC 0005PALAZPILL",
        ]

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
                sku = f"SCALA {row['SKU']}"
                pattern = common.formatText(
                    row['PATTERN_DESCRIPTION'].replace('PILLOW', ''))
                color = common.formatText(row['COLOR'])

                # Categorization
                brand = BRAND

                type = common.formatText(row['CATEGORY'])
                if "FABR" in type:
                    type = "Fabric"
                elif "WALL" in type:
                    type = "Wallpaper"
                elif "TRIM" in type:
                    type = "Trim"
                elif "PILL" in type:
                    type = "Pillow"
                else:
                    continue

                manufacturer = common.formatText(row['BRAND'])
                if "Scalamandre" in manufacturer or "Wallquest" in manufacturer or "Scalamandré" in manufacturer or 'THIRD FLOOR FABRIC' in manufacturer or 'WALLCOVERING' in manufacturer:
                    manufacturer = "Scalamandre"
                elif "Old World Weavers" in manufacturer:
                    sku = "OWW {}".format(row['SKU'])
                elif "Grey Watkins" in manufacturer:
                    sku = "GWA {}".format(row['SKU'])

                collection = common.formatText(
                    row.get('WEB COLLECTION NAME', ''))

                # Main Information
                description = common.formatText(row['DESIGN_INSPIRATION'])
                usage = common.formatText(row['WEARCODE']).title()
                width = common.formatFloat(row['WIDTH'])
                size = common.formatText(row['PIECE SIZE'])
                repeatV = common.formatFloat(row['PATTERN REPEAT LENGTH'])
                repeatH = common.formatFloat(row['PATTERN REPEAT WIDTH'])

                # Additional Information
                content = common.formatText(row.get('FIBER CONTENT', ''))
                features = [common.formatText(row.get('WEARCODE', ''))]
                yards = common.formatFloat(row['YARDS PER ROLL'])
                material = common.formatText(row.get('MATERIALTYPE', ''))

                # Measurement
                if row['MIN ORDER']:
                    minimum = common.formatInt(row['MIN ORDER'].split(' ')[0])
                else:
                    minimum = 0

                if common.formatInt(row['WEB SOLD BY']) > 1:
                    increment = ",".join(
                        [str(ii * common.formatInt(row['WEB SOLD BY'])) for ii in range(1, 25)])
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
                uom = UOM_DICT.get(row['UNITOFMEASURE'], '')

                # Pricing
                cost = common.formatFloat(row['NETPRICE'])
                if mpn in onSaleMPNs:
                    cost = round(cost * 0.75, 2)

                # Tagging
                tags = f"{collection}, {row.get('WEARCODE', '')}, {material}"

                # Stock
                if row.get('STOCKINVENTORY') != 'N':
                    stockP = common.formatInt(row.get('AVAILABLE'))
                else:
                    stockP = 0

                stockNote = common.formatText(row.get('LEAD TIME', ''))
                if not stockNote and type == "Pillow":
                    stockNote = "2-3 Weeks (Custom Order)"

                if type == "Pillow" and stockP == 0:
                    stockP = 5

                # Status
                statusP = True
                statusS = True

                if row.get('DISCONTINUED', False) != False:
                    statusP = False
                    statusS = False
                if row.get('WEBENABLED', '') not in ["Y", "S"]:
                    statusP = False
                    statusS = False
                if row.get('IMAGEVALID', False) != True:
                    statusP = False
                    statusS = False
                if manufacturer in ["Tassinari & Chatel", "Lelievre", "Nicolette Mayer", "Jean Paul Gaultier"]:
                    statusP = False
                    statusS = False

                manufacturer = f"{manufacturer} {type}"

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
                'material': material,

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
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self, missingOnly=True):
        con = self.con
        csr = con.cursor()
        csr.execute(
            f"SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = '{BRAND}'")

        hasImage = []
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        csr.close()

        products = Scalamandre.objects.all()
        for product in products:
            mpn = product.mpn
            productId = product.productId

            if missingOnly and productId in hasImage:
                continue

            thumbnail = ""
            roomsets = []

            try:
                r = requests.get(f"{API_ADDRESS}/ScalaFeedAPI/FetchImagesByItemID?ITEMID={mpn}",
                                 headers={'Authorization': 'Bearer {}'.format(self.token)})
                images = json.loads(r.text)

                for image in images:
                    if image["HIGHRESIMAGE"] or image["IMAGEPATH"]:
                        if image["IMAGETYPE"] == "MAIN":
                            thumbnail = image["HIGHRESIMAGE"] or image["IMAGEPATH"]
                        else:
                            roomsets.append(
                                image["HIGHRESIMAGE"] or image["IMAGEPATH"])

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            if productId and thumbnail:
                self.databaseManager.downloadImage(
                    productId=productId, thumbnail=thumbnail, roomsets=roomsets)

    def hires(self):
        fnames = os.listdir(f"{FILEDIR}/images/scalamandre/")
        for fname in fnames:
            if "_" in fname:
                prefix = fname.split("_")[0]
                number = fname.split("_")[1]

                if prefix == "SC":
                    mpn = f'SC {number}'
                elif prefix == "WSB":
                    mpn = f'WSB{number}'
                else:
                    mpn = f'{prefix}{number}'

                try:
                    product = Scalamandre.objects.get(mpn=mpn)

                    if product.productId:
                        copyfile(f"{FILEDIR}/images/scalamandre/{fname}",
                                 f"{FILEDIR}/../../../images/hires/{product.productId}_20.jpg")
                        debug.debug(
                            BRAND, 0, f"Copied {fname} to {product.productId}_20.jpg")

                    os.remove(f"{FILEDIR}/images/scalamandre/{fname}")
                except Scalamandre.DoesNotExist:
                    continue

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
