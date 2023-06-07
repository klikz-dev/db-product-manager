from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import Stout

import os
import environ
import pymysql
import xlrd
import requests
import json

from library import database, debug, common


SEARCH_API_URL = "https://www.estout.com/api/search.vbhtml"
SEARCH_API_KEY = "aeba0d7a-9518-4299-b06d-46ab828e3288"

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Stout"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            processor.databaseManager.downloadFileFromLink(
                "https://www.stouttextiles.com/downloads/Online_Retail_Items.xlsx", f"{FILEDIR}/stout-master.xlsx")
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = Stout.objects.filter(
                Q(type='Pillow') | Q(type='Throws'))
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=False)

        if "pillow" in options['functions']:
            processor.databaseManager.linkPillowSample()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Stout)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/stout-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 0))

                try:
                    debug.debug(BRAND, 0, f"Fetching data for {mpn}")

                    res = requests.post(SEARCH_API_URL, data={
                                        'id': mpn, 'key': SEARCH_API_KEY})
                    result = json.loads(res.content)
                    data = result["result"][0]
                except Exception as e:
                    debug.debug(BRAND, 1, f"Search API Error. {str(e)}")
                    continue

                sku = f"STOUT {mpn}"

                pattern = common.formatText(sh.cell_value(i, 1).split(" ")[0])
                color = common.formatText(sh.cell_value(i, 8))

                # Categorization
                usage = common.formatText(sh.cell_value(i, 14)).title()
                construction = common.formatText(sh.cell_value(i, 10))
                style = common.formatText(sh.cell_value(i, 11))

                if "Trimming" in usage or "Trimming" in construction or "Trimming" in style:
                    type = "Trim"
                elif "Wallcovering" in usage or "Wallcovering" in construction or "Wallcovering" in style:
                    type = "Wallpaper"
                else:
                    type = "Fabric"

                if pattern == "" or color == "" or type == "":
                    continue

                manufacturer = f"{BRAND} {type}"
                collection = common.formatText(sh.cell_value(i, 19))

                # Main Information
                width = common.formatFloat(sh.cell_value(i, 4))

                repeatV = common.formatFloat(sh.cell_value(i, 5))
                repeatH = common.formatFloat(sh.cell_value(i, 6))

                # Additional Information
                content = str(sh.cell_value(i, 7)).replace(
                    " ", ", ").replace("%", "% ").strip()

                finish = common.formatFloat(sh.cell_value(i, 13))
                country = common.formatFloat(sh.cell_value(i, 15))

                specs = []
                if sh.cell_value(i, 12):
                    specs.append(str(sh.cell_value(i, 12)))

                features = []
                if construction:
                    features.append(f"Construction: {construction}")

                # Pricing
                cost = common.formatFloat(data.get("price", "0"))
                if cost == 0:
                    cost = common.formatFloat(sh.cell_value(i, 2))

                map = common.formatFloat(data.get("map", "0"))

                msrp = common.formatFloat(sh.cell_value(i, 3))

                # Measurement
                uom = str(data.get("uom", "")).upper()
                if uom == "YARD":
                    uom = "Per Yard"
                elif uom == "ROLL":
                    uom = "Per Roll"
                elif uom == "EACH":
                    uom = "Per Item"
                else:
                    debug.debug(BRAND, 1, f"Unknown UOM {uom} for MPN {mpn}")
                    continue

                # Tagging
                tags = f"{construction}, {style}"

                # Image
                thumbnail = f"https://cdn.estout.com/Images/{mpn}.jpg"

                # Status
                phase = common.formatInt(data.get("phase", ""))
                if phase == 0 or phase == 1:
                    statusP = True
                    statusS = True
                elif phase == 2:
                    statusP = True
                    statusS = False
                else:
                    statusP = False
                    statusS = False

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'width': width,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'content': content,
                'finish': finish,
                'country': country,
                'specs': specs,
                'features': features,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'uom': uom,

                'tags': tags,
                'colors': color,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products
