from unicodedata import category
from django.core.management.base import BaseCommand
from brands.models import Kasmir
from shopify.models import Product as ShopifyProduct

import os
import time
import pymysql
import sys
import xlrd
import urllib.request

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.kasmir
markup_trade = markup.kasmir_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Kasmir Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "getProductIds" in options['functions']:
            self.getProductIds()

        if "addNew" in options['functions']:
            self.addNew()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "updateStock" in options['functions']:
            self.updateStock()

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "fixMissingImages" in options['functions']:
            self.fixMissingImages()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updatePrice()
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def downloadcsv(self):
        try:
            urllib.request.urlretrieve(
                "ftp://226022:Ashley1!@65.98.183.71/Current-Inventory_Int.xls", FILEDIR + "/files/kasmir-master.xls")
        except Exception as e:
            debug("Kasmir", 2, "Download Failed. Exiting")
            print(e)
            return False

        debug("Kasmir", 0, "Download Completed")
        return True

    def getProducts(self):
        if not self.downloadcsv():
            sys.exit(2)

        Kasmir.objects.all().delete()

        wb = xlrd.open_workbook(FILEDIR + "/files/kasmir-master.xls")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                row = sh.row_values(i)

                pattern = str(row[0]).strip()
                if "BOOKPATTERN" == pattern.upper() or "ALCANTARA" in pattern.upper():
                    continue
                color = str(row[1]).strip()
                mpn = pattern + "/" + color
                sku = "KM " + mpn
                brand = "Kasmir"
                ptype = "Fabric"

                vr = str(row[5]).strip()
                if "N/A" == vr:
                    vr = ""

                hr = str(row[6]).strip()
                if "N/A" == hr:
                    hr = ""

                uom = "Per Yard"

                width = str(row[3]).strip() + " inches"
                price = float(str(row[2]).replace("$", "").strip()) / 2
                collection = str(int(row[25]))
                content = str(row[26]).strip()
                usage = str(row[56]).strip()
                if usage == "":
                    usage = "Fabric"
                picLoc = "https://www.kasmirfabricsonline.com/sampleimages/Large/{}".format(
                    str(row[57]).replace(' ', '%20').strip())
                if "ImageComingSoon.jpg" == picLoc:
                    picLoc = ""

                try:
                    style = str(row[54]).strip()
                except:
                    style = ""
                    pass

                try:
                    construction = str(row[55]).strip()
                except:
                    construction = ""
                    pass

                try:
                    stock = int(row[58])
                except:
                    stock = 0

                manufacturer = "{} {}".format(brand, ptype)

                try:
                    Kasmir.objects.get(mpn=mpn)
                    continue
                except Kasmir.DoesNotExist:
                    pass

                # Tagging
                keywords = "{}, {}".format(style, construction)

                Kasmir.objects.create(
                    mpn=mpn,
                    sku=sku,
                    collection=collection,
                    pattern=pattern,
                    color=color,
                    manufacturer=manufacturer,
                    content=content,
                    construction=construction,
                    colors=color,
                    ptype=ptype,
                    brand=brand,
                    uom=uom,
                    usage=usage,
                    style=keywords,
                    category=keywords,
                    width=width,
                    hr=hr,
                    vr=vr,
                    cost=price,
                    thumbnail=picLoc,
                    stock=stock
                )

                debug("Kasmir", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("Kasmir", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Kasmir');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Kasmir.objects.get(sku=sku)
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
                        "Kasmir", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Kasmir", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Kasmir.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Kasmir", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Kasmir", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Kasmir.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Kasmir", 1,
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
                    desc += "Width: {}<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {}<br/>".format(product.height)
                if product.rollLength != None and product.rollLength != "":
                    desc += "Roll Length: {}<br/>".format(product.rollLength)
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {}<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {}<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.construction != None and product.construction != "":
                    desc += "Construction: {}<br/>".format(
                        product.construction)
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
                        priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Kasmir", 2, "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                increment = ""
                if product.increment != None and product.increment != "":
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

                debug("Kasmir", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Kasmir.objects.all()
        for product in products:
            sku = product.sku

            category = product.style
            style = product.style
            colors = product.colors

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(category)))
                con.commit()

                debug("Kasmir", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("Kasmir", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("Kasmir", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

        csr.close()
        con.close()

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Kasmir'")
        con.commit()

        products = Kasmir.objects.all()

        for product in products:
            sku = product.sku
            stock = product.stock

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Kasmir')".format(
                    sku, stock, ""))
                con.commit()
                debug("Kasmir", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug("Kasmir", 1,
                      "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Kasmir');""")

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
                product = Kasmir.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Kasmir", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(newCost, markup_price)
                newPriceTrade = common.formatprice(newCost, markup_trade)

                if product.map > 0:
                    newPrice = common.formatprice(product.map, 1)
            except:
                debug("Kasmir", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("Kasmir", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Kasmir", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def fixMissingImages(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        hasImage = []

        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = 'Kasmir'")
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        products = Kasmir.objects.all()
        for product in products:
            if product.productId == None or product.productId in hasImage:
                continue

            if product.thumbnail and product.thumbnail.strip() != "":
                debug("Kasmir", 0, "Product productID: {} is missing pic. downloading from {}".format(
                    product.productId, product.thumbnail))

                try:
                    common.picdownload2(
                        product.thumbnail, "{}.jpg".format(product.productId))
                except Exception as e:
                    print(e)

        csr.close()
        con.close()
