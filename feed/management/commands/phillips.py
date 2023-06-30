from django.core.management.base import BaseCommand
from feed.models import Phillips

import environ
import requests
import json
import pymysql
import time

from library import database, debug, common


API_BASE_URL = "https://step-up-production.ue.r.appspot.com/v1"
API_KEY = "57d18c3398da46c9b19d8a5d86498765"
API_USERNAME = "orders@decoratorsbest.com"
API_PASSWORD = "m8q97J%7$MfC"

BRAND = "Phillips"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=False)

        if "update" in options['functions']:
            processor = Processor()
            products = Phillips.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=False)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(key="statusS", tag="NoSample")

        if "order" in options['functions']:
            processor = Processor()
            processor.order()

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    products = processor.fetchFeed()
                    processor.databaseManager.writeFeed(products=products)
                    processor.databaseManager.statusSync(fullSync=False)
                    processor.databaseManager.updatePrices(formatPrice=False)

                    print("Finished process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(60 * 60 * 24 * 7)


class Processor:
    def __init__(self):
        response = requests.request(
            "POST",
            "{}{}".format(API_BASE_URL, "/auth"),
            headers={
                'Content-type': 'application/json',
                'x-api-key': API_KEY
            },
            data=json.dumps({
                "email": API_USERNAME,
                "password": API_PASSWORD
            })
        )
        data = json.loads(response.text)
        self.token = data['data']['token']

        self.env = environ.Env()

        self.con = pymysql.connect(host=self.env('MYSQL_HOST'), user=self.env('MYSQL_USER'), passwd=self.env(
            'MYSQL_PASSWORD'), db=self.env('MYSQL_DATABASE'), connect_timeout=5)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Phillips)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Get Product Types
        types = {}
        response = requests.request(
            "GET",
            "https://step-up-production.ue.r.appspot.com/v1/items-categories",
            headers={
                'x-api-key': API_KEY,
                'Authorization': "Bearer {}".format(self.token)
            }
        )
        data = json.loads(response.text)
        for type in data['data']:
            types[type['_id']] = type['name']

        # Get Product Collections
        collections = {}
        response = requests.request(
            "GET",
            "https://step-up-production.ue.r.appspot.com/v1/items-collections",
            headers={
                'x-api-key': API_KEY,
                'Authorization': "Bearer {}".format(self.token)
            }
        )
        data = json.loads(response.text)
        for collection in data['data']:
            collections[collection['_id']] = collection['name']

        # Get Product Feed
        products = []
        page = 1
        while True:
            response = requests.request(
                "GET",
                "{}{}?page={}&page_size=100".format(
                    API_BASE_URL, "/ecomm/items", page),
                headers={
                    'x-api-key': API_KEY,
                    'Authorization': "Bearer {}".format(self.token)
                }
            )
            data = json.loads(response.text)

            if len(data['data']) > 0:
                for row in data['data']:
                    try:
                        # Primary Keys
                        mpn = row['_id']
                        sku = "PC {}".format(mpn)
                        upc = row['upc']
                        pattern = row['desc']
                        color = str(row['descspec']).replace(",", "")
                        if color == "":
                            color = row['description']['color'][0]
                        title = " ".join((pattern, color))

                        # Categorization
                        brand = BRAND

                        typeText = types.get(row['class']['category'], "")
                        if typeText == "" or typeText == "Abstract" or typeText == "Animals":
                            type = "Decor"
                        elif typeText == "Pedestals" or typeText == "Seating" or typeText == "Figures" or typeText == "Framed":
                            type = "Accents"
                        elif typeText == "Bowls / Vessels":
                            type = "Bowls"
                        elif typeText == "Consoles / Sofa Tables":
                            type = "Consoles"
                        elif typeText == "Dining Tables":
                            type = "Dining Chairs"
                        elif typeText == "Hanging Lamps":
                            type = "Accent Lamps"
                        else:
                            type = typeText

                        manufacturer = BRAND

                        if len(row['class']['collection']) > 0:
                            collection = collections.get(
                                row['class']['collection'][0], "")
                        else:
                            collection = ""

                        # Main Information
                        description = row['description']['story']
                        width = row['description']['sizew']
                        height = row['description']['sizel']
                        depth = row['description']['sizeh']
                        weight = row['description']['weight']

                        # Additional Information
                        material = ", ".join(row['description']['material'])
                        addmat = ", ".join(row['description']['addmat'])
                        material = "{}, {}".format(material, addmat)
                        finish = ", ".join(row['description']['finish'])
                        care = row['description']['care']
                        disclaimer = row['description']['disclaimer']
                        country = row.get('countryoforigin', "")

                        # Measurement
                        uom = row['price']['uom']
                        if uom == "each":
                            uom = "Per Item"
                        minimum = row['price']['factor']

                        # Tagging
                        tags = ", ".join((typeText, ", ".join(row['tags'])))
                        colors = ", ".join(row['description']['color'])

                        # Pricing
                        if row['price']['pricelist'] == "BASE":
                            cost = row['price']['price']
                        else:
                            debug(BRAND, 1,
                                  "Price Error for MPN: {}".format(mpn))
                            continue
                        msrp = row['msrp']
                        map = row['map']

                        # Availability
                        statusP = False
                        if row['status'] == "ACTIVE":
                            statusP = True

                        # Assets
                        thumbnail = row['assets']['images']['main']
                        roomsets = []
                        for roomset in row['assets']['images']['details']:
                            roomsets.append(roomset['url'])
                        for roomset in row['assets']['images']['lifestyle']:
                            roomsets.append(roomset['url'])
                    except Exception as e:
                        debug.debug(BRAND, 1, str(e))
                        continue

                    product = {
                        'mpn': mpn,
                        'sku': sku,
                        'upc': upc,
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
                        'weight': weight,

                        'material': material,
                        'finish': finish,
                        'care': care,
                        'disclaimer': disclaimer,
                        'country': country,

                        'uom': uom,
                        'minimum': minimum,

                        'tags': tags,
                        'colors': colors,

                        'cost': cost,
                        'msrp': msrp,
                        'map': map,

                        'statusP': statusP,

                        'thumbnail': thumbnail,
                        'roomsets': roomsets,
                    }
                    products.append(product)

                page += 1
            else:
                break

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self, productId, thumbnail, roomsets):
        if thumbnail and thumbnail.strip() != "":
            try:
                common.picdownload2(thumbnail, "{}.jpg".format(productId))
            except Exception as e:
                debug.debug(BRAND, 1, str(e))

        if len(roomsets) > 0:
            idx = 2
            for roomset in roomsets:
                try:
                    common.roomdownload(
                        roomset, "{}_{}.jpg".format(productId, idx))
                    idx = idx + 1
                except Exception as e:
                    debug.debug(BRAND, 1, str(e))

    def order(self):
        orders = self.databaseManager.getOrders()

        lastPO = -1
        for order in orders:
            try:
                items = []
                for item in order['items']:
                    items.append({
                        'itemno': item['mpn'],
                        'qtyorder': item['quantity']
                    })

                body = {
                    'reference': f"PO #{order['po']}",
                    'shipto': {
                        'shipname': order['name'],
                        'address': " ".join((order['address1'], order['address2'])),
                        'city': order['city'],
                        'state': order['state'],
                        'zip': order['zip'],
                        'country': "USA",
                        'phone': order['phone'],
                        'fax': '',
                        'email': '',
                    },
                    'shipcontact': {
                        'name': "DecoratorsBest Orders Department",
                        'email': 'purchasing@decoratorsbest.com',
                        'phone': ''
                    },
                    'items': items
                }

                response = requests.request(
                    "POST",
                    "{}{}".format(API_BASE_URL, "/ecomm/orders"),
                    headers={
                        'x-api-key': API_KEY,
                        'Authorization': "Bearer {}".format(self.token)
                    },
                    data=json.dumps(body)
                )

                data = json.loads(response.text)

                ref = data['data']['_id']

                if ref:
                    self.databaseManager.updateEDIOrderStatus(order['po'])
                    self.databaseManager.updateRefNumber(order['po'], ref)
                    lastPO = order['po']

                    debug.debug(
                        BRAND, 0, f"Successfully processed order {order['po']}. Got ref: {ref}")
                else:
                    debug.debug(BRAND, 2, f"Failed to submit PO {order['po']}")
                    break
            except Exception as e:
                debug.debug(BRAND, 2, str(e))
                break

        print(lastPO)

        if lastPO != -1:
            self.databaseManager.updatePORecord(lastPO)
