import codecs
import csv
from django.core.management.base import BaseCommand
from brands.models import Stout
from shopify.models import Product as ShopifyProduct

import requests
import os
import xlrd
import json
import pymysql
import time
from ftplib import FTP_TLS

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = env('MYSQL_PORT')

markup_price = markup.stout
markup_trade = markup.stout_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRODUCT_LINK_LIST = ["https://www.estout.com/search/results?searchtype=f&pp=100&page=",
                     "https://www.estout.com/search/results?page=1&use=11&bknum=1258&pp=100", "https://www.estout.com/search/results?page=1&use=9&bknum=1602&pp=100"]
PRODUCT_LINK_LIST_T = ["Fabric", "Trim", "Wallpaper"]


class Command(BaseCommand):
    help = 'Build Stout Database'

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

        if "updateExisting" in options['functions']:
            self.updateExisting()

        if "updateStock" in options['functions']:
            self.updateStock()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updatePrice()
                self.updateStock()

                print("Completed. Waiting for next run")
                time.sleep(86400)

    def downloadcsv(self):
        try:
            ftps = FTP_TLS('www.estout.com')
            ftps.login('apiData', 'sbFtp3050')
            ftps.prot_p()
            ftps.retrlines('LIST')

            srcFile = 'onlineRetail.CSV'
            dstFile = open(FILEDIR + "/files/stout-master.csv", 'wb')

            ftps.retrbinary('RETR %s' % srcFile, dstFile.write)

            ftps.close()
        except Exception as e:
            debug("Stout", 1, "Download Failed. Exiting")
            print(e)
            return False

        return True

    def getProducts(self):
        if not self.downloadcsv():
            return

        Stout.objects.all().delete()

        s = requests.Session()
        r = s.post("https://www.estout.com/checklogin?ref=",
                   data={'un': "DecoratorsBest", 'pw': 'b1028h47ks'})

        if r.status_code != 200:
            return

        f = open(FILEDIR + "/files/stout-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        for row in cr:
            mpn = str(row[0])
            if mpn == 'ITEM-NUMBER':
                continue

            sku = "STOUT {}".format(mpn)
            plink = "https://www.stouttextiles.com/details?&sku={}".format(mpn)

            pattern = str(row[1]).split(" ")[0]
            color = str(row[8])

            cost = float(row[2])
            msrp = float(row[3])

            brand = "Stout"
            collection = str(row[19])

            width = float(str(row[4]).replace("in", "").strip())
            vr = float(str(row[5]))
            hr = float(str(row[6]))
            content = str(row[7]).replace(
                " ", ", ").replace("%", "% ")

            construction = str(row[10])
            style = str(row[11]).replace(
                " ", ", ")

            spec = str(row[12])
            finish = str(row[13])

            usage = str(row[14]).lower().capitalize()
            country = str(row[15])

            feature = "Construction: {}<br />Test Spec: {}<br />Finish: {}<br />Country: {}".format(
                construction, spec, finish, country)

            ptype = "Fabric"
            if "Trimming" in usage or "Trimming" in construction or "Trimming" in style:
                ptype = "Trim"
            if "Wallcovering" in usage or "Wallcovering" in construction or "Wallcovering" in style:
                ptype = "Wallpaper"

            manufacturer = "{} {}".format(brand, ptype)

            thumbnail = "https://cdn.estout.com/Images/{}.jpg".format(mpn)

            # Tagging
            keywords = "{}, {}".format(feature, style)

            try:
                Stout.objects.get(mpn=mpn)
                continue
            except Stout.DoesNotExist:
                pass

            product = Stout.objects.create(
                brand=brand,
                manufacturer=manufacturer,
                ptype=ptype,
                collection=collection,
                mpn=mpn,
                sku=sku,
                url=plink,
                pattern=pattern,
                color=color,
                cost=cost,
                msrp=msrp,
                width=width,
                vr=vr,
                hr=hr,
                content=content,
                feature=feature,
                category=keywords,
                style=keywords,
                colors=color,
                usage=usage,
                thumbnail=thumbnail,
            )

            try:
                rq = requests.post("https://www.estout.com/api/search.vbhtml", data={
                    'id': mpn, 'key': 'aeba0d7a-9518-4299-b06d-46ab828e3288'})
                j = json.loads(rq.content)

                stock = j["result"][0]["avail"]

                boqtyArray = j["result"][0]["poqty"]
                bodueArray = j["result"][0]["podue"]
                if len(boqtyArray) > 0:
                    boqty = float(boqtyArray[0])
                else:
                    boqty = 0
                if len(bodueArray) > 0:
                    bodue = bodueArray[0]
                else:
                    bodue = None

                uom = j["result"][0]["uom"]
                if uom == "YARD":
                    uom = "Per Yard"
                elif uom == "ROLL":
                    uom = "Per Roll"
                elif uom == "EACH":
                    uom = "Per Item"
                else:
                    debug("Stout", 1,
                          "UOM Error for MPN: {}. UOM: {}".format(mpn, uom))
                    continue

                price = j["result"][0]["price"]
                map = j["result"][0]["map"]

                strStatus = j["result"][0]["phase"]

                if "0" in strStatus:
                    status = True
                elif "1" in strStatus or "2" in strStatus:
                    status = True
                elif "3" in strStatus or "4" in strStatus:
                    status = False
                else:
                    status = False

                product.stock = int(float(stock))
                product.boqty = boqty
                product.bodue = bodue
                product.uom = uom
                product.cost = price
                product.map = map
                product.status = status

                product.save()

                debug("Stout", 0,
                      "Success to get product details for MPN: {}".format(mpn))
            except Exception as e:
                debug("Stout", 1,
                      "JSON Error: {}. Error: {}".format(mpn, e))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Stout');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Stout.objects.get(sku=sku)
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
                        "Stout", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Stout", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Stout.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Stout", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Stout", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Stout.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Stout", 1,
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

                increment = ""
                if product.increment != None:
                    increment = product.increment

                if product.ptype == "Wallpaper":
                    usage = "Wallcovering"
                elif product.ptype == "Fabric":
                    usage = "Fabric"
                elif product.ptype == "Trim":
                    usage = "Trimming"
                else:
                    debug("Stout", 1, "Type Error: SKU: {}. No MAP Provided".format(
                        product.sku))
                    continue

                desc = ""
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.width != None and product.width != "" and float(product.width) != 0:
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Height: {} ft<br/>".format(product.height)
                if product.hr != None and product.hr != "" and float(product.hr) != 0:
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "" and float(product.vr) != 0:
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
                    if product.map > 0:
                        price = common.formatprice(product.map, 1)
                        priceTrade = common.formatprice(cost, markup_trade)
                    else:
                        debug("Stout", 1, "Price Error: SKU: {}. No MAP Provided".format(
                            product.sku))
                        continue
                except Exception as e:
                    print(e)
                    debug("Stout", 1, "Price Error: SKU: {}".format(product.sku))
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
                    sq(increment),
                    sq(product.uom),
                    sq(usage),
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

                product.productId = productId
                product.save()

                if product.thumbnail and product.thumbnail.strip() != "":
                    try:
                        common.picdownload2(
                            product.thumbnail, "{}.jpg".format(productId))
                    except:
                        pass

                debug("Stout", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Stout.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Stout", 1,
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

                increment = ""
                if product.increment != None:
                    increment = product.increment

                if product.ptype == "Wallpaper":
                    usage = "Wallcovering"
                elif product.ptype == "Fabric":
                    usage = "Fabric"
                elif product.ptype == "Trim":
                    usage = "Trimming"
                else:
                    debug("Stout", 1, "Type Error: SKU: {}. No MAP Provided".format(
                        product.sku))
                    continue

                desc = ""
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.width != None and product.width != "" and float(product.width) != 0:
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Height: {} ft<br/>".format(product.height)
                if product.hr != None and product.hr != "" and float(product.hr) != 0:
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "" and float(product.vr) != 0:
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
                    if product.map > 0:
                        price = common.formatprice(product.map, 1)
                        priceTrade = common.formatprice(cost, markup_trade)
                    else:
                        debug("Stout", 1, "Price Error: SKU: {}. No MAP Provided".format(
                            product.sku))
                        continue
                except Exception as e:
                    print(e)
                    debug("Stout", 1, "Price Error: SKU: {}".format(product.sku))
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
                    sq(increment),
                    sq(product.uom),
                    sq(usage),
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

                debug("Stout", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Stout');""")

        rows = csr.fetchall()
        for row in rows:
            productId = row[0]
            shopifyProduct = ShopifyProduct.objects.get(productId=productId)

            try:
                pv1 = shopifyProduct.variants.filter(
                    isDefault=1).values('cost', 'price')[0]
                pv2 = shopifyProduct.variants.filter(
                    name__startswith="Trade - ").values('price')[0]
            except Exception as e:
                print(e)
                continue

            oldCost = pv1['cost']
            oldPrice = pv1['price']
            oldTradePrice = pv2['price']

            try:
                product = Stout.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("York", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                if product.map > 0:
                    newPrice = common.formatprice(product.map, 1)
                    newPriceTrade = common.formatprice(newCost, markup_trade)
                else:
                    debug("Stout", 1, "Price Error: SKU: {}. No MAP Provided".format(
                        product.sku))
                    continue
            except:
                debug("Stout", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("Stout", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Stout", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Stout'")
        con.commit()

        products = Stout.objects.all()

        for product in products:
            sku = product.sku
            stock = product.stock
            bodue = product.bodue
            if bodue == None:
                bodue = ""

            try:
                if "MARCUS WILLIAM" in product.collection:
                    csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Stout')".format(
                        sku, stock, "2-3 weeks"))
                    con.commit()
                else:
                    csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Stout')".format(
                        sku, stock, bodue))
                    con.commit()
                debug("Stout", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug("Stout", 1,
                      "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Stout.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(str(category).strip())))
                con.commit()

                debug("Stout", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(str(style).strip())))
                con.commit()

                debug("Stout", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(str(colors).strip())))
                con.commit()

                debug("Stout", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

        csr.close()
        con.close()
