from django.core.management.base import BaseCommand
from brands.models import Pindler
from shopify.models import Product as ShopifyProduct

import os
import sys
import pymysql
import requests
import csv
import codecs

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.pindler
markup_trade = markup.pindler_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Pindler Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "getProductIds" in options['functions']:
            self.getProductIds()

        if "addNew" in options['functions']:
            self.addNew()

        if "updateExisting" in options['functions']:
            self.updateExisting()

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "updateSizeTags" in options['functions']:
            self.updateSizeTags()

        if "fixMissingImages" in options['functions']:
            self.fixMissingImages()

        if "main" in options['functions']:
            self.getProducts()
            self.getProductIds()

    def downloadcsv(self):
        debug("Pindler", 0, "Download New Master CSV from Pinidler FTP")

        r = requests.get(
            "https://trade.pindler.com/dataexport/DecoratorBest/DECORBEST.csv", auth=("decorbest", "pnp$7175"))

        if r.status_code == 200:
            with open(FILEDIR + '/files/pindler-master.csv', "wb") as out:
                for bits in r.iter_content():
                    out.write(bits)

            debug("Pindler", 0, "Pindler FTP Master CSV File Download Completed")
            return True
        else:
            debug("Pindler", 2, "Failed New Master CSV from Pindler Trade Portal")
            return False

    def getProducts(self):
        if not self.downloadcsv():
            sys.exit(2)

        s = requests.Session()

        Pindler.objects.all().delete()

        f = open(FILEDIR + "/files/pindler-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        index = 0
        for row in cr:
            index += 1
            if index == 1:
                continue

            try:
                brand = "Pindler"
                mpn = row[0]

                try:
                    Pindler.objects.get(mpn=mpn)
                    continue
                except Pindler.DoesNotExist:
                    pass

                sku = "PDL " + row[20] + "-" + row[18]
                sku = sku.replace("'", "")

                book = ""
                if row[1] != "":
                    book = row[1]
                elif row[3] != "":
                    book = row[3]

                cost = float(row[25])
                pattern = row[19]
                color = row[18]
                width = row[26]
                content = row[4]
                hr = row[9]
                vr = row[24]

                if row[20].find("T") >= 0:
                    ptype = "Trim"
                else:
                    ptype = "Fabric"

                uom = "Per Yard"

                colors = str(row[12]).strip()

                keywords = " ".join(
                    [row[12], row[13], row[14], row[15], row[16], row[17]])

                piclink = row[10]

                if keywords.find("UPHOLSTERY") >= 0:
                    usage = "Upholstery"
                elif keywords.find("DRAPERY") >= 0:
                    usage = "Drapery"
                elif ptype == "Trim":
                    usage = "Trimming"
                else:
                    usage = "Fabric"

                manufacturer = "{} {}".format(brand, ptype)

                Pindler.objects.create(
                    mpn=mpn,
                    sku=sku,
                    collection=book,
                    pattern=pattern,
                    color=color,
                    manufacturer=manufacturer,
                    content=content,
                    colors=colors,
                    ptype=ptype,
                    brand=brand,
                    uom=uom,
                    usage=usage,
                    category=keywords,
                    style=keywords,
                    width=width,
                    hr=hr,
                    vr=vr,
                    cost=cost,
                    thumbnail=piclink,
                )

                debug("Pindler", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("Pindler", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Pindler');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Pindler.objects.get(sku=sku)
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
                        "Pindler", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Pindler", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Pindler.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Pindler", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Pindler", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Pindler.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Pindler", 1,
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
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.width != None and product.width != "":
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {} ft<br/>".format(product.height)
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)
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
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)

                    if product.map > 0:
                        price = common.formatprice(product.map, 1)
                except:
                    debug("Pindler", 2, "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                increment = ""
                if product.increment != None:
                    increment = product.increment

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
                    sq(increment),
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

                debug("Pindler", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Pindler.objects.all()
        products = Pindler.objects.filter(productId='6864031514670')

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Pindler", 1,
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
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.width != None and product.width != "":
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {} ft<br/>".format(product.height)
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)
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
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)

                    if product.map > 0:
                        price = common.formatprice(product.map, 1)
                except:
                    debug("Pindler", 2, "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                increment = ""
                if product.increment != None:
                    increment = product.increment

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
                    sq(increment),
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

                if product.thumbnail and product.thumbnail.strip() != "":
                    try:
                        common.picdownload2(
                            product.thumbnail, "{}.jpg".format(productId))
                    except:
                        pass

                debug("Pindler", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Pindler');""")

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
                product = Pindler.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Pindler", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            map = product.map
            try:
                newPrice = common.formatprice(newCost, markup_price)
                newPriceTrade = common.formatprice(newCost, markup_trade)

                if product.map > 0:
                    newPrice = common.formatprice(map, 1)
            except:
                debug("Pindler", 2, "Price Error: SKU: {}".format(product.sku))
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

                debug("Pindler", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Pindler", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Pindler.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors
            collection = product.collection

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(category)))
                con.commit()

                debug("Pindler", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("Pindler", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("Pindler", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

            if collection != None and collection != "":
                csr.execute("CALL AddToEditCollection ({}, {})".format(
                    sq(sku), sq(collection)))
                con.commit()

                debug("Pindler", 0, "Added Collection. SKU: {}, Collection: {}".format(
                    sku, sq(collection)))

        csr.close()
        con.close()

    def updateSizeTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Pindler.objects.all()
        for product in products:
            sku = product.sku
            ptype = product.ptype
            width = product.width

            if width != None and width != "" and ptype == "Trim":
                try:
                    width = float(str(width).replace('"', ''))
                except:
                    continue

                if width == 0:
                    continue

                widthTag = '5" and More'
                if width < 1:
                    widthTag = 'Up to 1"'
                if width >= 1 and width < 2:
                    widthTag = '1" to 2"'
                if width >= 2 and width < 3:
                    widthTag = '2" to 3"'
                if width >= 3 and width < 4:
                    widthTag = '3" to 4"'
                if width >= 4 and width < 5:
                    widthTag = '4" to 5"'

                csr.execute("CALL AddToEditSize ({}, {})".format(
                    sq(sku), sq(widthTag)))
                con.commit()

                debug("Pindler", 0,
                      "Added Width. SKU: {}, Width: {}, Width Tag: {}".format(sku, width, widthTag))

        csr.close()
        con.close()

    def fixMissingImages(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()
        hasImage = []
        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = 'Pindler'")
        for row in csr.fetchall():
            hasImage.append(row[0])

        products = Pindler.objects.all()
        for product in products:
            if product.productId == None:
                continue

            if int(product.productId) in hasImage:
                continue

            if product.thumbnail and product.thumbnail.strip() != "":
                try:
                    common.picdownload2(
                        product.thumbnail, "{}.jpg".format(product.productId))
                except:
                    pass

        csr.close()
        con.close()
