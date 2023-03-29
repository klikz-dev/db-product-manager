from library import debug
from brands.models import Feed
from mysql.models import Type


class DatabaseManager:
    def __init__(self, con):
        self.con = con
        self.csr = self.con.cursor()
        self.log = debug.debug

    def writeFeed(self, brand, products: list):
        self.log("DatabaseManager", 0,
                 "Started writing {} feeds to our database".format(brand))

        Feed.objects.filter(brand=brand).delete()

        total = len(products)
        success = 0
        failed = 0
        for product in products:
            try:
                feed = Feed.objects.create(
                    mpn=product.get('mpn'),
                    sku=product.get('sku'),
                    upc=product.get('upc', ""),
                    pattern=product.get('pattern'),
                    color=product.get('color'),
                    brand=product.get('brand'),
                    type=product.get('type'),
                    manufacturer=product.get('manufacturer'),
                    collection=product.get('collection', ""),
                    description=product.get('description', ""),
                    usage=product.get('usage', ""),
                    disclaimer=product.get('disclaimer', ""),
                    width=product.get('width', 0),
                    length=product.get('length', 0),
                    height=product.get('height', 0),
                    size=product.get('size', ""),
                    dimension=product.get('dimension', ""),
                    repeatH=product.get('repeatH', 0),
                    repeatV=product.get('repeatV', 0),
                    repeat=product.get('repeat', ""),
                    material=product.get('material', ""),
                    finish=product.get('finish', ""),
                    care=product.get('care', ""),
                    specs=product.get('specs', []),
                    features=product.get('features', []),
                    weight=product.get('weight', 5),
                    country=product.get('country', ""),
                    uom=product.get('uom'),
                    minimum=product.get('minimum', 1),
                    increment=product.get('increment', ""),
                    tags=product.get('tags', ""),
                    colors=product.get('colors', ""),
                    cost=product.get('cost'),
                    msrp=product.get('msrp', 0),
                    map=product.get('map', 0),
                    statusP=product.get('statusP', False),
                    statusS=product.get('statusS', False),
                    stockP=product.get('stockP', 0),
                    stockS=product.get('stockS', 0),
                    thumbnail=product.get('thumbnail', ""),
                    roomsets=product.get('roomsets', [])
                )
                success += 1
                print("Brand: {}, MPN: {}".format(feed.brand, feed.mpn))
            except Exception as e:
                failed += 1
                self.log("DatabaseManager", 1, str(e))
                continue

        self.log("DatabaseManager", 0, "Finished writing {} feeds to our database. Total: {}, Success: {}, Failed: {}".format(
            brand, total, success, failed))

    def fetchType(self, typeText):
        try:
            productType = Type.objects.get(name=typeText)
            if productType.parentTypeId == 0:
                ptype = productType.name
            else:
                parentType = Type.objects.get(
                    typeId=productType.parentTypeId)
                if parentType.parentTypeId == 0:
                    ptype = parentType.name
                else:
                    rootType = Type.objects.get(
                        typeId=parentType.parentTypeId)
                    ptype = rootType.name
        except Type.DoesNotExist:
            self.log("DatabaseManager", 1,
                     "Unknown product type: {}".format(typeText))
            ptype = ""

        return ptype
