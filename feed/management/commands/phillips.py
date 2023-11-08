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
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "white-glove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove", logic=True)

        if "quick-ship" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="quickShip", tag="Quick Ship")

        if "best-seller" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="bestSeller", tag="Best Selling")

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

        # BestSellers
        bestSellers = [
            "River Stone Coffee Table Roman Stone Large",
            "River Stone Coffee Table Roman Stone Small",
            "Outstretched Arms Sculpture Aluminum Large",
            "Flower Wall Art Medium White Metal",
            "Flower Wall Art Large White Metal",
            "Teak Slice Coffee Table Rectangle",
            "Teak Slice Coffee Table Square",
            "Cast Oil Drum Wall Discs Silver Leaf Set of 4",
            "Cast Root Framed Console Table Resin Silver Leaf LG",
            "Beau Cast Root Console Table Gel Coat White",
            "Teak Chunk Coffee Table Round",
            "Vine Wall Tile",
            "Horse Pipe Sculpture Rearing Stainless Steel",
            "Colossal Cast Stone Sculpture Single Hole Roman Stone",
            "Colossal Cast Stone Sculpture Double Hole Roman Stone",
            "Arc Console Table  Double Side",
            "Diving Wall Sculpture Aluminum Large",
            "Diving Sculpture Aluminum Large",
            "Cast Root Framed Console Table Resin Gold Leaf LG",
            "River Stone Coffee Table Gel Coat White Large",
            "Clouds Wall Art Bleached Finish",
            "Freeform Bench Roman Stone",
            "Square Root Console Table Silver Leaf",
            "Climbing Sculpture w/Rope Black/Silver Aluminum",
            "Dice Wall Art Chamcha Wood Natural",
            "Waterfall Console Table Natural",
            "Flower Wall Art Small White Metal",
            "Geometry Coffee Table",
            "River Stone Coffee Table Gold Leaf Small",
            "Log Coffee Table Roman Stone",
            "Teak Wood Console Table Iron Sheet Top",
            "Birch Leaf Wall Art Copper LG",
            "Crazy Cut Coffee Table",
            "Handstand Sculpture Aluminum Large",
            "Atlas Console Table Chamcha Wood Natural Metal",
            "Framed Slice Wall Tile Teak Wood Black Frame",
            "Agate Side Table Assorted",
            "Crazy Wire Lounging Male",
            "River Stone Coffee Table Gel Coat White Small",
            "River Stone Coffee Table Gel Coat Black Large",
            "Lloyd Sculpture Resin Bronze Finish",
            "Lottie Sculpture Bronze Finish Resin",
            "River Stone Coffee Table Gold Leaf Large",
            "Molten Wall Disc Large Silver Leaf",
            "Freeform Console Table Silver Leaf LG",
            "Birch Leaf Wall Art Copper XL",
            "Birch Leaf Wall Art Copper MD",
            "Mercury Mirror Black Gold Leaf",
            "Colossal Cast Stone Sculpture with Seat Roman Stone",
            "Lloyd Wall Sculpture Resin Silver Leaf",
            "Broken Egg Wall Art White and Gold Leaf Set of 4",
            "River Stone Coffee Table Gel Coat Black Small",
            "Molten Wall Disc Medium Silver Leaf",
            "Poppy Flower Wall Art Copper LG",
            "Cast Root Framed Console Table Resin Brown",
            "River Console Table Double Sided",
            "Geometry Console Table",
            "Seat Belt Dining Chair White/Off-White",
            "Molten Wall Disc Large Gold Leaf",
            "Manhattan Coffee Table Square with Glass",
            "Waterfall Bench Natural",
            "Atlas Console Table Chamcha Wood Gray Stone Finish Metal",
            "Convergence Mirror Resin Gold Leaf",
            "Lottie Wall Sculpture Resin Silver Leaf",
            "Cast Boulder Coffee Table Roman Stone LG",
            "River Stone Coffee Table Silver Leaf Small",
            "Sheep Sculpture Cream",
            "River Stone Coffee Table Bronze Large",
            "Shell Coffee Table w/Glass Ming SS Legs",
            "River Stone Coffee Table Charcoal Stone Large",
            "Entropy Chair",
            "River Stone Coffee Table Silver Leaf Large",
            "Split the Difference Coffee Table Char",
            "Broken Egg Wall Art Black and Gold Leaf Set of 4",
            "River Stone Coffee Table Polished Aluminum Large",
            "Bull Pipe Sculpture Stainless Steel",
            "Flower Wall Art Large Blue Metal",
            "Fashion Faces Wall Art Small White and Silver Leaf Set of 3",
            "Burled Coffee Table Black Metal Legs Large",
            "Iron Frame Bar Table Natural",
            "Vine Wall Flower",
            "Cast Boulder Coffee Table Roman Stone SM",
            "Concrete Bar Table Chamcha Wood Top",
            "Molten Wall Disc Medium Gold Leaf",
            "Atlas Desk Natural Waterfall Leg",
            "Waterfall Coffee Table",
            "Seat Belt Dining Chair Black/Black",
            "Lottie Wall Sculpture Resin Bronze Finish",
            "Horse Pipe Sculpture Walking Stainless Steel",
            "Horse Pipe Sculpture Galloping Stainless Steel",
            "Lloyd Wall Sculpture Resin Bronze Finish",
            "Chuleta Rings Wall Art Chamcha Wood Rectangular",
            "Trifoil Coffee Table Bronze w/ Glass",
            "River Stone Coffee Table Charcoal Stone Small",
            "Cast Root Coffee Table White Stone With Glass",
            "Burled Root Wall Art Large Silver Leaf",
            "Asken Wall Art Wood Freeform",
            "Round Wood Stool Assorted Styles",
            "Crazy Wire Lounging Female",
            "Concrete Bar Stool Chamcha Wood Top Stainless Steel Footrest",
            "Log Side Table Roman Stone",
            "Burled Bowl Resin Gold Leaf Finish",
            "Paint Can Wall Art Square Assorted Colors LG",
            "Fashion Faces Wall Art Small Black and Gold Leaf Set of 3",
            "See Speak Hear No Evil Wall Art Resin Bronze Set Of 3",
            "Teak Chunk Stool Round",
            "Poppy Flower Wall Art Silver/Black LG",
            "River Stone Coffee Table Liquid Gold Large",
            "Seat Belt Rocking Chair Gray/Black",
            "Lottie Sculpture Resin Liquid Silver",
            "Flower Wall Art Large Coral Metal",
            "Atlas River Wall Panel Natural",
            "Swirl Wall Tile Teak Wood Assorted",
            "River Stone Coffee Table Liquid Silver Small",
            "Seat Belt Rocking Chair Blue/Black",
            "Boscage Console Table Iron Frame",
            "Floating Coffee Table with Acrylic Legs Natural Assorted",
            "Noir Cast Root Coffee Table Black Gold Leaf",
            "Plateada Hollow Console Silver Leaf",
            "Lloyd Sculpture Resin Liquid Silver",
            "Flower Wall Art Medium Blue Metal",
            "Boulder Side Table",
            "Sheep Side Table Peach/Cream",
            "River Stone Coffee Table Liquid Silver Large",
            "Longhorn Bull Wall Art Resin Silver Leaf",
            "Hourglass Side Table",
            "Marley Bar Table Chamcha Wood Gray Stone Finish",
            "Honeycomb Wall Art LG",
            "Burled Root Wall Art Large Faux Bois Finish",
            "Negotiation Coffee Table Char",
            "Broken Egg Wall Art White and Silver Leaf Set of 4",
            "Wire Tree Wall Art Rectangular Metal Black",
            "Metal Lotus Wall Art Assorted Colors",
            "Waterfall Desk Gray Stone Acrylic Leg",
            "Freeform Bench Bronze",
            "Crazy Wire Lounging Female",
            "Cast Petrified Wood Stool Resin",
            "Cast Oil Drum Wall Discs Liquid Silver Set of 4",
            "Origins Dining Chair Natural",
            "Honey Drum People Wall Art",
            "Waterfall Desk Natural Satin Black Overlap Leg",
            "Broken Egg Coffee Table White and Gold Leaf",
            "Freeform Console Table Polished Bronze",
            "Geometry Side Table",
            "Seat Belt Dining Chair Silver Metallic",
            "River Stone Coffee Table Polished Aluminum Small",
            "Freeform Console Table Silver Leaf Extra Large",
            "Rhino Wall Art Resin Gold Leaf",
            "Flower Wall Art Large Ivory Metal",
            "Flower Wall Art Medium Coral Metal",
            "Old Lumber Dining Table Roman Stone",
            "Blocks Wall Art Chamcha Wood Natural LG",
            "Freeform Console Table Gel Coat White LG",
            "Square Root Console Table Resin Antique Bronze Finish",
            "Pebble Mirror Round",
            "Crazy Wire Retriever LG",
            "Freeform Console Table Faux Bois LG",
            "Crazy Cut Console Stainless Steel Silver",
            "Prism Stool Natural",
            "Log Side Table Gold Leaf",
            "Origins Freeform Desk Assorted",
            "Geometry Small Coffee Table",
            "River Stone Coffee Table Bronze Small",
            "Marley Bar Table Chamcha Wood Burnt Finish",
            "Shell Coffee Table Glass Top Ming Stainless Steel Legs",
            "Paint Can Wall Art Rectangle Assorted Colors",
            "Cast Root Framed Console Table Resin Silver Leaf SM",
            "Seat Belt Rocking Chair Black/Black",
            "Molten Side Table LG Poured Brass In Wood",
            "Cast Onyx Bowl Faux Finish Large",
            "Rock Pond Mirror Gold Leaf",
            "Chain Wall art Chamcha Wood Gray Stone Finish",
            "Lotus Wall Art Silver/Black LG",
            "Swoop Wall Art Black Wood Small",
            "Fashion Faces Wall Art Small White and Gold Leaf Set of 3",
            "Dog Side Table",
            "Teak Chunk Round Coffee Table Black",
            "Log Coffee Table Gold Leaf",
            "Flower Wall Art Medium Ivory Metal",
            "Cast Wall Onyx Bowl Faux Finish LG",
            "River Stone Coffee Table Liquid Gold Small",
            "Seat Belt Rocking Chair White",
            "Blue Marlin Fish Wall Sculpture Resin Silver Leaf",
            "Log Stool Roman Stone LG",
            "Square Root Wall Art Silver Leaf LG",
            "Boscage Coffee Table on Black Metal Legs Round",
            "Rock Pond Mirror Gold Leaf",
            "Seat Belt Dining Chair Gray/Black",
            "Lloyd Sculpture Resin Gel Coat White",
            "Freeform Wall Tile Gray Stone Assorted",
            "Lottie Sculpture Resin Silver Leaf",
            "River Mirror Natural",
            "Mercury Mirror Silver Leaf",
            "Lloyd Sculpture Resin Silver Leaf",
            "Seat Belt Rocking Chair Orange",
            "Seat Belt Dining Chair Beige/Beige",
            "Floating Console Table Acrylic Legs",
            "Log Coffee Table Bronze",
            "Iron Frame Counter Stool Natural",
            "Seat Belt Dining Chair High Back White/Off-White",
            "Sweep Side Table",
            "Reclaimed Oil Drum Wall Disc Individual Pieces Assorted Colors and Depths",
            "Burled Root Wall Art Large Black and Gold Leaf",
            "Freeform Console Table Bronze Extra Large",
            "Side Table Black Wash Round",
            "Marley Bar Stool Burnt Stainless Steel Foot Rest",
            "Cast Petrified Wood Stool Resin",
            "Lottie Sculpture Resin Gel Coat White",
            "Molten Wall Disc Small Silver Leaf",
            "Freeform Console Table Faux Bois SM",
            "Seat Belt Dining Chair Orange",
            "Triangle Bench",
            "Seat Belt Dining Chair Gold Metallic",
            "Waterfall Desk Silver Leaf",
            "Freeform Console Table Gel Coat White Extra Large",
            "Clover Coffee Table Chamcha Wood Gray Stone Finish Metal Base",
            "Lotus Wall Art Silver/Black MD",
            "Fashion Faces Wall Art Large Pout Black and Gold Leaf",
            "Cast Wall Onyx Bowl Faux Finish SM",
            "Tall Chiseled Female Sculpture Resin Silver Leaf",
            "Stacked Wall Ring Bleached MD",
            "Sable Cast Root Console Table Silver Leaf",
            "Honeycomb Wall Art MD",
            "Freeform Console Table Silver Leaf",
            "Flower Wall Art Large Black Metal",
            "Cast Root Framed Console Table Resin Gold Leaf SM",
            "Lathe Side Table Chamcha Wood",
            "Agate Console Table Stainless Steel Base",
            "Ripple Coffee Table Black/Silver Aluminum",
            "Crown Console Table Silver Leaf",
            "Venice Freeform Console Bronze",
            "Black Iron Bar Stool Swivel Seat Natural",
            "See Hear Speak No Evil Silver Leaf Set Of 3",
            "Score Coffee Table Chamcha Wood Iron Base",
            "Criss Cross Coffee Table on Black Iron Legs Chamcha Wood",
            "Enchanting Buddha Roman Stone",
            "Amorphous Planter Large White",
            "Check Mate Sculpture Black",
            "Split Slab Mirror",
            "Iron Frame Bar Stool Natural",
            "Atlas Coffee Table Chamcha Wood Gray Stone Finish Metal",
            "Flower Wall Art Medium Dandelion Metal",
            "Flower Wall Art Medium Black Metal",
            "Atlas Coffee Table Chamcha Wood Natural Metal",
            "Score Console Table Chamcha Wood Iron Base",
            "Cast Sonokeling Floor Sculpture  Faux Bois",
            "Cast Petrified Wood Stool Resin",
            "Frozen Dining Chair Vintage Gray Taupe",
            "Great Dane Bronze Right",
            "Teak Slice Pedestal Square LG",
            "Blue Glass Bowl MD",
            "Paint Can Wall Art Square Assorted Colors SM",
            "Flower Wall Art Large Dandelion Metal",
            "Atlas Side Table Chamcha Wood Gray Stone Finish Metal",
            "Feathers Wall Art Large Silver Leaf Set of 2",
            "Molten Wall Tile Poured Aluminum In Wood",
            "Square Root Cast Coffee Table With Glass",
            "Stacked Wood Floor Sculptures Bleached Set of 3",
            "Geode Texture Panel Black and Gold Wall Decor",
            "Vested Female Sculpture Large Chamcha Natural White Gold",
            "Freeform Bench Silver Leaf",
            "Flower Wall Art Small Coral Metal",
            "Molten Wall Disc Small Gold Leaf",
            "Asken Wall Art Wood LG",
            "Beau Cast Root Console Table Bronze",
            "Molten Coffee Table Poured Brass In Wood",
            "Seat Belt Rocking Chair Red",
            "Bicycle Wheel Wall Art Assorted",
            "Stump Stool Natural Assorted",
            "Post Set of 3 Metal Base Burnt",
            "Fashion Faces Wall Art Large Smile Black and Gold Leaf",
            "Freeform Wall Tile Natural Assorted",
            "Log Side Table Bronze",
            "Rock Pond Mirror Silver Leaf",
            "Elephant Wall Art Resin Silver Leaf",
            "Ginkgo Leaf Wall Art 9 Leaves Silver",
            "Orchid Sprig Wall Art Medium Metal White",
            "Molten Side Table SM Poured Brass In Wood",
            "Cast Petrified Wood Stool Resin",
            "Cairn Wall Tile Silver",
            "Crazy Cut Club Chair",
            "Triangle Bench Gray Stone",
            "Cast Onyx Bowl Faux Finish Small",
            "Molten Wall Tile Poured Brass In Wood",
            "Black Wood Abstract Sculpture Assorted with Natural Characteristics",
            "River Stone Side Table Bronze",
            "Root Wall Art Large Silver Leaf",
            "Chuleta Rings Wall Art Chamcha Wood Square LG",
            "Floating Console Table Gray Stone Finish Acrylic Legs",
            "Fashion Faces Wall Art Large Pout White and Silver Leaf",
            "Flower Wall Art Small Blue Metal",
            "Pebble End Table",
            "Great Dane Bronze Left",
            "Asterisk Cast Root Coffee Table Silver Leaf",
            "Cast Petrified Wood Stool Resin",
            "Spanish Fighting Bull Wall Art Resin Silver Leaf",
            "Ball on the Wall Medium Polished Aluminum Finish",
            "Life Size Cow Grazing Off White",
            "Slice Stool Round White Stone"
        ]

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

                        specs = [
                            ("Weight", f"{row['description']['weight']} lbs"),
                        ]

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
                        if row['status'] == "ACTIVE":
                            statusP = True
                        else:
                            statusP = False

                        statusS = False

                        if f"{pattern} {color}" in bestSellers:
                            bestSeller = True
                        else:
                            bestSeller = False

                        # Shipping
                        packWidth = row['description']['packw']
                        packHeight = row['description']['packl']
                        packDepth = row['description']['packh']
                        packWeight = row['description']['packwght']

                        if packWidth > 107 or packHeight > 107 or packDepth > 107 or packWeight > 40:
                            whiteGlove = True
                        else:
                            whiteGlove = False

                        if row['settings']['stocking'] == True and row['qtyavailable'] > 0:
                            quickShip = True
                        else:
                            quickShip = False

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
                        'specs': specs,

                        'material': material,
                        'finish': finish,
                        'care': care,
                        'disclaimer': disclaimer,
                        'country': country,
                        'weight': packWeight,

                        'uom': uom,
                        'minimum': minimum,

                        'tags': tags,
                        'colors': colors,

                        'cost': cost,
                        'msrp': msrp,
                        'map': map,

                        'statusP': statusP,
                        'statusS': statusS,
                        'whiteGlove': whiteGlove,
                        'quickShip': quickShip,
                        'bestSeller': bestSeller,

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
