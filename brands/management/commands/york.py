import environ
from library import debug, common,  shopify, markup
from django.core.management.base import BaseCommand
from brands.models import York
from shopify.models import Product as ShopifyProduct

import os
import pymysql
import paramiko
import requests
import json
import time
import sys
import xlrd
from shutil import copyfile

import urllib.request

opener = urllib.request.build_opener()
opener.addheaders = [
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)

env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.york
markup_trade = markup.york_trade  # MSRP

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_BASE_URL = "http://yorkapi.yorkwall.com:10090/pcsiapi"  # 206.41.194.97


class Command(BaseCommand):
    help = 'Build York Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "testAPI" in options['functions']:
            self.testAPI()

        if "getProductIds" in options['functions']:
            self.getProductIds()

        if "addNew" in options['functions']:
            self.addNew()

        if "updateExisting" in options['functions']:
            self.updateExisting()

        if "image" in options['functions']:
            self.image()

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "updateStock" in options['functions']:
            self.updateStock()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "quickship" in options['functions']:
            self.quickship()

        if "bestSellers" in options['functions']:
            self.bestSellers()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updateStock()

                print("Finished Updating Inventory. Waiting for next run.")
                time.sleep(86400)

    def testAPI(self):
        testType = "product"
        testMPN = "HA1326"

        req = requests.get(
            "{}/{}.php/{}".format(API_BASE_URL, testType, testMPN))
        res = json.loads(req.text)
        print(res)

    def getProducts(self):
        York.objects.all().delete()

        try:
            reqCollections = requests.get(
                "{}/collections.php".format(API_BASE_URL))
            resCollections = json.loads(reqCollections.text)
            collections = resCollections['results']
        except Exception as e:
            sys.exit(1)

        for collection in collections:
            collectionID = collection['collectionID']
            collectionName = collection['name']

            if collectionID == "":
                continue

            debug("York", 0, "Processing Collection ID: {}, Name: {}".format(
                collectionID, collectionName))

            reqCollection = requests.get(
                "{}/collection.php/{}".format(API_BASE_URL, collectionID))
            resCollection = json.loads(reqCollection.text)
            products = resCollection['results']

            for product in products:
                productID = product['productID']
                productName = product['description']

                debug("York", 0, "Processing Product ID: {}, Name: {}".format(
                    productID, productName))

                try:
                    reqProduct = requests.get(
                        "{}/product.php/{}".format(API_BASE_URL, productID))
                    resProduct = json.loads(reqProduct.text)
                    row = resProduct['results'][0]
                except Exception as e:
                    print(e)
                    debug("York", 1, "Error ID: {}, Name: {}".format(
                        productID, productName))
                    continue

                brand = str(row['CategoryName']).strip()
                brandID = str(row['CategoryNumber']).strip()

                # 4/24 Bug fix - York collection name error
                collectionName = str(row['CollectionName']).strip()

                if brand == "Ron Redding Designs":
                    brand = "Ronald Redding Designs"
                if brand == "Inspired by Color":
                    brand = "York"
                if brand == "Florance Broadhurst":
                    brand = "Florence Broadhurst"
                if brand == "York Style Makers":
                    brand = "York Stylemakers"
                if brand == "YorkPa":
                    brand = "York"
                if brand == "Cary Lind Designs":
                    brand = "Carey Lind Designs"
                if brand == "York Designers Series":
                    brand = "York Designer Series"
                if "RoomMates" in collectionName:
                    brand = "RoomMates"

                if "Rifle Paper Co." in collectionName:  # 11/29 request from Barbara. Set Rifle collection to brand
                    brand = "Rifle Paper Co."

                # 4/6/22 from Barbara. Set Dazzling Dimensions and Bohemian Luxe collections to Antonina Vella Brand
                if "Dazzling Dimensions" in collectionName or "Bohemian Luxe" in collectionName:
                    brand = "Antonina Vella"

                try:
                    mpn = int(row['VendorItem#'])
                except:
                    mpn = str(row['VendorItem#'])

                sku = "YORK {}".format(mpn)

                try:
                    York.objects.get(mpn=mpn)
                    debug("York", 1, "Duplicated MPN: {}, Brand: {}".format(mpn, brand))
                    continue
                except York.DoesNotExist:
                    pass

                pattern = str(row['ProductName']).replace(
                    "Wallpaper", "").replace("  ", "").replace("\"", "").strip()
                color = str(row['Color']).replace(
                    ", ", "/").replace("\"", "").strip()

                pattern = pattern.title()
                color = color.title()
                try:
                    York.objects.get(pattern=pattern, color=color)
                    debug("York", 1, "Duplicated MPN: {}, Brand: {}".format(mpn, brand))
                    continue
                except York.DoesNotExist:
                    pass

                uomText = str(row['UOM'])
                if "YARD" in uomText:
                    uom = "Per Yard"
                elif "EACH" in uomText:
                    uom = "Per Each"
                elif "SPOOL" in uomText:
                    uom = "Per Spool"
                elif "ROLL" in uomText:
                    uom = "Per Roll"
                else:
                    debug("York", 1, "UOM error for MPN: {}".format(mpn))
                    continue

                try:
                    minimum = int(row['OrderIncrement'])
                except:
                    minimum = 2

                increment = ""
                if minimum > 1:
                    increment = ",".join([str(ii * minimum)
                                          for ii in range(1, 26)])

                cost = float(row['DECBESTPRICE'])
                msrp = float(row['MSRP'])
                try:
                    map = float(row['NewMap'])
                except:
                    map = 0
                if msrp < 13:
                    continue

                repeat = ""
                if str(row['PatternRepeat']) != "" and str(row['PatternRepeat']) != "None":
                    repeat += str(row['PatternRepeat'])
                if str(row['PatternRepeatCM']) != "" and str(row['PatternRepeatCM']) != "None":
                    repeat += " / " + str(row['PatternRepeatCM'])

                match = str(row['Match'])
                style = str(row['Substrate'])
                category = str(row['Theme'])

                if str(row['AdvertisingCopyIII']) != "":
                    description = str(row['AdvertisingCopyIII'])
                else:
                    description = str(row['AdvertisingCopy'])

                dimension = ""
                if str(row['ProductDimension']) != "" and str(row['ProductDimension']) != "None":
                    dimension += str(row['ProductDimension'])
                if str(row['ProductDimensionMetric']) != "" and str(row['ProductDimensionMetric']) != "None":
                    dimension += " / " + str(row['ProductDimensionMetric'])

                weight = 1

                feature = str(row['KeyFeatures'])

                ptype = "Wallpaper"
                usage = "Wallcovering"

                manufacturer = "{} {}".format(brand, ptype)

                # Status
                status = True
                statusText = row['SKUStatus']

                quickship = False
                if row['QuickShip'] == 'Y':
                    quickship = True

                try:
                    reqStock = requests.get(
                        "{}/stock.php/{}".format(API_BASE_URL, mpn))
                    resStock = json.loads(reqStock.text)
                    stock = int(resStock["results"][0]["amount"])
                except:
                    stock = 0

                # Tagging
                keywords = "{}, {}, {}, {}, {}".format(
                    collectionName, category, style, description, feature)

                York.objects.create(
                    mpn=mpn,
                    sku=sku,
                    collection_num=collectionID,
                    collection=collectionName,
                    brand_num=brandID,
                    brand=brand,
                    pattern=pattern,
                    color=color,
                    manufacturer=manufacturer,
                    colors=color,
                    ptype=ptype,
                    uom=uom,
                    usage=usage,
                    category=keywords,
                    style=keywords,
                    dimension=dimension,
                    weight=weight,
                    repeat=repeat,
                    match=match,
                    feature=feature,
                    description=description,
                    cost=cost,
                    msrp=msrp,
                    map=map,
                    minimum=minimum,
                    increment=increment,
                    stock=stock,
                    status=status,
                    statusText=statusText,
                    quickship=quickship,
                )

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'York');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = York.objects.get(sku=sku)
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
                        "York", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "York", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except York.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "York", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("York", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = York.objects.all()

        for product in products:
            try:
                if product.productId != None:
                    continue

                name = " | ".join((product.brand, product.pattern,
                                  product.color, product.ptype))
                title = " ".join((product.brand, product.pattern,
                                 product.color, product.ptype))
                description = title
                vname = title
                hassample = 1
                gtin = ""
                weight = product.weight

                desc = ""
                if product.description != None and product.description != "":
                    desc += "{}<br/><br/>".format(
                        product.description)
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.dimension != None and product.dimension != "":
                    desc += "Roll Dimensions: {}<br/>".format(
                        product.dimension)
                if product.repeat != None and product.repeat != "":
                    desc += "Repeat: {}<br/>".format(product.repeat)
                if product.rollLength != None and product.rollLength != "":
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} in.<br/>".format(
                            product.rollLength)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.match != None and product.match != "":
                    desc += "Match: {}<br/>".format(product.match)
                if product.feature != None and product.feature != "":
                    desc += "Feature: {}<br/>".format(product.feature)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    if product.map != None and float(product.map) > 0:
                        price = common.formatprice(product.map, 1)
                    else:
                        price = common.formatprice(cost, markup_price)

                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("York", 2, "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                if product.collection != None and product.collection != "":
                    csr.execute("CALL AddToProductCollection ({}, {})".format(
                        sq(product.sku), sq(product.collection)))
                    con.commit()

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
                productId = shopify.NewProductBySku(product.sku, con)
                if productId == None:
                    continue

                product.productId = productId
                product.save()

                debug("York", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # products = York.objects.all()
        products = York.objects.filter(collection="Greenhouse")

        for product in products:
            try:
                if product.productId == None:
                    continue

                name = " | ".join((product.brand, product.pattern,
                                  product.color, product.ptype))
                title = " ".join((product.brand, product.pattern,
                                 product.color, product.ptype))
                description = title
                vname = title
                hassample = 1
                gtin = ""
                weight = product.weight

                desc = ""
                if product.description != None and product.description != "":
                    desc += "{}<br/><br/>".format(
                        product.description)
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.dimension != None and product.dimension != "":
                    desc += "Roll Dimensions: {}<br/>".format(
                        product.dimension)
                if product.repeat != None and product.repeat != "":
                    desc += "Repeat: {}<br/>".format(product.repeat)
                if product.rollLength != None and product.rollLength != "":
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} in.<br/>".format(
                            product.rollLength)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.match != None and product.match != "":
                    desc += "Match: {}<br/>".format(product.match)
                if product.feature != None and product.feature != "":
                    desc += "Feature: {}<br/>".format(product.feature)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    if product.map != None and float(product.map) > 0:
                        price = common.formatprice(product.map, 1)
                    else:
                        price = common.formatprice(cost, markup_price)

                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("York", 2, "Price Error: SKU: {}".format(product.sku))
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

                debug("York", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'York');""")

        rows = csr.fetchall()
        for row in rows:
            try:
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
            except Exception as e:
                print(e)
                continue

            try:
                product = York.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("York", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                if product.map != None and float(product.map) > 0:
                    newPrice = common.formatprice(product.map, 1)
                else:
                    newPrice = common.formatprice(newCost, markup_price)

                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("York", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("York", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("York", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def downloadcsv(self):
        debug("York", 0, "Download New Inventory File from York FTP")

        host = "34.203.121.151"
        port = 22
        username = "york"
        password = "York123Decbest!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("York", 2, "Connection to York FTP Server Failed")
            return False

        try:
            sftp.get("/york/DecBest Inventory.xlsx", FILEDIR +
                     '/files/york-inventory.xlsx')
            sftp.close()
        except Exception as e:
            print(e)
            debug("York", 1, "No Inventory File")
            return

        debug("York", 0, "York FTP Inventory Download Completed")
        return True

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'York'")
        con.commit()

        products = York.objects.all()

        for product in products:
            sku = product.sku
            stock = product.stock

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 2, '{}', 'York')".format(
                    sku, stock, ""))
                con.commit()
                debug("York", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug("York", 2,
                      "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = York.objects.all()
        for product in products:
            sku = product.sku

            category = product.category + "-" + product.feature
            style = product.style
            colors = product.colors
            subtypes = ""

            if "mural" in product.pattern.lower():
                subtypes = "Murals"

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(str(category).strip())))
                con.commit()

                debug("York", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(str(style).strip())))
                con.commit()

                debug("York", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(str(colors).strip())))
                con.commit()

                debug("York", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

            if subtypes != None and subtypes != "":
                csr.execute("CALL AddToEditSubtype ({}, {})".format(
                    sq(sku), sq(str(subtypes).strip())))
                con.commit()

                debug("York", 0,
                      "Added Subtype. SKU: {}, Subtype: {}".format(sku, sq(subtypes)))

        csr.close()
        con.close()

    def image(self):
        fnames = os.listdir(FILEDIR + "/files/images/york/")
        print(fnames)
        for fname in fnames:
            try:
                if "_" in fname:
                    mpn = fname.split("_")[0]

                    product = York.objects.get(mpn=mpn)
                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "/files/images/york/" + fname, FILEDIR +
                                 "/../../images/roomset/{}_2.jpg".format(productId))
                else:
                    mpn = fname.split(".")[0]
                    product = York.objects.get(mpn=mpn)
                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "/files/images/york/" + fname, FILEDIR +
                                 "/../../images/product/{}.jpg".format(productId))

                os.remove(FILEDIR + "/files/images/york/" + fname)
            except:
                continue

    def quickship(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = York.objects.all()

        # Get Current York QuickShip products and add to pending update tag queue
        csr.execute("""SELECT ProductID FROM Product P 
                    LEFT JOIN ProductTag PT ON P.SKU = PT.SKU
                    WHERE 
                        PT.TagID = 31 AND 
                        PT.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'York');""")
        rows = csr.fetchall()
        for row in rows:
            productId = row[0]
            print(productId)
            csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                productId))
            con.commit()

        # Delete All York Quickship products from PT
        csr.execute("""DELETE FROM ProductTag
                    WHERE 
                        TagID = 31 AND 
                        SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'York');""")
        con.commit()

        # Freshly re-add quickship products
        for product in products:
            if product.quickship:
                csr.execute("CALL AddToProductTag ({}, {})".format(
                    sq(product.sku), sq("Quick Ship")))
                con.commit()

                csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                    product.productId))
                con.commit()

                debug('York', 0, "Added to Quick Ship. SKU: {}".format(product.sku))

        csr.close()
        con.close()

    def bestSellers(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        wb = xlrd.open_workbook(FILEDIR + "/files/york-bestsellers.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                mpn = str(sh.cell_value(i, 0))
            except:
                continue

            try:
                product = York.objects.get(mpn=mpn)
            except York.DoesNotExist:
                continue

            csr.execute("CALL AddToProductTag ({}, {})".format(
                sq(product.sku), sq("Best Selling")))
            con.commit()

            csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                product.productId))
            con.commit()

            debug('York', 0, "Added to Best selling. SKU: {}".format(product.sku))

        csr.close()
        con.close()
