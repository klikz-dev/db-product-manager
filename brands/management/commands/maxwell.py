from django.core.management.base import BaseCommand
from brands.models import Maxwell
from shopify.models import Product as ShopifyProduct

import requests
import json
import pymysql
import time
import os
from shutil import copyfile

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.maxwell
markup_trade = markup.maxwell_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MXURL = 'https://distribution.pdfsystems.com'
APIKEY = '286d17936503cc7c82de30e4c4721a67'
HEADERS = {'x-api-key': APIKEY}


class Command(BaseCommand):
    help = 'Build Maxwell Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "getProductIds" in options['functions']:
            self.getProductIds()

        if "addNew" in options['functions']:
            self.addNew()

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "roomset" in options['functions']:
            self.roomset()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updatePrice()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def getProducts(self):
        Maxwell.objects.all().delete()

        for page in range(1, 30):
            reqList = requests.get(
                "{}/api/simple/item/list?count=1000&page={}".format(MXURL, str(page)), headers=HEADERS)
            resList = json.loads(reqList.text)

            for i in range(0, len(resList)):
                brand = "Maxwell"
                mpn = resList[i]['sku']
                sku = "MW {}".format(mpn)

                try:
                    Maxwell.objects.get(mpn=mpn)
                    continue
                except Maxwell.DoesNotExist:
                    pass

                req = requests.get(
                    "{}/api/simple/item/lookup?sku={}".format(MXURL, mpn), headers=HEADERS)
                try:
                    res = json.loads(req.text)
                except:
                    continue

                pattern = res['style']
                color = res['color']

                ptype = ""
                try:
                    collection = res['books'][len(res['books']) - 1]
                except:
                    collection = ''

                description = ""
                try:
                    width = res['width'].split("X")[0]
                except:
                    width = ""
                try:
                    height = res['width'].split("X")[1]
                except:
                    height = ""
                if res['repeat'] != None:
                    vr = res['repeat'].split(" ")[0]
                    try:
                        hr = res['repeat'].split(" ")[1]
                    except:
                        hr = ""
                else:
                    hr = ""
                    vr = ""
                content = res['content']
                if content == None:
                    content = ""
                feature = res['label_message']
                if feature == None:
                    feature = ""

                uom = ""
                try:
                    usage = res['grading']['USAGE'][0]
                except:
                    usage = ''
                minimum = 1
                increment = ""

                style = ""
                colors = ""
                category = res['product_category']

                cost = float(res['price'])
                msrp = 0
                map = 0

                try:
                    stock = int(res['inventory']['available'])
                except:
                    stock = 0
                if res['image_url'] == None or res['discontinued'] != None:
                    status = False
                else:
                    status = True

                if res['image_url'] != None:
                    thumbnail = res['image_url']
                else:
                    thumbnail = ""
                roomset = ""

                if "WALLPAPER" in category:
                    usage == "Wallpaper"
                    ptype = "Wallpaper"
                    uom = "Per Roll"
                else:
                    usage == "Fabric"
                    ptype = "Fabric"
                    uom = "Per Yard"

                manufacturer = "{} {}".format(brand, ptype)

                try:
                    Maxwell.objects.create(
                        mpn=mpn,
                        sku=sku,
                        pattern=pattern,
                        color=color,
                        brand=brand,
                        ptype=ptype,
                        manufacturer=manufacturer,
                        collection=collection,
                        description=description,
                        width=width,
                        height=height,
                        content=content,
                        hr=hr,
                        vr=vr,
                        feature=feature,
                        uom=uom,
                        usage=usage,
                        minimum=minimum,
                        increment=increment,
                        style=style,
                        colors=colors,
                        category=category,
                        cost=cost,
                        msrp=msrp,
                        map=map,
                        status=status,
                        stock=stock,
                        thumbnail=thumbnail,
                        roomset=roomset,
                        productId="",
                    )
                    debug(
                        "Maxwell", 0, "Success to get product details for MPN: {}".format(mpn))
                except Exception as e:
                    print(e)
                    debug(
                        "Maxwell", 2, "Failed to get product details for MPN: {}".format(mpn))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Maxwell');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Maxwell.objects.get(sku=sku)
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
                        "Maxwell", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Maxwell", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Maxwell.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Maxwell", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Maxwell", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Maxwell.objects.all()

        for product in products:
            try:
                if (product.productId != None and product.productId != "") or product.status == False:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Maxwell", 1,
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
                if product.width != None and product.width != "":
                    desc += "Width: {}<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {}<br/>".format(product.height)
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {}<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {}<br/>".format(product.vr)
                if product.rollLength != None and product.rollLength != "" and float(product.rollLength) != 0:
                    if "Yard" in product.uom:
                        pass
                    else:
                        desc += "Roll Length: {} yds<br/>".format(
                            product.rollLength)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Maxwell", 2,
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
                productId = shopify.NewProductBySku(product.sku, con)
                if productId == None:
                    continue

                product.productId = productId
                product.save()

                if product.thumbnail and product.thumbnail.strip() != "":
                    try:
                        common.picdownload2(
                            product.thumbnail, "{}.jpg".format(productId))
                    except:
                        pass

                debug("Maxwell", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Maxwell');""")

        rows = csr.fetchall()
        for row in rows:
            productId = row[0]
            shopifyProduct = ShopifyProduct.objects.get(productId=productId)

            pv1 = shopifyProduct.variants.filter(
                isDefault=1).values('cost', 'price')[0]
            pv2 = shopifyProduct.variants.filter(
                name__startswith="Trade - ").values('price')[0]

            oldCost = pv1['cost']
            oldPrice = pv1['price']
            oldTradePrice = pv2['price']

            try:
                product = Maxwell.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Maxwell", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(newCost, markup_price)
                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("Maxwell", 2,
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

                debug("Maxwell", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Maxwell", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Maxwell.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            color = product.colors

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("Maxwell", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if color != None and color != "":
                col = str(color).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("Maxwell", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

        csr.close()
        con.close()

    def roomset(self):
        fnames = os.listdir(FILEDIR + "/files/images/maxwell/")

        for fname in fnames:
            try:
                if "Maxwell-Fabrics_" in fname:
                    tmp = fname.replace("Maxwell-Fabrics_",
                                        "").replace(".jpg", "")
                    mpn = tmp.split("_")[0]
                    roomId = int(tmp.split("_")[1]) + 1

                    product = Maxwell.objects.get(mpn=mpn)
                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "/files/images/maxwell/" + fname, FILEDIR +
                                 "/../../images/roomset/{}_{}.jpg".format(productId, roomId))

                        debug("Maxwell", 0, "Roomset Image {}_{}.jpg".format(
                            productId, roomId))

                        os.remove(
                            FILEDIR + "/files/images/maxwell/" + fname)
                    else:
                        print("No product found with MPN: {}".format(mpn))
                else:
                    continue

            except Exception as e:
                print(e)
                continue
