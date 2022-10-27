from django.core.management.base import BaseCommand
from brands.models import PhillipJeffries
from shopify.models import Product as ShopifyProduct

import os
import pymysql
import requests
import xlrd
import json
import math
import paramiko
import sys
import csv
import codecs
import time

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.phillipjeffries
markup_trade = markup.phillipjeffries_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build PhillipJeffries Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "getProductIds" in options['functions']:
            self.getProductIds()

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "updateStock" in options['functions']:
            while True:
                self.updateStock()
                print("Completed. Waiting for next run")
                time.sleep(86400)

        if "addNew" in options['functions']:
            self.addNew()
            self.updateTags()

        if "updateExisting" in options['functions']:
            self.updateExisting()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "main" in options['functions']:
            self.getProducts()
            self.getProductIds()

    def getProducts(self):
        s = requests.Session()

        PhillipJeffries.objects.all().delete()

        wb = xlrd.open_workbook(FILEDIR + "/files/pj-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                mpn = str(sh.cell_value(i, 0))
                if mpn[0] != '0':
                    try:
                        mpn = int(float(mpn))
                    except:
                        pass
                else:
                    continue

                try:
                    PhillipJeffries.objects.get(mpn=mpn)
                    continue
                except PhillipJeffries.DoesNotExist:
                    pass

                sku = 'PJ {}'.format(mpn)

                r = s.get(
                    "https://www.phillipjeffries.com/api/products/skews/{}.json".format(mpn))
                j = json.loads(r.text)
                if "error" in j:
                    continue

                ptype = "Wallpaper"
                usage = "Wallcovering"
                brand = "Phillip Jeffries"
                pattern = str(j["collection"]["name"]
                              ).strip().replace("NEW - ", "")
                color = str(j["name"].replace(
                    pattern, "").replace("-", "").strip())
                description = str(j["collection"]["description"])
                collection = ""
                try:
                    collection = str(j["collection"]["binders"][0]["name"])
                except:
                    pass
                width = str(j["specs"]["width"])
                hr = str(j["specs"]["horizontal_repeat"])
                vr = str(j["specs"]["vertical_repeat"])
                feature = j["specs"]["maintenance"]
                stock = 0
                for st in j["stock"]["sales"]["lots"]:
                    stock += float(st["on_hand"])
                stock = math.floor(stock)

                price = float(str(sh.cell_value(i, 2)).replace("$", ""))

                uom = j["order"]["wallcovering"]["price"]["unit_of_measure"]
                if "YARD" == uom:
                    uom = "Yard"
                minimum = int(j["order"]["wallcovering"]["minimum_order"])
                incre = j["order"]["wallcovering"]["order_increment"]
                try:
                    if int(float(incre)) > 1:
                        increment = ",".join(
                            [str(ii * int(float(incre))) for ii in range(1, 21)])
                    else:
                        increment = ""
                except:
                    pass
                picLink = j["assets"]["about_header_src"]

                manufacturer = "{} {}".format(brand, ptype)

                category = "{}, {}".format(collection, description)
                style = "{}, {}".format(collection, description)
                colors = color

                PhillipJeffries.objects.create(
                    mpn=mpn,
                    sku=sku,
                    collection=collection,
                    pattern=pattern,
                    color=color,
                    feature=feature,
                    manufacturer=manufacturer,
                    minimum=minimum,
                    increment=increment,
                    ptype=ptype,
                    brand=brand,
                    uom=uom,
                    usage=usage,
                    width=width,
                    hr=hr,
                    vr=vr,
                    description=description,
                    thumbnail=picLink,
                    cost=price,
                    category=category,
                    style=style,
                    colors=colors
                )

                debug("Phillip Jeffries", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("Phillip Jeffries", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Phillip Jeffries');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = PhillipJeffries.objects.get(sku=sku)
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
                        "Phillip Jeffries", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug("Phillip Jeffries", 0,
                          "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except PhillipJeffries.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug("Phillip Jeffries", 0,
                          "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Phillip Jeffries", 0,
              "Total {} Products. Published {} Products, Unpublished {} Products.".format(total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = PhillipJeffries.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Phillip Jeffries", 1,
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
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {}<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {}<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.feature != None and product.feature != "":
                    desc += "Maintenance: {}<br/>".format(product.feature)
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
                    debug("Phillip Jeffries", 2,
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

                debug("Phillip Jeffries", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = PhillipJeffries.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Phillip Jeffries", 1,
                          "No product Image for MPN: {}".format(product.mpn))
                    continue

                if product.minimum > 7:  # Update Small minimum products
                    continue

                if product.minimum < 5:
                    minimum = 12
                elif product.minimum == 5:
                    minimum = 10
                elif product.minimum == 6:
                    minimum = 12
                elif product.minimum == 7:
                    minimum = 14
                else:
                    print("Error: Minimum: {}")

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
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {}<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {}<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.feature != None and product.feature != "":
                    desc += "Maintenance: {}<br/>".format(product.feature)
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
                    debug("Phillip Jeffries", 2,
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
                    minimum,
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

                debug("Phillip Jeffries", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Phillip Jeffries');""")

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
                product = PhillipJeffries.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("PhillipJeffries", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(newCost, markup_price)
                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("PhillipJeffries", 1,
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

                debug("PhillipJeffries", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("PhillipJeffries", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def manualPrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        wb = xlrd.open_workbook(FILEDIR + "/files/pj-price.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            mpn = str(sh.cell_value(i, 0))
            cost = float(str(sh.cell_value(i, 2)).replace("$", ""))

            try:
                product = PhillipJeffries.objects.get(mpn=mpn)
            except:
                debug("Phillip Jeffries", 1,
                      "Price Updating -- Updated product does not exist in the master list: MPN: {}".format(mpn))

            sku = product.sku
            productId = product.productId

            if productId != "" and productId != None:
                product.cost = cost
                product.save()

                try:
                    price = common.formatprice(product.cost, markup_price)
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Phillip Jeffries", 2,
                          "Price Error: SKU: {}".format(product.sku))
                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99

                try:
                    csr.execute("SELECT PV1.Cost, PV1.Price, PV2.Price AS TradePrice FROM ProductVariant PV1, ProductVariant PV2 WHERE PV1.ProductID = {} AND PV2.ProductID = {} AND PV1.IsDefault = 1 AND PV2.Name LIKE 'Trade - %' AND PV1.Cost IS NOT NULL AND PV2.Cost IS NOT NULL".format(productId, productId))
                    tmp = csr.fetchone()
                    if tmp == None:
                        debug("Phillip Jeffries", 2, "Update Price Error: ProductId: {}, SKU: {}".format(
                            productId, sku))
                        continue
                    oCost = float(tmp[0])
                    oPrice = float(tmp[1])
                    oTrade = float(tmp[2])

                    if cost != oCost or price != oPrice or priceTrade != oTrade:
                        csr.execute("CALL UpdatePriceAndTrade ({}, {}, {}, {})".format(
                            productId, cost, price, priceTrade))
                        con.commit()
                        csr.execute(
                            "CALL AddToPendingUpdatePrice ({})".format(productId))
                        con.commit()

                        debug("Phillip Jeffries", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                            productId, cost, price, priceTrade))
                    else:
                        debug("Phillip Jeffries", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                            productId, price, priceTrade))
                except:
                    debug(1, "Updating price error for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                        productId, cost, price, priceTrade))
                    continue

        csr.close()
        con.close()

    def downloadcsv(self):
        debug("Phillip Jeffries", 0,
              "Download New Inventory File from Phillip Jeffries FTP")

        host = "34.203.121.151"
        port = 22
        username = "db-pj"
        password = "DecorPJ123!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Phillip Jeffries", 2,
                  "Connection to Phillip Jeffries FTP Server Failed")
            return False

        try:
            sftp.get("inventory.csv", FILEDIR + '/files/pj-inventory.csv')
            sftp.close()
        except Exception as e:
            print(e)
            debug("Phillip Jeffries", 1, "No Inventory File")
            return

        debug("Phillip Jeffries", 0,
              "Phillip Jeffries FTP Inventory Download Completed")
        return True

    def updateStock(self):
        if not self.downloadcsv():
            sys.exit(2)

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM ProductInventory WHERE Brand = 'Phillip Jeffries'")
        con.commit()

        f = open(FILEDIR + "/files/pj-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        index = 0
        for row in cr:
            index += 1
            if index == 1:
                continue

            mpn = str(row[0])
            if mpn[0] != '0':
                try:
                    mpn = int(float(mpn))
                except:
                    pass

            sku = "PJ {}".format(mpn)

            stockval = 0
            try:
                stockval = int(float(row[1]))
            except:
                stockval = 0

            # Save to Product data
            try:
                product = PhillipJeffries.objects.get(sku=sku)
                product.stock = stockval
                product.save()
            except:
                pass

        products = PhillipJeffries.objects.all()
        for product in products:
            sku = product.sku
            stockval = product.stock

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', '{}')".format(
                    sku, stockval, "Contact Customer Service to check stock.", 'Phillip Jeffries'))
                con.commit()
                print("Updated inventory for {} to {}.".format(sku, stockval))
            except Exception as e:
                print(e)
                print("Error Updating inventory for {} to {}.".format(sku, stockval))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = PhillipJeffries.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("Phillip Jeffries", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if style != None and style != "":
                sty = str(style).strip()
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(sty)))
                con.commit()

                debug("Phillip Jeffries", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(sty)))

            if colors != None and colors != "":
                col = str(colors).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("Phillip Jeffries", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

        csr.close()
        con.close()
