import paramiko
from library import debug, common, shopify, markup
from django.core.management.base import BaseCommand
from brands.models import Materialworks
from shopify.models import Product as ShopifyProduct

import os
import csv
import pymysql
import time
import xlrd
from shutil import copyfile

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.materialworks
markup_trade = markup.materialworks_trade
markup_pillow_trade = markup.materialworks_pillow_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build MaterialWorks Database'

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

        if "updateStock" in options['functions']:
            while True:
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

        if "image" in options['functions']:
            self.image()

        if "updateStock" in options['functions']:
            while True:
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

        if "main" in options['functions']:
            self.getProducts()
            self.getProductIds()

    def getProducts(self):
        Materialworks.objects.all().delete()

        wb = xlrd.open_workbook(FILEDIR + "/files/materialworks-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                mpn = str(sh.cell_value(i, 0)).strip()

                try:
                    Materialworks.objects.get(mpn=mpn)
                    continue
                except Materialworks.DoesNotExist:
                    pass

                sku = "DBM {}".format(mpn)

                pattern = str(sh.cell_value(i, 4)).strip()
                color = str(sh.cell_value(i, 5)).strip()

                brand = "Materialworks"
                collection = str(sh.cell_value(i, 2)).strip()

                ptype = str(sh.cell_value(i, 3)).strip()

                cost = float(sh.cell_value(i, 7))
                map = float(sh.cell_value(i, 8))
                msrp = float(sh.cell_value(i, 9))

                uom = str(sh.cell_value(i, 17)).strip()
                if uom == "Yard":
                    uom = "Per Yard"
                elif uom == "Roll":
                    uom = "Per Roll"
                elif uom == "Each":
                    uom = "Per Item"
                else:
                    debug("Materialworks", 1, "UOM error {}".format(mpn))
                    continue

                minimum = 1
                increment = ''

                usage = str(sh.cell_value(i, 18)).strip().replace("/ ", "/")

                width = str(sh.cell_value(i, 11)).strip()
                height = str(sh.cell_value(i, 12)).strip()

                size = str(sh.cell_value(i, 6)).strip().replace('x', '" x ').replace(
                    'X', '" x ').replace('In', '"').replace(' "', '"')

                vr = str(sh.cell_value(i, 14)).strip()
                hr = str(sh.cell_value(i, 15)).strip()

                description = str(sh.cell_value(i, 10)).strip()
                content = str(sh.cell_value(i, 13)).strip()

                feature = str(sh.cell_value(i, 16)).strip()

                style = str(sh.cell_value(i, 21)).strip()
                colors = str(sh.cell_value(i, 22)).strip()
                category = str(sh.cell_value(i, 23)).strip()

                keywords = "{}, {}, {}".format(usage, style, category)

                manufacturer = "{} {}".format(brand, ptype)

                Materialworks.objects.create(
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
                    category=keywords,
                    style=keywords,
                    colors=colors,
                    width=width,
                    height=height,
                    size=size,
                    hr=hr,
                    vr=vr,
                    description=description,
                    content=content,
                    feature=feature,
                    cost=cost,
                    map=map,
                    msrp=msrp
                )

                debug("Materialworks", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("Materialworks", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Materialworks')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = Materialworks.objects.get(mpn=mpn)
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
                        "Materialworks", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Materialworks", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except Materialworks.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Materialworks", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("Materialworks", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Materialworks.objects.all()

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

                if product.width != None and product.width != "":
                    desc += "Width: {}<br/>".format(product.width)

                if product.height != None and product.height != "":
                    desc += "Length: {}<br/>".format(product.height)

                if product.size != None and product.size != "":
                    desc += "Size: {}<br/>".format(product.size)

                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {}<br/>".format(product.hr)

                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {}<br/>".format(product.vr)

                if product.content != None and product.content != "":
                    desc += "Content: {}<br/><br/>".format(product.content)

                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)

                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)

                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format("DecoratorsBest", product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(cost, markup_trade)
                    if product.ptype == "Pillow":
                        priceTrade = common.formatprice(cost, markup_pillow_trade)
                except:
                    debug("Materialworks", 1,
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

                debug("Materialworks", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Materialworks.objects.all()

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

                if product.width != None and product.width != "":
                    desc += "Width: {}<br/>".format(product.width)

                if product.height != None and product.height != "":
                    desc += "Length: {}<br/>".format(product.height)

                if product.size != None and product.size != "":
                    desc += "Size: {}<br/>".format(product.size)

                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {}<br/>".format(product.hr)

                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {}<br/>".format(product.vr)

                if product.content != None and product.content != "":
                    desc += "Content: {}<br/><br/>".format(product.content)

                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)

                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)

                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format("DecoratorsBest", product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(cost, markup_trade)
                    if product.ptype == "Pillow":
                        priceTrade = common.formatprice(
                            cost, markup_pillow_trade)
                except:
                    debug("Materialworks", 1,
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

                debug("Materialworks", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Materialworks');""")

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
                product = Materialworks.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Materialworks", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(product.map, 1)
                newPriceTrade = common.formatprice(newCost, markup_trade)
                if product.ptype == "Pillow":
                    newPriceTrade = common.formatprice(newCost, markup_pillow_trade)
            except:
                debug("Materialworks", 1,
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

                debug("Materialworks", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Materialworks", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def downloadInvFile(self):
        debug("Brewster", 0, "Download New CSV from Brewster FTP")

        host = "18.206.49.64"
        port = 22
        username = "materialworks"
        password = "MWDecor1!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Materialworks", 2,
                  "Connection to Materialworks FTP Server Failed")
            return False

        sftp.chdir(path='/materialworks')

        try:
            files = sftp.listdir()
        except:
            debug("Materialworks", 1, "No New Inventory File")
            return False

        for file in files:
            if "EDI" in file:
                continue
            sftp.get(file, FILEDIR + '/files/materialworks-inventory.csv')
            sftp.remove(file)

        sftp.close()

        debug("Materialworks", 0, "Materialworks FTP Inventory Download Completed")
        return True

    def updateStock(self):
        if not self.downloadInvFile():
            return

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM ProductInventory WHERE Brand = 'Materialworks'")
        con.commit()

        f = open(FILEDIR + '/files/materialworks-inventory.csv', "rt")
        cr = csv.reader(f)

        for row in cr:
            if row[0] == "ValdeseMaterial":
                continue

            mpn = "{}".format(row[0])
            sku = "DBM {}".format(mpn)

            stock = int(row[5])

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Materialworks')".format(
                    sku, stock, ""))
                con.commit()
                debug("Materialworks", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug(
                    "Materialworks", 1, "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Materialworks.objects.all()
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

                debug("Materialworks", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(sty)))

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("Materialworks", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if colors != None and colors != "":
                col = str(colors).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("Materialworks", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

        csr.close()
        con.close()

    def updateSizeTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Materialworks.objects.all()
        for product in products:
            sku = product.sku
            ptype = product.ptype
            size = product.size
            width = product.width

            if size != None and size != "" and ptype == "Pillow":
                csr.execute("CALL AddToEditSize ({}, {})".format(
                    sq(sku), sq(size)))
                con.commit()

                debug("Materialworks", 0,
                      "Added Size. SKU: {}, Size: {}".format(sku, sq(size)))

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

                debug("Materialworks", 0,
                      "Added Width. SKU: {}, Width: {}, Width Tag: {}".format(sku, width, widthTag))

        csr.close()
        con.close()

    def image(self):
        fnames = os.listdir(FILEDIR + "/files/images/materialworks/")
        print(fnames)
        for fname in fnames:
            try:
                mpn = fname.split(".")[0]

                product = Materialworks.objects.get(mpn=mpn)
                productId = product.productId

                if productId != None and productId != "":
                    copyfile(FILEDIR + "/files/images/materialworks/" + fname, FILEDIR +
                             "/../../images/product/{}.jpg".format(productId))

                os.remove(FILEDIR + "/files/images/materialworks/" + fname)
            except:
                continue

    def roomset(self):
        fnames = os.listdir(FILEDIR + "/files/images/materialworks/")

        for fname in fnames:
            try:
                if "_" in fname:
                    mpn = fname.split("_")[0]
                    roomId = int(fname.split("_")[1].split(".")[0]) + 1

                    product = Materialworks.objects.get(mpn=mpn)
                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "/files/images/materialworks/" + fname, FILEDIR +
                                 "/../../images/roomset/{}_{}.jpg".format(productId, roomId))

                        debug("Materialworks", 0, "Roomset Image {}_{}.jpg".format(
                            productId, roomId))

                        os.remove(
                            FILEDIR + "/files/images/materialworks/" + fname)
                    else:
                        print("No product found with MPN: {}".format(mpn))
                else:
                    continue

            except Exception as e:
                print(e)
                continue
