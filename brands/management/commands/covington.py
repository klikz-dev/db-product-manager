from django.core.management.base import BaseCommand
from brands.models import Covington
from shopify.models import Product as ShopifyProduct

import os
import csv
import pymysql
import time
import xlrd
from shutil import copyfile

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.covington
markup_trade = markup.covington_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Covington Database'

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

        if "updateStock" in options['functions']:
            self.updateStock()

        if "image" in options['functions']:
            self.image()

        if "roomset" in options['functions']:
            self.roomset()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updatePrice()
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def getProducts(self):
        Covington.objects.all().delete()

        wb = xlrd.open_workbook(FILEDIR + "/files/covington-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                mpn = str(sh.cell_value(i, 0)).strip()

                try:
                    Covington.objects.get(mpn=mpn)
                    continue
                except Covington.DoesNotExist:
                    pass

                sku = "DBC {}".format(mpn)

                pattern = str(sh.cell_value(i, 4)).strip()
                color = str(sh.cell_value(i, 5)).strip()

                brand = "Covington"
                collection = str(sh.cell_value(i, 2)).strip()

                ptype = str(sh.cell_value(i, 3)).strip()

                try:
                    price = round(float(
                        str(sh.cell_value(i, 6)).replace('$', '').strip()), 2)
                except:
                    debug("Covington", 1, "Produt price error {}".format(mpn))
                    continue

                uom = str(sh.cell_value(i, 20)).strip()
                if uom == "Yard":
                    uom = "Per Yard"
                elif uom == "Roll":
                    uom = "Per Roll"
                else:
                    debug("Covington", 1, "UOM error {}".format(mpn))
                    continue

                minimum = int(sh.cell_value(i, 22))

                # Covington has no increment.
                increment = ''

                usage = str(sh.cell_value(i, 21)).strip()

                try:
                    width = round(float(sh.cell_value(i, 10)), 2)
                except:
                    width = 0
                try:
                    hr = round(float(sh.cell_value(i, 14)), 2)
                except:
                    hr = 0
                try:
                    vr = round(float(sh.cell_value(i, 15)), 2)
                except:
                    vr = 0

                description = str(sh.cell_value(i, 9)).strip()
                content = str(sh.cell_value(i, 13)).strip()

                feature = str(sh.cell_value(i, 16)).strip()
                if str(sh.cell_value(i, 17)).strip() != "":
                    feature = feature + ", " + \
                        str(sh.cell_value(i, 17)).strip()
                if str(sh.cell_value(i, 18)).strip() != "":
                    feature = feature + ", " + \
                        str(sh.cell_value(i, 18)).strip()

                style = str(sh.cell_value(i, 24)).strip()
                colors = str(sh.cell_value(i, 25)).strip()
                category = feature + ", " + str(sh.cell_value(i, 26)).strip()

                manufacturer = "{} {}".format(brand, ptype)

                Covington.objects.create(
                    mpn=mpn,
                    sku=sku,
                    collection=collection,
                    pattern=pattern,
                    color=color,
                    manufacturer=manufacturer,
                    ptype=ptype,
                    brand=brand,
                    uom=uom,
                    minimum=minimum,
                    increment=increment,
                    usage=usage,
                    category=category,
                    style=style,
                    colors=colors,
                    width=width,
                    hr=hr,
                    vr=vr,
                    description=description,
                    content=content,
                    feature=feature,
                    cost=price,
                )

                debug("Covington", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("Covington", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Covington')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = Covington.objects.get(mpn=mpn)
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
                        "Covington", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Covington", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except Covington.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Covington", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("Covington", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Covington.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                name = " | ".join(("DecoratorsBest", product.pattern,
                                  product.color, product.ptype))
                title = " ".join(("DecoratorsBest", product.pattern,
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
                if product.width != None and product.width != "" and float(product.width) != 0:
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Length: {} in<br/>".format(product.height)
                if product.rollLength != None and product.rollLength != "" and float(product.rollLength) != 0:
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} yards<br/>".format(
                            product.rollLength)
                if product.hr != None and product.hr != "" and float(product.hr) != 0:
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "" and float(product.vr) != 0:
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.country != None and product.country != "":
                    desc += "Country of Origin: {}<br/>".format(
                        product.country)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format("DecoratorsBest", product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    if price < product.map:
                        price = common.formatprice(product.map, 1)

                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Covington", 1,
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

                product.productId = productId
                product.save()

                debug("Covington", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Covington.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                name = " | ".join(("DecoratorsBest", product.pattern,
                                  product.color, product.ptype))
                title = " ".join(("DecoratorsBest", product.pattern,
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
                if product.width != None and product.width != "" and float(product.width) != 0:
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Length: {} in<br/>".format(product.height)
                if product.rollLength != None and product.rollLength != "" and float(product.rollLength) != 0:
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} yards<br/>".format(
                            product.rollLength)
                if product.hr != None and product.hr != "" and float(product.hr) != 0:
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "" and float(product.vr) != 0:
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.country != None and product.country != "":
                    desc += "Country of Origin: {}<br/>".format(
                        product.country)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format("DecoratorsBest", product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    if price < product.map:
                        price = common.formatprice(product.map, 1)

                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Covington", 1,
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

                debug("Covington", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Covington');""")

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
                product = Covington.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Covington", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(newCost, markup_price)
                if newPrice < product.map:
                    newPrice = common.formatprice(product.map, 1)

                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("Covington", 1,
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

                debug("Covington", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Covington", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Covington'")
        con.commit()

        f = open(FILEDIR + '/files/covington-inventory.csv', "rt")
        cr = csv.reader(f)

        for row in cr:
            if row[0] == "Style":
                continue

            mpn = "{}#{}".format(row[0], row[2])
            sku = "DBC {}".format(mpn)

            stock = int(row[4])

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Covington')".format(
                    sku, stock, ""))
                con.commit()
                debug("Covington", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug(
                    "Covington", 1, "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Covington.objects.all()
        for product in products:
            sku = product.sku

            style = product.style
            category = product.category
            colors = product.colors

            if style != None and style != "":
                sty = str(style).strip()
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(sty)))
                con.commit()

                debug("Covington", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(sty)))

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("Covington", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if colors != None and colors != "":
                col = str(colors).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("Covington", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

        csr.close()
        con.close()

    def image(self):
        fnames = os.listdir(FILEDIR + "/files/images/covington/")
        print(fnames)
        for fname in fnames:
            try:
                pattern = fname.split(" ")[0]
                color = fname.split(" ")[1].split(".")[0]

                product = Covington.objects.get(pattern=pattern, color=color)
                productId = product.productId

                if productId != None and productId != "":
                    copyfile(FILEDIR + "/files/images/covington/" + fname, FILEDIR +
                             "/../../images/product/{}.jpg".format(productId))

                os.remove(FILEDIR + "/files/images/covington/" + fname)
            except:
                continue

    def roomset(self):
        fnames = os.listdir(FILEDIR + "/files/images/covington/")

        for fname in fnames:
            try:
                if "_" in fname:
                    mpn = fname.split("_")[0]
                    roomId = int(fname.split("_")[1].split(".")[0]) + 1

                    product = Covington.objects.get(mpn=mpn)
                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "/files/images/covington/" + fname, FILEDIR +
                                 "/../../images/roomset/{}_{}.jpg".format(productId, roomId))

                        debug("Covington", 0, "Roomset Image {}_{}.jpg".format(
                            productId, roomId))

                        os.remove(
                            FILEDIR + "/files/images/covington/" + fname)
                    else:
                        print("No product found with MPN: {}".format(mpn))
                else:
                    continue

            except Exception as e:
                print(e)
                continue
