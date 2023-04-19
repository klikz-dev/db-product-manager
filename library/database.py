import environ
import requests
import json

from library import debug, common, const, shopify
from mysql.models import Type
from shopify.models import Product

env = environ.Env()
SHOPIFY_API_URL = "https://decoratorsbest.myshopify.com/admin/api/{}".format(
    env('shopify_api_version'))
SHOPIFY_PRODUCT_API_HEADER = {
    'X-Shopify-Access-Token': env('shopify_product_token'),
    'Content-Type': 'application/json'
}


class DatabaseManager:
    def __init__(self, con, brand, Feed):
        self.con = con
        self.csr = self.con.cursor()

        self.brand = brand
        self.Feed = Feed

    def __del__(self):
        self.csr.close()

    def writeFeed(self, products: list):
        debug.debug(self.brand, 0,
                    f"Started writing {self.brand} feeds to our database")

        self.Feed.objects.all().delete()

        total = len(products)
        success = 0
        failed = 0
        for product in products:
            try:
                feed = self.Feed.objects.create(
                    mpn=product.get('mpn'),
                    sku=product.get('sku'),
                    upc=product.get('upc', ""),
                    pattern=product.get('pattern'),
                    color=product.get('color'),
                    title=product.get('title', ""),
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
                    yards=product.get('yards', 0),
                    repeatH=product.get('repeatH', 0),
                    repeatV=product.get('repeatV', 0),
                    repeat=product.get('repeat', ""),
                    content=product.get('content', ""),
                    match=product.get('match', ""),
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
                    whiteShip=product.get('whiteShip', False),
                    quickShip=product.get('quickShip', False),
                    stockP=product.get('stockP', 0),
                    stockS=product.get('stockS', 0),
                    stockNote=product.get('stockNote', 0),
                    thumbnail=product.get('thumbnail', ""),
                    roomsets=product.get('roomsets', [])
                )
                success += 1
                print(f"Brand: {feed.brand}, MPN: {feed.mpn}")
            except Exception as e:
                failed += 1
                debug.debug(self.brand, 1, str(e))
                continue

        debug.debug(
            self.brand, 0, f"Finished writing {self.brand} feeds to our database. Total: {total}, Success: {success}, Failed: {failed}")

    def statusSync(self, fullSync=False):
        debug.debug(self.brand, 0, f"Started status sync for {self.brand}")

        self.csr.execute(f"""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = '{self.brand}')""")
        rows = self.csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = self.Feed.objects.get(mpn=mpn)
                product.productId = productID
                product.save()

                if published == 1 and product.statusP == False:
                    self.csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    self.con.commit()
                    self.csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    self.con.commit()

                    upb = upb + 1
                    debug.debug(
                        self.brand, 0, f"Disabled product -- Brand: {self.brand}, ProductID: {productID}, mpn: {mpn}")

                if published == 0 and product.statusP == True and product.cost != None:
                    self.csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    self.con.commit()
                    self.csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    self.con.commit()

                    pb = pb + 1
                    debug.debug(
                        self.brand, 0, f"Enabled product -- Brand: {self.brand}, ProductID: {productID}, mpn: {mpn}")

            except self.Feed.DoesNotExist:
                if published == 1:
                    self.csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    self.con.commit()
                    self.csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    self.con.commit()

                    upb = upb + 1
                    debug.debug(
                        self.brand, 0, f"Disabled product -- Brand: {self.brand}, ProductID: {productID}, mpn: {mpn}")

            if fullSync:
                self.csr.execute(
                    "CALL AddToPendingUpdatePublish ({})".format(productID))
                self.con.commit()

        debug.debug(
            self.brand, 0, f"Finished status sync for {self.brand}. total: {total}, published: {pb}, unpublished: {upb}")

    def createProduct(self, product, formatPrice):

        ptype = product.type
        manufacturer = product.manufacturer

        if ptype in manufacturer:
            manufacturer = str(manufacturer).replace(ptype, "").strip()

        if product.title != "":
            name = " | ".join((manufacturer, product.title))
            title = " ".join((manufacturer, product.title))
        else:
            name = " | ".join(
                (manufacturer, product.pattern, product.color, ptype))
            title = " ".join(
                (manufacturer, product.pattern, product.color, ptype))

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
        if float(product.yards) > 0:
            bodyHTML += "Roll Length: {} yds<br/>".format(product.yards)

        if float(product.repeatH) > 0:
            bodyHTML += "Horizontal Repeat: {} in<br/>".format(product.repeatH)
        if float(product.repeatV) > 0:
            bodyHTML += "Vertical Repeat: {} in<br/>".format(product.repeatV)
        if product.repeat != "":
            bodyHTML += "Repeat: {}<br/>".format(product.repeat)

        if product.content != "":
            bodyHTML += "Content: {}<br/>".format(product.content)
        if product.match != "":
            bodyHTML += "Content: {}<br/>".format(product.match)
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
                bodyHTML += "{}<br/>".format(feature)
        bodyHTML += "<br/>"

        if product.country != "":
            bodyHTML += "Country of Origin: {}<br/>".format(
                product.country)
        if product.usage != "":
            bodyHTML += "Usage: {}<br/>".format(product.usage)
        else:
            bodyHTML += "Usage: {}<br/><br/>".format(ptype)

        bodyHTML += "{} {}".format(manufacturer, ptype)

        try:
            useMAP = const.markup[self.brand]["useMAP"]
            consumerMarkup = const.markup[self.brand]["consumer"]
            tradeMarkup = const.markup[self.brand]["trade"]

            if useMAP and product.map > 0:
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
            debug.debug(self.brand, 1, str(e))
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
            debug.debug(self.brand, 1,
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

    def createProducts(self, formatPrice=True):
        products = self.Feed.objects.all()

        for product in products:
            if product.statusP == False or product.productId != None:
                continue

            try:
                createdInDatabase = self.createProduct(
                    product, formatPrice)
                if not createdInDatabase:
                    continue
            except Exception as e:
                debug.debug(self.brand, 1, str(e))
                continue

            try:
                product.productId = shopify.NewProductBySku(
                    product.sku, self.con)
                product.save()

                self.downloadImage(product.productId,
                                   product.thumbnail, product.roomsets)

                debug.debug(self.brand, 0, "Created New product ProductID: {}, SKU: {}".format(
                    product.productId, product.sku))

            except Exception as e:
                debug.debug(self.brand, 1, str(e))

    def updateProducts(self, products, formatPrice=True):
        for product in products:
            if product.statusP == False or product.productId == None:
                return False

            try:
                createdInDatabase = self.createProduct(
                    self.brand, product, formatPrice)
                if not createdInDatabase:
                    continue
            except Exception as e:
                debug.debug(self.brand, 1, str(e))
                continue

            try:
                self.csr.execute(
                    "CALL AddToPendingUpdateProduct ({})".format(product.productId))
                self.con.commit()

                debug.debug(self.brand, 0, "Updated the product ProductID: {}, SKU: {}".format(
                    product.productId, product.sku))

            except Exception as e:
                debug.debug(self.brand, 1, str(e))

    def updatePrices(self, formatPrice=True):
        products = self.Feed.objects.all()

        for product in products:
            cost = product.cost
            productId = product.productId

            if productId != "" and productId != None:
                try:
                    useMAP = const.markup[self.brand]["useMAP"]
                    if product.type == "Pillow" and "consumer_pillow" in const.markup[self.brand]:
                        consumerMarkup = const.markup[self.brand]["consumer_pillow"]
                        tradeMarkup = const.markup[self.brand]["trade_pillow"]
                    else:
                        consumerMarkup = const.markup[self.brand]["consumer"]
                        tradeMarkup = const.markup[self.brand]["trade"]

                    if useMAP and product.map > 0:
                        if formatPrice:
                            price = common.formatprice(product.map, 1)
                        else:
                            price = product.map
                    else:
                        if formatPrice:
                            price = common.formatprice(
                                product.cost, consumerMarkup)
                        else:
                            price = product.cost * consumerMarkup

                    if formatPrice:
                        priceTrade = common.formatprice(
                            product.cost, tradeMarkup)
                    else:
                        priceTrade = product.cost * tradeMarkup
                except Exception as e:
                    debug.debug(self.brand, 1, str(e))
                    return False

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99

                try:
                    self.csr.execute("SELECT PV1.Cost, PV1.Price, PV2.Price AS TradePrice FROM ProductVariant PV1, ProductVariant PV2 WHERE PV1.ProductID = {} AND PV2.ProductID = {} AND PV1.IsDefault = 1 AND PV2.Name LIKE 'Trade - %' AND PV1.Cost IS NOT NULL AND PV2.Cost IS NOT NULL".format(productId, productId))
                    tmp = self.csr.fetchone()
                    if tmp == None:
                        debug.debug(
                            "DatabaseManager", 1, "Variant not found: ProductId: {}".format(productId))
                        continue

                    oCost = float(tmp[0])
                    oPrice = float(tmp[1])
                    oTrade = float(tmp[2])

                    if cost != oCost or price != oPrice or priceTrade != oTrade:
                        self.csr.execute("CALL UpdatePriceAndTrade ({}, {}, {}, {})".format(
                            productId, cost, price, priceTrade))
                        self.con.commit()
                        self.csr.execute(
                            "CALL AddToPendingUpdatePrice ({})".format(productId))
                        self.con.commit()

                        debug.debug(self.brand, 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                            productId, cost, price, priceTrade))
                    else:
                        debug.debug(self.brand, 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                            productId, price, priceTrade))

                except:
                    debug.debug(self.brand, 1, "Updating price error for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                        productId, cost, price, priceTrade))
                    continue

    def downloadImage(self, productId, thumbnail, roomsets):
        if thumbnail and thumbnail.strip() != "":
            try:
                common.picdownload2(str(thumbnail).replace(
                    " ", "%20"), "{}.jpg".format(productId))
            except Exception as e:
                debug.debug(self.brand, 1, str(e))

        if len(roomsets) > 0:
            idx = 2
            for roomset in roomsets:
                try:
                    common.roomdownload(str(roomset).replace(
                        " ", "%20"), "{}_{}.jpg".format(productId, idx))
                    idx = idx + 1
                except Exception as e:
                    debug.debug(self.brand, 1, str(e))

    def downloadImages(self, missingOnly=True):
        hasImage = []

        self.csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = '{}'".format(self.brand))
        for row in self.csr.fetchall():
            hasImage.append(str(row[0]))

        products = self.Feed.objects.all()
        for product in products:
            if not product.productId:
                continue

            if missingOnly and product.productId in hasImage:
                continue

            self.downloadImage(product.productId,
                               product.thumbnail, product.roomsets)

    def updateStock(self, stocks, stockType=1):
        for stock in stocks:
            try:
                self.csr.execute("CALL UpdateProductInventory ('{}', {}, {}, '{}', '{}')".format(
                    stock['sku'], stock['quantity'], stockType, stock['note'], self.brand))
                self.con.commit()
                debug.debug(self.brand, 0,
                            "Updated inventory. {}.".format(stock))
            except Exception as e:
                debug.debug(self.brand, 1, str(e))

    def updateTags(self, category=True):
        products = self.Feed.objects.all()

        for product in products:
            sku = product.sku
            type = product.type

            colors = product.colors
            tags = ", ".join((product.type, product.pattern, product.tags))
            collection = product.collection
            size = product.size
            width = product.width

            if tags:
                if category:
                    self.csr.execute("CALL AddToEditCategory ({}, {})".format(
                        common.sq(sku), common.sq(tags)))
                    self.con.commit()

                self.csr.execute("CALL AddToEditStyle ({}, {})".format(
                    common.sq(sku), common.sq(tags)))
                self.con.commit()

                self.csr.execute("CALL AddToEditSubtype ({}, {})".format(
                    common.sq(sku), common.sq(str(tags).strip())))
                self.con.commit()

            if colors:
                self.csr.execute("CALL AddToEditColor ({}, {})".format(
                    common.sq(sku), common.sq(colors)))
                self.con.commit()

            if collection:
                self.csr.execute("CALL AddToEditCollection ({}, {})".format(
                    common.sq(sku), common.sq(collection)))
                self.con.commit()

            if size and type == "Pillow":
                self.csr.execute("CALL AddToEditSize ({}, {})".format(
                    common.sq(sku), common.sq(size)))
                self.con.commit()

            if width > 0 and type == "Trim":

                if width < 1:
                    tag = 'Up to 1"'
                elif width < 2:
                    tag = '1" to 2"'
                elif width < 3:
                    tag = '2" to 3"'
                elif width < 4:
                    tag = '3" to 4"'
                elif width < 5:
                    tag = '4" to 5"'
                else:
                    tag = '5" and More'

                self.csr.execute("CALL AddToEditSize ({}, {})".format(
                    common.sq(sku), common.sq(tag)))
                self.con.commit()

            debug.debug(self.brand, 0,
                        "Added Tags for Brand: {}, SKU: {}".format(self.brand, sku))

    def customTags(self, key, tag):
        products = self.Feed.objects.all()

        for product in products:
            if product.productId:
                if product[key]:
                    self.csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(product.sku), common.sq(tag)))
                    self.con.commit()
                    debug.debug(self.brand, 0, "{} Tag has been applied to the {} product {}".format(
                        tag, self.brand, product.sku))
                else:
                    self.csr.execute("CALL RemoveFromProductTag ({}, {})".format(
                        common.sq(product.sku), common.sq(tag)))
                    self.con.commit()
                    debug.debug(self.brand, 0, "{} Tag has been removed from the {} product {}".format(
                        tag, self.brand, product.sku))

                self.csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                    product.productId))
                self.con.commit()

    def getOrders(self):
        ediName = f"{self.brand}EDI"
        ediStatus = f"{self.brand} EDI"

        self.csr.execute(f"""SELECT DISTINCT
                    O.OrderNumber AS OrderNumber, 
                    DATE_FORMAT(O.CreatedAt, '%d-%b-%y') AS OrderDate, 
                    CONCAT(O.ShippingFirstName, ' ', O.ShippingLastName) AS Name,
                    O.ShippingAddress1 AS Address1,
                    O.ShippingAddress2 AS Address2,
                    O.ShippingCompany AS Suite,
                    O.ShippingCity AS City,
                    O.ShippingState AS State,
                    '' AS County,
                    O.ShippingZip AS Zip,
                    CASE
                        WHEN O.ShippingCountry = 'United States' THEN 'US'
                        WHEN O.ShippingCountry = 'Canada' THEN 'CA'
                        WHEN O.ShippingCountry = 'Australia' THEN 'AU'
                        WHEN O.ShippingCountry = 'United Kingdom' THEN 'UK'
                        WHEN O.ShippingCountry = 'Finland' THEN 'FI'
                        WHEN O.ShippingCountry = 'Egypt' THEN 'EG'
                        WHEN O.ShippingCountry = 'China' THEN 'CN'
                        WHEN O.ShippingCountry = 'France' THEN 'FR'
                        WHEN O.ShippingCountry = 'Germany' THEN 'DE'
                        WHEN O.ShippingCountry = 'Mexico' THEN 'MX'
                        WHEN O.ShippingCountry = 'Russia' THEN 'RU'
                        WHEN O.ShippingCountry = 'Ireland' THEN 'IE'
                        WHEN O.ShippingCountry = 'Greece' THEN 'GR'
                        ELSE O.ShippingCountry
                    END AS Country,

                    CASE
                        WHEN O.ShippingMethod LIKE '%2nd Day%' THEN 'UPS2'
                        WHEN O.ShippingMethod LIKE '%2-day%' THEN 'UPS2'
                        WHEN O.ShippingMethod LIKE '%Overnight%' THEN 'UPSN'
                        WHEN O.ShippingMethod LIKE '%Next Day%' THEN 'UPSN'
                    ELSE 'UPSG'
                    END AS ShippingMethod,

                    O.OrderNote AS ShipInstruction,
                    CONCAT('DecoratorsBest/', O.ShippingLastName) AS PackInstruction,
                    O.ShopifyOrderID,
                    O.ShippingPhone

                    FROM Orders_ShoppingCart OS JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Orders O ON OS.ShopifyOrderID = O.ShopifyOrderID

                    WHERE PV.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = '{self.brand}')
                        AND O.OrderNumber > (SELECT {ediName} FROM PORecord)
                        AND O.Status NOT LIKE '%Hold%'
                        AND O.Status NOT LIKE '%Back Order%'
                        AND O.Status NOT LIKE '%Cancel%'
                        AND O.Status NOT LIKE '%Processed%'
                        AND O.Status NOT LIKE '%CFA%'
                        AND O.Status NOT LIKE '%Call Manufacturer%'
                        AND O.Status NOT LIKE '%{ediStatus}%'

                    ORDER BY O.OrderNumber ASC""")

        orders = []
        for row in self.csr.fetchall():
            po = int(row[0])
            orderDate = str(row[1]).strip()

            name = str(row[2]).strip()

            address1 = str(row[3]).replace("\n", "").strip()
            address2 = str(row[4]).strip()
            if "," in address1:
                address2 = str(address1).split(",")[1].strip()
                address1 = str(address1).split(",")[0].strip()
            if address2 == None or address2 == '':
                address2 = ''

            city = str(row[6]).strip()
            state = str(row[7]).strip()
            zip = str(row[9]).strip()
            country = str(row[10]).strip()
            phone = str(row[15]).strip()

            shippingMethod = str(row[11]).strip()

            shipInstruction = str(row[12]).replace('\n', ' ')
            packInstruction = str(row[13]).replace('\n', ' ')
            instructions = ""
            if shipInstruction:
                instructions += f"Ship Instruction: {shipInstruction}\n\r"
            if packInstruction:
                instructions += f"Pack Instruction: {packInstruction}"

            self.csr.execute(f"""SELECT P.ManufacturerPartNumber AS Item, CASE WHEN PV.Name LIKE '%Sample - %' THEN 'Sample' ELSE REPLACE(PV.Pricing, 'Per ', '') END AS UOM, OS.Quantity, P.SKU, PV.Cost
                            FROM Orders O JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Product P ON P.ProductID = PV.ProductID
                            WHERE PV.SKU IN (SELECT SKU
                                                FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                                                WHERE M.Brand = '{self.brand}')
                            AND O.OrderNumber = {po}""")

            items = []
            for item in self.csr.fetchall():
                mpn = str(item[0])
                uom = str(item[1])
                quantity = int(item[2])

                if "Sample" == uom:
                    uom = "MM (Sample)"
                elif "Yard" == uom:
                    uom = "YD"
                elif "Roll" == uom:
                    uom = "RL"
                elif "Square Foot" == uom:
                    uom = "SQF"
                else:
                    uom = "EA"

                items.append({
                    'mpn': mpn,
                    'uom': uom,
                    'quantity': quantity,
                })

            orders.append({
                'po': po,
                'orderDate': orderDate,
                'name': name,
                'address1': address1,
                'address2': address2,
                'city': city,
                'state': state,
                'zip': zip,
                'country': country,
                'phone': phone,
                'shippingMethod': shippingMethod,
                'instructions': instructions,
                'items': items,
            })

        return orders

    def updateEDIOrderStatus(self, orderNumber):
        ediStatus = f"{self.brand} EDI"

        self.csr.execute(
            f"SELECT Status FROM Orders WHERE OrderNumber = {orderNumber}")
        extStatus = (self.csr.fetchone())[0]
        if extStatus == "New":
            newStatus = f"{ediStatus}"
        else:
            newStatus = f"{extStatus}, {ediStatus}"

        self.csr.execute(
            f"UPDATE Orders SET Status = {common.sq(newStatus)} WHERE OrderNumber = {orderNumber}")
        self.con.commit()

    def updatePORecord(self, lastPO):
        ediName = f"{self.brand}EDI"

        self.csr.execute(f"UPDATE PORecord SET {ediName} = {lastPO}")
        self.con.commit()

    def updateRefNumber(self, orderNumber, refNumber):
        ediStatus = f"{self.brand} EDI"

        self.csr.execute(
            f"SELECT ReferenceNumber FROM Orders WHERE OrderNumber = '{orderNumber}'")

        try:
            ref = str((self.csr.fetchone())[0])
            if ref == "None":
                ref = ""

            print(ref)

            if refNumber not in ref:
                newRef = f"{ref}\n{ediStatus}: {refNumber}"

                self.csr.execute(
                    f"UPDATE Orders SET ReferenceNumber = {common.sq(newRef)} WHERE OrderNumber = {orderNumber}")
                self.con.commit()
        except Exception as e:
            debug.debug(self.brand, str(e))

    def linkPillowSample(self):
        pillows = self.Feed.objects.filter(ptype="Pillow")

        for pillow in pillows:
            try:
                fabric = self.Feed.objects.get(
                    pattern=pillow.pattern, color=pillow.color, ptype="Fabric")
                product = Product.objects.get(productId=fabric.productId)
                handle = product.handle
            except self.Feed.DoesNotExist:
                debug.debug(
                    self.brand, 1, f"Matching Fabric not found for pillow Pattern: {pillow.pattern} and Color: {pillow.color}")
                continue

            productId = pillow.productId

            response = requests.get(
                f"{SHOPIFY_API_URL}/products/{productId}/metafields.json", headers=SHOPIFY_PRODUCT_API_HEADER)
            data = json.loads(response.text)

            isFabricLinked = False
            for metafield in data['metafields']:
                if metafield['key'] == "fabric_id":
                    payload = json.dumps({
                        "metafield": {
                            "namespace": "product",
                            "key": "fabric_id",
                            "type": "single_line_text_field",
                            "value": handle
                        }
                    })

                    response = requests.put(
                        f"{SHOPIFY_API_URL}/products/{productId}/metafields/{metafield['id']}.json", headers=SHOPIFY_PRODUCT_API_HEADER, data=payload)

                    if response.status_code == 200:
                        debug.debug(
                            self.brand, 0, f"Fabric link has been updated successfully. Pillow: {productId}, Fabric: {fabric.productId}")
                    else:
                        debug.debug(
                            self.brand, 1, f"Metafield Update API error. {response.text}")

                    isFabricLinked = True
                    break

            if not isFabricLinked:
                payload = json.dumps({
                    "metafield": {
                        "namespace": "product",
                        "key": "fabric_id",
                        "type": "single_line_text_field",
                        "value": handle
                    }
                })

                response = requests.post(
                    f"{SHOPIFY_API_URL}/products/{productId}/metafields.json", headers=SHOPIFY_PRODUCT_API_HEADER, data=payload)

                if response.status_code == 201:
                    debug.debug(
                        self.brand, 0, f"Fabric has been linked successfully. Pillow: {productId}, Fabric: {fabric.productId}")
                else:
                    debug.debug(
                        self.brand, 1, f"Metafield Create API error. {response.text}")
