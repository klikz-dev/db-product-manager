from math import pi
from django.core.management.base import BaseCommand
from brands.models import Schumacher
from shopify.models import Product as ShopifyProduct

import os
import pymysql
import sys
import xlrd
import paramiko
import time
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

markup_price = markup.schumacher
markup_trade = markup.schumacher_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Schumacher Database'

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

        if "updateTags" in options['functions']:
            self.updateTags()

        if "fixImages" in options['functions']:
            self.fixImages()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updatePrice()
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def downloadcsv(self):
        debug("Schumacher", 0, "Download New Master XLS from Schumacher FTP")

        host = "34.203.121.151"
        port = 22
        username = "schumacher"
        password = "Sch123Decbest!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Schumacher", 2, "Connection to Schumacher FTP Server Failed")
            return False

        sftp.get("../daily_feed/Assortment-DecoratorsBest.csv",
                 FILEDIR + '/files/schumacher-master.csv')

        sftp.close()

        debug("Schumacher", 0, "Schumacher FTP Master File Download Completed")
        return True

    def getProducts(self):
        if not self.downloadcsv():
            sys.exit(2)

        Schumacher.objects.all().delete()

        f = open(FILEDIR + "/files/schumacher-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Category":
                continue

            brand = "Schumacher"

            try:
                mpn = int(row[3])
                sku = "SCH {}".format(mpn)
            except:
                mpn = str(row[3]).strip()
                sku = "SCH {}".format(str(mpn).replace("'", ""))

            try:
                Schumacher.objects.get(sku=sku)
                continue
            except Schumacher.DoesNotExist:
                pass

            pattern = str(row[4]).strip().replace('', '').replace('¥', '').replace('…', '').replace('„', '')
            color = str(row[5]).strip().replace('', '').replace('¥', '').replace('…', '').replace('„', '')
            ptype = str(row[0]).strip()

            collection = str(row[2]).strip()
            if "STAPETER" in collection:
                collection = "BORÃSTAPETER"
                brand = "BORÃSTAPETER"

            if "FABRIC" == ptype:
                ptype = "Fabric"
                usage = "Fabric"
            elif "TRIM" == ptype:
                ptype = "Trim"
                usage = "Trimming"
            elif "WALLPAPER" == ptype or "WALLCOVERING" == ptype:
                ptype = "Wallpaper"
                usage = "Wallcovering"
            elif "FURNITURE & ACCESSORIES" == ptype:
                ptype = "Pillow"
                usage = "Pillow"
                pattern = pattern.replace("Pillow", "").strip()
            else:
                debug("Schumacher", 1,
                      "Product Type Error: MPN: {}, Type: {}".format(mpn, ptype))
                continue

            price = float(row[7])

            width = str(row[11]).strip()
            vr = str(row[15]).strip()
            hr = str(row[16]).strip()
            match = str(row[14]).strip()
            try:
                rollLength = float(row[8])
            except:
                rollLength = 0
            description = row[17].replace('', '').replace('¥', '').replace('…', '').replace('„', '')

            content1 = row[12]
            content2 = row[13]

            if content1 == "" and content2 == "":
                content = ""
            elif content1 == "" and content2 != "":
                content = content2
            elif content1 != "" and content2 == "":
                content = content1
            else:
                content = content1.strip() + ", " + content2.strip()

            if row[6] == "#N/A":
                style = ""
            else:
                style = str(row[6]).strip()

            priceby = str(row[9]).strip().upper()
            if "YARD" in priceby or "REPEAT" in priceby:
                uom = "Per Yard"
            elif "ROLL" in priceby:
                uom = "Per Roll"
            elif "EACH" in priceby or "UNIT" in priceby or "SET" in priceby:
                uom = "Per Item"
            elif "PANEL" in priceby:
                uom = "Per Panel"
            else:
                debug("Schumacher", 1, "Pricing Error. mpn: {}. Priceby: {}".format(
                    mpn, priceby))

            try:
                minimum = int(float(row[10]))
            except:
                minimum = 1

            if ptype == "Wallpaper":
                incre = minimum
            else:
                incre = 1  # 4/4/22. From Bk / Matthew - Sch Fab and Trim have no increment

            # Update 7/30/21. Sch Trim has minimum of 2. No increment changes needed
            # if ptype == "Trim" and minimum < 2:
            if ptype != "Wallpaper" and ptype != "Pillow" and minimum < 2:  # Update 8/2. Same issue with Fabric
                minimum = 2

            increment = ""
            if incre > 1:
                increment = ",".join([str(ii * incre) for ii in range(1, 26)])

            stock = int(row[19])
            picLink = str(row[18]).strip()
            roomset = str(row[22]).strip()

            manufacturer = "{} {}".format(brand, ptype)

            # Tagging
            keywords = "{}, {}, {}".format(collection, style, description)

            Schumacher.objects.create(
                mpn=mpn,
                sku=sku,
                collection=collection,
                pattern=pattern,
                color=color,
                manufacturer=manufacturer,
                colors=color,
                ptype=ptype,
                brand=brand,
                uom=uom,
                usage=usage,
                category=keywords,
                style=keywords,
                width=width,
                hr=hr,
                vr=vr,
                match=match,
                rollLength=rollLength,
                description=description,
                content=content,
                cost=price,
                stock=stock,
                thumbnail=picLink,
                roomset=roomset,
                minimum=minimum,
                increment=increment,
            )

            debug("Schumacher", 0,
                  "Success to get product details for MPN: {}".format(mpn))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Schumacher');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Schumacher.objects.get(sku=sku)
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
                        "Schumacher", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Schumacher", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Schumacher.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Schumacher", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            # Temp. DB - Shopify sync issue.
            # csr.execute(
            #     "CALL AddToPendingUpdatePublish ({})".format(productID))
            # con.commit()

        debug("Schumacher", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Schumacher.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Schumacher", 1,
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
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} yds<br/>".format(
                            product.rollLength)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.match != None and product.match != "":
                    desc += "Match: {}<br/>".format(product.match)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Schumacher", 2,
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

                roomsets = str(product.roomset).split(",")

                for idx, roomset in enumerate(roomsets):
                    if idx == 0:
                        try:
                            common.picdownload2(
                                str(roomset).strip(), "{}.jpg".format(productId))
                        except Exception as e:
                            print(e)

                    else:
                        try:
                            common.roomdownload(
                                str(roomset).strip(), "{}_{}.jpg".format(productId, idx + 1))
                        except Exception as e:
                            print(e)

                debug("Schumacher", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # products = Schumacher.objects.all()
        products = Schumacher.objects.filter(collection="BORÃSTAPETER")

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Schumacher", 1,
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
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} yds<br/>".format(
                            product.rollLength)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.match != None and product.match != "":
                    desc += "Match: {}<br/>".format(product.match)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Schumacher", 2,
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

                debug("Schumacher", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Schumacher');""")

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
                product = Schumacher.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Schumacher", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(newCost, markup_price)
                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("Schumacher", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("Schumacher", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Schumacher", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Schumacher'")
        con.commit()

        products = Schumacher.objects.all()

        for product in products:
            sku = product.sku
            stock = product.stock

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 2, '{}', 'Schumacher')".format(
                    sku, stock, ""))
                con.commit()
                debug("Schumacher", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug("Schumacher", 2,
                      "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Schumacher.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.color

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(category)))
                con.commit()

                debug("Schumacher", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("Schumacher", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("Schumacher", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

        csr.close()
        con.close()

    def fixImages(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()
        hasImage = []
        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = 'Schumacher'")
        for row in csr.fetchall():
            hasImage.append(row[0])

        products = Schumacher.objects.all()

        for product in products:
            if product.productId == None:
                continue

            if int(product.productId) in hasImage:
                continue

            if product.thumbnail == "":
                continue
            
            productId = product.productId
            roomsets = str(product.roomset).split(",")

            for idx, roomset in enumerate(roomsets):
                if idx == 0:
                    try:
                        common.picdownload2(
                            str(roomset).strip(), "{}.jpg".format(productId))
                    except Exception as e:
                        print(e)

                else:
                    try:
                        common.roomdownload(
                            str(roomset).strip(), "{}_{}.jpg".format(productId, idx + 1))
                    except Exception as e:
                        print(e)
