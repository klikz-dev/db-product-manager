from django.core.management.base import BaseCommand
from brands.models import Scalamandre
from shopify.models import Product as ShopifyProduct

import requests
import json
import pymysql
import os
import time

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.scalamandre
markup_price_colony = markup.scalamandre_colony
markup_trade = markup.scalamandre_trade
markup_trade_european = markup.scalamandre_trade_european
markup_price_pillow = markup.scalamandre_pillow
markup_trade_pillow = markup.scalamandre_pillow_trade

debug = debug.debug
sq = common.sq


FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# API credentials
API_ADDRESS = 'http://scala-api.scalamandre.com/api'
API_USERNAME = 'Decoratorsbest'
API_PASSWORD = 'EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!'


# Get API token
r = requests.post("{}/Auth/authenticate".format(API_ADDRESS), headers={'Content-Type': 'application/json'},
                  data=json.dumps({"Username": API_USERNAME, "Password": API_PASSWORD}))
j = json.loads(r.text)
API_TOKEN = j['token']


class Command(BaseCommand):
    help = 'Build Scalamandre Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "getProductIds" in options['functions']:
            self.getProductIds()

        if "addNew" in options['functions']:
            self.addNew()
            self.updateTags()

        if "updateExisting" in options['functions']:
            self.updateExisting()

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "updateStock" in options['functions']:
            self.updateStock()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "fixMissingImages" in options['functions']:
            self.fixMissingImages()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updateStock()

                print("Completed. Waiting for next run")
                time.sleep(86400)

    def getProducts(self):
        try:
            r = requests.get("{}/ScalaFeedAPI/FetchProductsFeed".format(API_ADDRESS),
                             headers={'Authorization': 'Bearer {}'.format(API_TOKEN)})
            j = json.loads(r.text)
            rows = j['FEEDPRODUCTS']

        except Exception as e:
            print(e)
            return

        Scalamandre.objects.all().delete()

        for row in rows:
            brand = str(row['BRAND']).strip()

            mpn = row['SKU']
            new_mpn = row['ITEMID']

            if row['DISCONTINUED'] != False:
                status = False
            else:
                status = True

                try:
                    if (row['WEBENABLED'] != "Y" and row['WEBENABLED'] != "S") or row['IMAGEVALID'] != True:
                        status = False
                except:
                    continue

            # Remove Tassinari & Chatel Fabric. 3/14 from BK
            if brand == "Tassinari & Chatel" or brand == "Lelievre" or brand == "Nicolette Mayer" or brand == "Jean Paul Gaultier":
                status = False

            unknownBrands = []
            # 1/4 Remove Wallquest and include in Scala
            if "Scalamandre" in brand or "Wallquest" in brand or "Scalamandré" in brand:
                brand = "Scalamandre"
                sku = "SCALA {}".format(mpn)
            elif "Sandberg" in brand:  # 1/4 Make Sandberg as child brand
                brand = "Sandberg"
                sku = "SCALA {}".format(mpn)
            elif "Old World Weavers" in brand:
                sku = "OWW {}".format(mpn)
            elif "Grey Watkins" in brand:
                sku = "GWA {}".format(mpn)
            # elif "Boris Kroll" in brand: ### Strange Bug -- To-do
            #     sku = "BK {}".format(mpn)
            elif brand == "Aldeco" or brand == "Alhambra" or brand == "Christian Fischbacher" or brand == "Colony" or brand == "Hinson" or brand == "JWall" or brand == "Jean Paul Gaultier" or brand == "Lelievre" or brand == "MissoniHome" or brand == "Nicolette Mayer" or brand == "Tassinari & Chatel":
                sku = "SCALA {}".format(mpn)
            else:
                if brand not in unknownBrands:
                    unknownBrands.append(brand)
                continue

            try:
                Scalamandre.objects.get(sku=sku)
                continue
            except Scalamandre.DoesNotExist:
                pass

            pattern = row['PATTERN_DESCRIPTION']
            pattern = pattern.replace("PILLOW", "").strip()

            color = row['COLOR']

            if "FABR" in row['CATEGORY']:
                ptype = "Fabric"
            elif "WALL" in row['CATEGORY']:
                ptype = "Wallpaper"
            elif "TRIM" in row['CATEGORY']:
                ptype = "Trim"
            elif "PILL" in row['CATEGORY']:
                ptype = "Pillow"
            else:
                debug("Scalamandre", 2,
                      "Product Type Error. Type: {}".format(row['CATEGORY']))
                continue

            try:
                collection = row['WEB COLLECTION NAME']
            except:
                collection = ""
                pass

            description = str(row['DESIGN_INSPIRATION']).strip()

            try:
                width = row['WIDTH']
            except:
                width = ""
                pass

            try:
                pieceSize = row['PIECE SIZE']
            except:
                pieceSize = ""

            try:
                rollLength = row['YARDS PER ROLL']
            except:
                rollLength = ""

            try:
                vr = row['PATTERN REPEAT LENGTH']
            except:
                vr = ""
                pass

            try:
                hr = row['PATTERN REPEAT WIDTH']
            except:
                hr = ""
                pass

            try:
                content = row['FIBER CONTENT']
            except:
                content = ""
                pass

            usage = row['WEARCODE']
            if ptype == "Fabric":
                if "drapery" in usage.lower():
                    usage = "Drapery"
                elif "upholstery" in usage.lower():
                    usage = "Upholstery"
                elif "multi" in usage.lower():
                    usage = "Multipurpose"
                else:
                    usage = "Fabric"
            elif ptype == "Wallpaper":
                usage = "Wallcovering"
            elif ptype == "Trim":
                usage = "Trimming"
            elif ptype == "Pillow":
                usage = "Pillow"
            else:
                debug("Scalamandre", 2, "Type Error: SKU: {}".format(sku))
                continue

            price = row['NETPRICE']

            if row['STOCKINVENTORY'] != 'N':
                try:
                    stock = int(row['AVAILABLE'])
                except:
                    stock = 0
            else:
                stock = 0

            try:
                stockText = row['LEAD TIME']
            except:
                stockText = ""

            try:
                minimum = int(row['MIN ORDER'].split(' ')[0])
            except:
                minimum = 0

            try:
                if int(row['WEB SOLD BY']) > 1:
                    increment = ",".join(
                        [str(ii * int(row['WEB SOLD BY'])) for ii in range(1, 25)])
                else:
                    increment = ""
            except:
                increment = ""

            if row['UNIT OF MEASURE'] == "RL" or row['UNIT OF MEASURE'] == "DR":
                uom = 'Per Roll'
            elif row['UNIT OF MEASURE'] == "YD" or row['UNIT OF MEASURE'] == "LY":
                uom = 'Per Yard'
            elif row['UNIT OF MEASURE'] == "EA" or row['UNIT OF MEASURE'] == "PC":
                uom = 'Per Item'
            elif row['UNIT OF MEASURE'] == "SF":
                uom = 'Per Square Foot'
            elif row['UNIT OF MEASURE'] == "ST":
                uom = 'Per Set'
            elif row['UNIT OF MEASURE'] == "PN":
                uom = 'Per Panel'
            elif row['UNIT OF MEASURE'] == "TL":
                uom = 'Per Tile'
            else:
                debug("Scalamandre", 1, "UOM Error. MPN: {}".format(new_mpn))
                continue

            try:
                feature = str(row['WEARCODE']).strip()
            except:
                feature = ''
            try:
                category = str(row['MATERIALTYPE']).strip()
            except:
                category = ''

            try:
                picLink = row['IMAGEPATH']
            except:
                continue

            manufacturer = "{} {}".format(brand, ptype)

            # Tagging
            keywords = "{}, {}, {}".format(collection, category, feature)

            try:
                Scalamandre.objects.create(
                    mpn=new_mpn,
                    sku=sku,
                    pattern=pattern,
                    color=color,
                    brand=brand,
                    ptype=ptype,
                    manufacturer=manufacturer,
                    collection=collection,
                    description=description,
                    width=width,
                    pieceSize=pieceSize,
                    rollLength=rollLength,
                    content=content,
                    hr=hr,
                    vr=vr,
                    uom=uom,
                    usage=usage,
                    feature=feature,
                    category=keywords,
                    style=keywords,
                    minimum=minimum,
                    increment=increment,
                    colors=color,
                    cost=price,
                    status=status,
                    stock=stock,
                    stockText=stockText,
                    thumbnail=picLink,
                    productId="",
                )
                debug("Scalamandre", 0,
                      "Success to get product details for MPN: {}".format(mpn))
            except Exception as e:
                print(e)
                debug("Scalamandre", 2,
                      "Failed to get product details for MPN: {}".format(mpn))

        print(unknownBrands)

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Scalamandre');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Scalamandre.objects.get(sku=sku)
                product.productId = productID
                product.save()

                if published == 1 and product.status == False:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Scalamandre", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Scalamandre", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Scalamandre.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Scalamandre", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Scalamandre", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Scalamandre.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != "":
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Scalamandre", 1,
                          "No product Image for MPN: {}".format(product.mpn))
                    continue

                name = " | ".join((product.brand, product.pattern,
                                  product.color, product.ptype))
                title = " ".join((product.brand, product.pattern,
                                 product.color, product.ptype))
                description = title
                vname = title
                hassample = 1
                gtin = ""
                weight = 1

                desc = ""
                if product.description != None and product.description != "":
                    desc += "{}<br/><br/>".format(
                        product.description)
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.pieceSize != None and product.pieceSize != "" and product.ptype == "Pillow":
                    desc += "Meassurement: {}<br/>".format(product.pieceSize)
                else:
                    if product.width != None and product.width != "":
                        desc += "Width: {}<br/>".format(product.width)
                    if product.height != None and product.height != "":
                        desc += "Height: {}<br/>".format(product.height)
                    if product.hr != None and product.hr != "":
                        desc += "Horizontal Repeat: {}<br/>".format(product.hr)
                    if product.vr != None and product.vr != "":
                        desc += "Vertical Repeat: {}<br/>".format(product.vr)
                if product.rollLength != None and product.rollLength != "" and product.rollLength != 0 and product.uom == "Per Roll":
                    desc += "Roll Length: {} yds<br/>".format(
                        product.rollLength)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/>".format(product.feature)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    if product.ptype == "Pillow":
                        price = common.formatprice(cost, markup_price_pillow)
                        priceTrade = common.formatprice(
                            cost, markup_trade_pillow)
                    else:
                        if "Colony" in product.manufacturer:
                            price = common.formatprice(
                                cost, markup_price_colony)
                        else:
                            price = common.formatprice(cost, markup_price)

                        if 'Old World Weavers' in product.manufacturer or 'Grey Watkins' in product.manufacturer or 'Hinson' in product.manufacturer:
                            priceTrade = common.formatprice(cost, markup_trade)
                        else:
                            priceTrade = common.formatprice(
                                cost, markup_trade_european)
                except:
                    debug("Scalamandre", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                csr.execute("CALL CreateProduct ({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{})".format(
                    sq(product.sku),
                    sq(name),
                    sq(product.manufacturer),
                    sq(product.mpn),
                    sq(desc),
                    sq(title),
                    sq(description),
                    sq(product.ptype),
                    sq(vname),
                    hassample,
                    cost,
                    price,
                    priceTrade,
                    priceSample,
                    sq(product.pattern),
                    sq(product.color),
                    product.minimum,
                    sq(product.increment),
                    sq(product.uom),
                    sq(product.usage),
                    sq(product.collection),
                    sq(str(gtin)),
                    weight
                ))
                con.commit()

            except Exception as e:
                print(e)
                print(product.sku)
                continue

            try:
                productId = shopify.NewProductBySku(product.sku, con)
                if productId == None:
                    continue

                product.productId = productId
                product.save()

                self.downloadImage(product.mpn, productId)

                debug("Scalamandre", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Scalamandre.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Scalamandre", 1,
                          "No product Image for MPN: {}".format(product.mpn))
                    continue

                name = " | ".join((product.brand, product.pattern,
                                  product.color, product.ptype))
                title = " ".join((product.brand, product.pattern,
                                 product.color, product.ptype))
                description = title
                vname = title
                hassample = 1
                gtin = ""
                weight = 1

                desc = ""
                if product.description != None and product.description != "":
                    desc += "{}<br/><br/>".format(
                        product.description)
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.pieceSize != None and product.pieceSize != "" and product.ptype == "Pillow":
                    desc += "Meassurement: {}<br/>".format(product.pieceSize)
                else:
                    if product.width != None and product.width != "":
                        desc += "Width: {}<br/>".format(product.width)
                    if product.height != None and product.height != "":
                        desc += "Height: {}<br/>".format(product.height)
                    if product.hr != None and product.hr != "":
                        desc += "Horizontal Repeat: {}<br/>".format(product.hr)
                    if product.vr != None and product.vr != "":
                        desc += "Vertical Repeat: {}<br/>".format(product.vr)
                if product.rollLength != None and product.rollLength != "" and product.rollLength != 0 and product.uom == "Per Roll":
                    desc += "Roll Length: {} yds<br/>".format(
                        product.rollLength)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/>".format(product.feature)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    if product.ptype == "Pillow":
                        price = common.formatprice(cost, markup_price_pillow)
                        priceTrade = common.formatprice(
                            cost, markup_trade_pillow)
                    else:
                        if "Colony" in product.manufacturer:
                            price = common.formatprice(
                                cost, markup_price_colony)
                        else:
                            price = common.formatprice(cost, markup_price)

                        if 'Old World Weavers' in product.manufacturer or 'Grey Watkins' in product.manufacturer or 'Hinson' in product.manufacturer:
                            priceTrade = common.formatprice(cost, markup_trade)
                        else:
                            priceTrade = common.formatprice(
                                cost, markup_trade_european)
                except:
                    debug("Scalamandre", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                csr.execute("CALL CreateProduct ({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{})".format(
                    sq(product.sku),
                    sq(name),
                    sq(product.manufacturer),
                    sq(product.mpn),
                    sq(desc),
                    sq(title),
                    sq(description),
                    sq(product.ptype),
                    sq(vname),
                    hassample,
                    cost,
                    price,
                    priceTrade,
                    priceSample,
                    sq(product.pattern),
                    sq(product.color),
                    product.minimum,
                    sq(product.increment),
                    sq(product.uom),
                    sq(product.usage),
                    sq(product.collection),
                    sq(str(gtin)),
                    weight
                ))
                con.commit()

            except Exception as e:
                print(e)
                continue

            try:
                productId = product.productId

                csr.execute(
                    "CALL AddToPendingUpdateProduct ({})".format(productId))
                con.commit()

                self.downloadImage(product.mpn, productId)

                debug("Scalamandre", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Scalamandre');""")

        rows = csr.fetchall()
        for row in rows:
            productId = row[0]
            shopifyProduct = ShopifyProduct.objects.get(
                productId=productId)

            pv1 = shopifyProduct.variants.filter(
                isDefault=1).values('cost', 'price')[0]
            pv2 = shopifyProduct.variants.filter(
                name__startswith="Trade - ").values('price')[0]

            oldCost = pv1['cost']
            oldPrice = pv1['price']
            oldTradePrice = pv2['price']

            try:
                product = Scalamandre.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Scalamandre", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                if product.ptype == "Pillow":
                    newPrice = common.formatprice(newCost, markup_price_pillow)
                    newPriceTrade = common.formatprice(
                        newCost, markup_trade_pillow)
                else:
                    if "Colony" in product.manufacturer:
                        newPrice = common.formatprice(
                            newCost, markup_price_colony)
                    else:
                        newPrice = common.formatprice(newCost, markup_price)

                    if 'Old World Weavers' in product.manufacturer or 'Grey Watkins' in product.manufacturer or 'Hinson' in product.manufacturer:
                        newPriceTrade = common.formatprice(
                            newCost, markup_trade)
                    else:
                        newPriceTrade = common.formatprice(
                            newCost, markup_trade_european)
            except:
                debug("Scalamandre", 1,
                      "Price Error: SKU: {}".format(product.sku))
                continue

            if newPrice < 19.99:
                newPrice = 19.99
                newPriceTrade = 16.99

            if float(oldCost) != float(newCost) or float(oldPrice) != float(newPrice) or float(oldTradePrice) != float(newPriceTrade):
                try:
                    csr.execute("CALL UpdatePriceAndTrade ({}, {}, {}, {})".format(
                        shopifyProduct.productId, newCost, newPrice, newPriceTrade))
                    con.commit()

                    csr.execute(
                        "CALL AddToPendingUpdatePrice ({})".format(shopifyProduct.productId))
                    con.commit()
                except Exception as e:
                    print(e)
                    continue

                debug("Scalamandre", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Scalamandre", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Scalamandre'")
        con.commit()

        products = Scalamandre.objects.all()

        for product in products:
            sku = product.sku
            stock = product.stock
            stockText = product.stockText

            try:
                if stockText != "":
                    if product.ptype == "Pillow":
                        csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Scalamandre')".format(
                            sku, stock, "2-3 Weeks (Custom Order)"))
                        con.commit()
                    else:
                        csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Scalamandre')".format(
                            sku, stock, stockText))
                        con.commit()
                else:
                    csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Scalamandre')".format(
                        sku, stock, "Contact Customer Service to check stock."))
                    con.commit()
                debug("Scalamandre", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug("Scalamandre", 2,
                      "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Scalamandre.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors
            ptype = product.ptype
            size = product.pieceSize

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(category)))
                con.commit()

                debug("Scalamandre", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("Scalamandre", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("Scalamandre", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

            if size != None and size != "" and ptype == "Pillow":
                csr.execute("CALL AddToEditSize ({}, {})".format(
                    sq(sku), sq(size)))
                con.commit()

                debug("Scalamandre", 0,
                      "Added Size. SKU: {}, Size: {}".format(sku, sq(size)))

        csr.close()
        con.close()

    def downloadImage(self, mpn, productId):
        try:
            r = requests.get("{}/ScalaFeedAPI/FetchImagesByItemID?ITEMID={}".format(API_ADDRESS, mpn),
                             headers={'Authorization': 'Bearer {}'.format(API_TOKEN)})
            images = json.loads(r.text)
        except:
            return

        roomId = 1
        for image in images:
            if "MAIN" in image['IMAGETYPE'] and image['IMAGEPATH'] != "":
                common.picdownload2(
                    str(image['IMAGEPATH']).strip(), "{}.jpg".format(productId))

            else:
                roomId += 1
                common.roomdownload(
                    str(image['IMAGEPATH']).strip(), "{}_{}.jpg".format(productId, roomId))

    def fixMissingImages(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()
        hasImage = []
        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = 'Scalamandre'")
        for row in csr.fetchall():
            hasImage.append(row[0])

        products = Scalamandre.objects.all()

        for product in products:
            if product.productId == None or product.productId == "":
                continue

            if int(product.productId) in hasImage:
                continue

            # Image API
            try:
                r = requests.get("{}/ScalaFeedAPI/FetchImagesByItemID?ITEMID={}".format(API_ADDRESS, product.mpn),
                                 headers={'Authorization': 'Bearer {}'.format(API_TOKEN)})
                images = json.loads(r.text)
            except:
                return

            roomId = 1
            for image in images:
                if "MAIN" in image['IMAGETYPE'] and image['IMAGEPATH'] != "":
                    common.picdownload2(
                        str(image['IMAGEPATH']).strip(), "{}.jpg".format(product.productId))

                else:
                    roomId += 1
                    common.roomdownload(
                        str(image['IMAGEPATH']).strip(), "{}_{}.jpg".format(product.productId, roomId))
