from library import debug, common, const
from brands.models import Feed
from mysql.models import Type


class DatabaseManager:
    def __init__(self, con):
        self.con = con
        self.csr = self.con.cursor()

    def __del__(self):
        self.csr.close()

    def writeFeed(self, brand, products: list):
        debug.debug("DatabaseManager", 0,
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
                debug.debug("DatabaseManager", 1, str(e))
                continue

        debug.debug("DatabaseManager", 0, "Finished writing {} feeds to our database. Total: {}, Success: {}, Failed: {}".format(
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
            debug.debug("DatabaseManager", 1,
                        "Unknown product type: {}".format(typeText))
            ptype = ""

        return ptype

    def statusSync(self, brand, fullSync=False):
        debug.debug("DatabaseManager", 0,
                    "Started status sync for {}".format(brand))

        self.csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = '{}')""".format(brand))
        rows = self.csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = Feed.objects.get(mpn=mpn)
                product.productId = productID
                product.save()

                if published == 1 and product.status == False:
                    self.csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    self.con.commit()
                    self.csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    self.con.commit()

                    upb = upb + 1
                    debug.debug(
                        "DatabaseManager", 0, "Disabled product -- Brand: {}, ProductID: {}, mpn: {}".format(brand, productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    self.csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    self.con.commit()
                    self.csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    self.con.commit()

                    pb = pb + 1
                    debug.debug(
                        "DatabaseManager", 0, "Enabled product -- Brand: {}, ProductID: {}, mpn: {}".format(brand, productID, mpn))

            except Feed.DoesNotExist:
                if published == 1:
                    self.csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    self.con.commit()
                    self.csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    self.con.commit()

                    upb = upb + 1
                    debug.debug(
                        "DatabaseManager", 0, "Disabled product -- Brand: {}, ProductID: {}, mpn: {}".format(brand, productID, mpn))

            if fullSync:
                self.csr.execute(
                    "CALL AddToPendingUpdatePublish ({})".format(productID))
                self.con.commit()

        debug.debug("DatabaseManager", 0,
                    "Finished status sync for {}. total: {}, published: {}, unpublished: {}".format(brand, total, pb, upb))

    def createProduct(self, brand, product, formatPrice=True):
        if product.statusP == False or product.productId != None:
            return False

        name = " | ".join(
            (product.manufacturer, product.pattern, product.color, product.type))
        title = " ".join(
            (product.manufacturer, product.pattern, product.color, product.type))
        description = title
        vname = title
        hassample = 1
        gtin = product.upc
        weight = product.weight

        bodyHTML = ""
        if product.description != "":
            bodyHTML += "{}<br/>".format(product.description)
        if product.disclaimer != "":
            bodyHTML += "<small><i>Disclaimer: {}</i></small><br/><br/>".format(
                product.disclaimer)
        else:
            bodyHTML += "<br/>"
        if product.collection != "":
            bodyHTML += "Collection: {}<br/><br/>".format(
                product.collection)

        if float(product.width) > 0:
            bodyHTML += "Width: {} in<br/>".format(product.width)
        if float(product.length) > 0:
            bodyHTML += "Length: {} in<br/>".format(product.length)
        if float(product.height) > 0:
            bodyHTML += "Height: {} in<br/>".format(product.height)
        if product.size != "":
            bodyHTML += "Size: {}<br/>".format(product.size)
        if product.size != "":
            bodyHTML += "Size: {}<br/>".format(product.size)
        if product.dimension != "":
            bodyHTML += "Dimension: {}<br/>".format(product.dimension)

        if float(product.repeatH) > 0:
            bodyHTML += "Horizontal Repeat: {} in<br/>".format(product.repeatH)
        if float(product.repeatV) > 0:
            bodyHTML += "Vertical Repeat: {} in<br/>".format(product.repeatV)
        if product.repeat != "":
            bodyHTML += "Repeat: {}<br/>".format(product.repeat)

        if product.material != "":
            bodyHTML += "Material: {}<br/>".format(product.material)
        if product.finish != "":
            bodyHTML += "Finish: {}<br/>".format(product.finish)
        if product.care != "":
            bodyHTML += "Care Instructions: {}<br/>".format(product.care)

        if len(product.specs) > 0:
            for spec in product.specs:
                bodyHTML += "{}: {}<br/>".format(spec['key'], spec['value'])
        if len(product.features) > 0:
            for feature in product.features:
                bodyHTML += "{}<br/><br/>".format(feature)

        if product.country != "":
            bodyHTML += "Country of Origin: {}<br/>".format(
                product.country)
        if product.usage != "":
            bodyHTML += "Usage: {}<br/>".format(product.usage)
        else:
            bodyHTML += "Usage: {}<br/>".format(product.type)

        bodyHTML += "{} {}".format(product.manufacturer, product.type)

        try:
            useMAP = const.markup[brand]["useMAP"]
            consumerMarkup = const.markup[brand]["consumer"]
            tradeMarkup = const.markup[brand]["trade"]

            if useMAP:
                if formatPrice:
                    price = common.formatprice(product.map, 1)
                else:
                    price = product.map
            else:
                if formatPrice:
                    price = common.formatprice(product.cost, consumerMarkup)
                else:
                    price = product.cost * consumerMarkup

            if formatPrice:
                priceTrade = common.formatprice(product.cost, tradeMarkup)
            else:
                priceTrade = product.cost * tradeMarkup
        except Exception as e:
            debug.debug("DatabaseManager", 1, str(e))
            return False

        if price < 19.99:
            price = 19.99
            priceTrade = 16.99
        priceSample = 5

        try:
            productType = Type.objects.get(name=product.type)
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
            debug.debug("DatabaseManager", 1,
                        "Unknown product type: {}".format(product.type))
            return False

        self.csr.execute("CALL CreateProduct ({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{})".format(
            common.sq(product.sku),
            common.sq(name),
            common.sq(product.manufacturer),
            common.sq(product.mpn),
            common.sq(bodyHTML),
            common.sq(title),
            common.sq(description),
            common.sq(ptype),
            common.sq(vname),
            hassample,
            product.cost,
            price,
            priceTrade,
            priceSample,
            common.sq(product.pattern),
            common.sq(product.color),
            product.minimum,
            common.sq(product.increment),
            common.sq(product.uom),
            common.sq(product.usage),
            common.sq(product.collection),
            common.sq(str(gtin)),
            weight
        ))
        self.con.commit()

        return True
