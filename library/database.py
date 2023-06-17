import environ
import requests
import json
import paramiko
import urllib

from library import debug, common, const, shopify
from mysql.models import Type, Manufacturer
from shopify.models import Product

opener = urllib.request.build_opener()
opener.addheaders = [
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)

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
                    pattern=product.get('pattern'),
                    color=product.get('color'),
                    name=product.get('name', ""),

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
                    depth=product.get('depth', 0),
                    size=product.get('size', ""),
                    dimension=product.get('dimension', ""),
                    repeatH=product.get('repeatH', 0),
                    repeatV=product.get('repeatV', 0),
                    repeat=product.get('repeat', ""),

                    yards=product.get('yards', 0),
                    content=product.get('content', ""),
                    match=product.get('match', ""),
                    material=product.get('material', ""),
                    finish=product.get('finish', ""),
                    care=product.get('care', ""),
                    specs=product.get('specs', []),
                    features=product.get('features', []),
                    weight=product.get('weight', 5),
                    country=product.get('country', ""),
                    upc=product.get('upc', ""),
                    custom=product.get('custom', {}),

                    cost=product.get('cost'),
                    msrp=product.get('msrp', 0),
                    map=product.get('map', 0),

                    uom=product.get('uom'),
                    minimum=product.get('minimum', 1),
                    increment=product.get('increment', ""),

                    tags=product.get('tags', ""),
                    colors=product.get('colors', ""),

                    statusP=product.get('statusP', False),
                    statusS=product.get('statusS', False),
                    european=product.get('european', False),
                    outlet=product.get('outlet', False),
                    whiteGlove=product.get('whiteGlove', False),
                    quickShip=product.get('quickShip', False),
                    bestSeller=product.get('bestSeller', False),

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

    def validateFeed(self):
        # Validate Required fields
        invalidProducts = []
        products = self.Feed.objects.all()
        for product in products:
            if not (product.pattern and product.color and product.type and product.cost > 0 and product.uom):
                invalidProducts.append(product.mpn)

        if len(invalidProducts) == 0:
            debug.debug(self.brand, 0, "Product fields are ok!")
        else:
            debug.debug(
                self.brand, 1, f"The following products missing mandatory fields: {', '.join(invalidProducts)}")

        # Validate Types
        types = self.Feed.objects.values_list('type', flat=True).distinct()
        unknownTypes = []
        for t in types:
            try:
                Type.objects.get(name=t)
            except Type.DoesNotExist:
                unknownTypes.append(t)

        if len(unknownTypes) == 0:
            debug.debug(self.brand, 0, "Types are ok!")
        else:
            debug.debug(self.brand, 1,
                        f"Unknown Types: {', '.join(unknownTypes)}")

        # Validate Manufacturers
        manufacturers = self.Feed.objects.values_list(
            'manufacturer', flat=True).distinct()
        unknownManufacturers = []
        for m in manufacturers:
            try:
                manufacturer = Manufacturer.objects.get(name=m)
                if not (manufacturer.name and manufacturer.brand):
                    unknownManufacturers(m)
            except Manufacturer.DoesNotExist:
                unknownManufacturers.append(m)

        if len(unknownManufacturers) == 0:
            debug.debug(self.brand, 0, "Manufacturers are ok!")
        else:
            debug.debug(
                self.brand, 1, f"Unknown Manufacturers: {', '.join(unknownManufacturers)}")

        # Validate UOMs
        uoms = self.Feed.objects.values_list('uom', flat=True).distinct()
        unknownUOMs = []
        for u in uoms:
            if u not in ['Per Roll', 'Per Yard', 'Per Item', 'Per Panel']:
                unknownUOMs.append(u)

        if len(unknownUOMs) == 0:
            debug.debug(self.brand, 0, "UOMs are ok!")
        else:
            debug.debug(
                self.brand, 1, f"Unknown UOMs: {', '.join(unknownUOMs)}")

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

    def formatPrice(self, product, formatPrice):
        try:
            useMAP = const.markup[self.brand]["useMAP"]

            consumerMarkup = const.markup[self.brand]["consumer"]
            tradeMarkup = const.markup[self.brand]["trade"]

            if product.type == "Pillow" and "consumer_pillow" in const.markup[self.brand]:
                consumerMarkup = const.markup[self.brand]["consumer_pillow"]
                tradeMarkup = const.markup[self.brand]["trade_pillow"]

            if product.european and "consumer_european" in const.markup[self.brand]:
                consumerMarkup = const.markup[self.brand]["consumer_european"]
                tradeMarkup = const.markup[self.brand]["trade_european"]

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
            debug.debug(self.brand, 1,
                        f"Price Error. Check if markups are defined properly. {str(e)}")
            return (0, 0, 0)

        if price < 19.99:
            price = 19.99
            priceTrade = 16.99
        priceSample = 5

        return (price, priceTrade, priceSample)

    def createProduct(self, product, formatPrice):

        ptype = product.type
        manufacturer = product.manufacturer

        if "JF Fabrics" in manufacturer:
            manufacturer = product.brand
        elif ptype in manufacturer:
            manufacturer = str(manufacturer).replace(ptype, "").strip()

        if str(ptype).endswith("es"):
            ptype = ptype[:-2]
        elif str(ptype).endswith("s"):
            ptype = ptype[:-1]

        if product.name != "":
            name = " | ".join((manufacturer, product.name))
            title = " ".join((manufacturer, product.name))
        else:
            name = " | ".join(
                (manufacturer, product.pattern, product.color, ptype))
            title = " ".join(
                (manufacturer, product.pattern, product.color, ptype))

        description = title
        vname = title
        hassample = 1
        gtin = product.upc
        weight = product.weight or 5

        bodyHTML = ""
        if product.description:
            bodyHTML += "{}<br/>".format(product.description)
        if product.disclaimer != "":
            bodyHTML += "<small><i>Disclaimer: {}</i></small><br/><br/>".format(
                product.disclaimer)
        else:
            bodyHTML += "<br/>"
        if product.collection:
            bodyHTML += "Collection: {}<br/><br/>".format(
                product.collection)

        if float(product.width) > 0:
            bodyHTML += "Width: {} in<br/>".format(product.width)
        if float(product.length) > 0:
            bodyHTML += "Length: {} in<br/>".format(product.length)
        if float(product.height) > 0:
            bodyHTML += "Height: {} in<br/>".format(product.height)
        if float(product.depth) > 0:
            bodyHTML += "Depth: {} in<br/>".format(product.depth)
        if product.size:
            bodyHTML += "Size: {}<br/>".format(product.size)
        if product.dimension:
            bodyHTML += "Dimension: {}<br/>".format(product.dimension)
        if float(product.yards) > 0:
            bodyHTML += "Roll Length: {} yds<br/>".format(product.yards)

        if float(product.repeatH) > 0:
            bodyHTML += "Horizontal Repeat: {} in<br/>".format(product.repeatH)
        if float(product.repeatV) > 0:
            bodyHTML += "Vertical Repeat: {} in<br/>".format(product.repeatV)
        if product.repeat:
            bodyHTML += "Repeat: {}<br/>".format(product.repeat)

        if product.content:
            bodyHTML += "Content: {}<br/>".format(product.content)
        if product.match:
            bodyHTML += "Content: {}<br/>".format(product.match)
        if product.material:
            bodyHTML += "Material: {}<br/>".format(product.material)
        if product.finish:
            bodyHTML += "Finish: {}<br/>".format(product.finish)
        if product.care:
            bodyHTML += "Care Instructions: {}<br/>".format(product.care)

        if len(product.specs) > 0:
            for spec in product.specs:
                specKey, specVal = spec
                bodyHTML += "{}: {}<br/>".format(specKey, specVal)
        if len(product.features) > 0:
            for feature in product.features:
                bodyHTML += "{}<br/>".format(feature)
        bodyHTML += "<br/>"

        if product.country:
            bodyHTML += "Country of Origin: {}<br/>".format(
                product.country)
        if product.usage:
            bodyHTML += "Usage: {}<br/>".format(product.usage)
        else:
            bodyHTML += "Usage: {}<br/><br/>".format(ptype)

        bodyHTML += "{} {}".format(manufacturer, ptype)

        price, priceTrade, priceSample = self.formatPrice(
            product, formatPrice=formatPrice)
        if price == 0:
            return False

        try:
            productType = Type.objects.get(name=product.type)
            if productType.parentTypeId == 0:
                rootProductType = productType.name
            else:
                parentType = Type.objects.get(
                    typeId=productType.parentTypeId)
                if parentType.parentTypeId == 0:
                    rootProductType = parentType.name
                else:
                    rootType = Type.objects.get(
                        typeId=parentType.parentTypeId)
                    rootProductType = rootType.name
        except Type.DoesNotExist:
            debug.debug(self.brand, 1,
                        "Unknown product type: {}".format(product.type))
            return False

        if rootProductType in ["Fabric", "Wallpaper", "Pillow"]:
            priceSample = 7
        elif rootProductType == "Rug":
            priceSample = 15

        self.csr.execute("CALL CreateProduct ({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{})".format(
            common.sq(product.sku),
            common.sq(name),
            common.sq(product.manufacturer),
            common.sq(product.mpn),
            common.sq(bodyHTML),
            common.sq(title),
            common.sq(description),
            common.sq(rootProductType),
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

        total = len(products)
        for index, product in enumerate(products):
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

                debug.debug(
                    self.brand, 0, f"{index}/{total}: Created New product ProductID: {product.productId}, SKU: {product.sku}")

            except Exception as e:
                debug.debug(self.brand, 1, str(e))

    def updateProducts(self, products, formatPrice=True):
        total = len(products)
        for index, product in enumerate(products):
            if product.productId == None:
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
                self.csr.execute(
                    f"CALL AddToPendingUpdateProduct ({product.productId})")
                self.con.commit()

                debug.debug(
                    self.brand, 0, f"{index}/{total}: Updated the product ProductID: {product.productId}, SKU: {product.sku}")

            except Exception as e:
                debug.debug(self.brand, 1, str(e))

    def updatePrices(self, formatPrice=True):
        updatedProducts = []

        self.csr.execute(f"""
            SELECT PV.VariantId, PV.ProductId, PV.Name, PV.Cost, PV.Price, PV.IsDefault
            FROM ProductVariant PV
            LEFT JOIN Product P ON P.ProductId = PV.ProductId
            LEFT JOIN ProductManufacturer PM ON PM.SKU = P.SKU
            LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
            WHERE M.BRAND = "{self.brand}"
                AND PV.Name NOT LIKE '%SAMPLE - %' 
                AND PV.Cost IS NOT NULL
                AND PV.ProductId IS NOT NULL
        """)
        variants = self.csr.fetchall()

        total = len(variants)
        for index, variant in enumerate(variants):
            try:
                productId = variant[1]
                name = variant[2]
                oldCost = float(variant[3])
                oldPrice = float(variant[4])
                isDefault = bool(variant[5])

                if productId in updatedProducts:
                    continue

                try:
                    product = self.Feed.objects.get(productId=productId)
                except self.Feed.DoesNotExist:
                    continue

                if isDefault:
                    type = "Consumer"
                elif "Trade - " in name:
                    type = "Trade"
                else:
                    debug.debug(self.brand, 1, f"Unknown variant {name}")
                    continue

                price, priceTrade, priceSample = self.formatPrice(
                    product, formatPrice=formatPrice)
                if price == 0:
                    return False

                if product.cost != oldCost or (type == "Consumer" and price != oldPrice) or (type == "Trade" and priceTrade != oldPrice):
                    self.csr.execute("CALL UpdatePriceAndTrade ({}, {}, {}, {})".format(
                        productId, product.cost, price, priceTrade))
                    self.con.commit()
                    self.csr.execute(
                        "CALL AddToPendingUpdatePrice ({})".format(productId))
                    self.con.commit()

                    updatedProducts.append(productId)

                    debug.debug(
                        self.brand, 0, f"{index}/{total}: Updated prices for ProductID: {productId}. COST: {product.cost}, Price: {price}, Trade Price: {priceTrade}, Checked: {type}")

                else:
                    debug.debug(
                        self.brand, 0, f"{index}/{total}: Prices are already updated. ProductId: {productId}. COST: {product.cost}, Price: {price}, Trade Price: {priceTrade}, Checked: {type}")

            except Exception as e:
                debug.debug(self.brand, 1, str(e))
                continue

    def downloadImage(self, productId, thumbnail, roomsets):
        if thumbnail and thumbnail.strip() != "" and "http" in thumbnail:
            try:
                common.picdownload2(str(thumbnail).strip().replace(
                    " ", "%20"), "{}.jpg".format(productId))
            except Exception as e:
                debug.debug(self.brand, 1, str(e))

        if len(roomsets) > 0:
            idx = 2
            for roomset in roomsets:
                try:
                    common.roomdownload(str(roomset).strip().replace(
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

    def downloadFileFromLink(self, src, dst):
        try:
            urllib.request.urlretrieve(src, dst)
            debug.debug(self.brand, 1,
                        f"Downloaded Successfully. {dst} From {src}")
        except Exception as e:
            debug.debug(self.brand, 1,
                        f"Download Error {dst} From {src}. Error: {str(e)}")

    def downloadFileFromSFTP(self, src, dst, fileSrc=True):
        try:
            transport = paramiko.Transport(
                (const.sftp[self.brand]["host"], const.sftp[self.brand]["port"]))
            transport.connect(
                username=const.sftp[self.brand]["user"], password=const.sftp[self.brand]["pass"])
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            debug.debug(self.brand, 1,
                        f"Connection to {self.brand} SFTP Server Failed. Error: {str(e)}")
            return False

        if fileSrc:
            sftp.get(src, dst)
        else:
            if src != "":
                sftp.chdir(src)

            files = sftp.listdir()
            for file in files:
                if "EDI" in file:
                    continue

                sftp.get(file, dst)
                sftp.remove(file)

        sftp.close()

        debug.debug(self.brand, 0,
                    f"{dst} downloaded from {self.brand} SFTP")
        return True

    def downloadFileFromFTP(self, src, dst):
        try:
            urllib.request.urlretrieve(
                f"ftp://{const.ftp[self.brand]['user']}:{const.ftp[self.brand]['pass']}@{const.ftp[self.brand]['host']}/{src}", dst)
        except Exception as e:
            debug.debug(self.brand, 1,
                        f"Connection to {self.brand} FTP Server Failed. Error: {str(e)}")
            return False

        debug.debug(self.brand, 0,
                    f"{dst} downloaded from {self.brand} FTP")
        return True

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
            length = product.length

            if tags:
                if category:
                    if type == "Fabric" and "outdoor" in tags.lower():
                        tags = f"{tags}, Performance Fabric"

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

            if type == "Pillow" or type == "Rug":
                size = f"{common.formatInt(width / 12)}' x {common.formatInt(length / 12)}', {size}, {tags}"
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

    def customTags(self, key, tag, logic=True):
        products = self.Feed.objects.all()

        for product in products:
            if product.productId:
                if getattr(product, key) == logic:
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
