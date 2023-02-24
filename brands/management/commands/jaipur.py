from django.core.management.base import BaseCommand
from brands.models import JaipurLiving
from shopify.models import Product as ShopifyProduct
from mysql.models import Type

import os
import paramiko
import pymysql
import xlrd
import csv
import time

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.jaipurliving
markup_trade = markup.jaipurliving_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Jaipur Living Database'

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

        if "updateTags" in options['functions']:
            self.updateTags()

        if "updateStock" in options['functions']:
            while True:
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "images" in options['functions']:
            self.images()

        if "main" in options['functions']:
            self.getProducts()
            self.getProductIds()

    def downloadDatasheet(self):
        debug("JaipurLiving", 0, "Download Master Datasheet from JaipurLiving FTP")

        host = "18.206.49.64"
        port = 22
        username = "jaipur"
        password = "JaipurDecor"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("JaipurLiving", 2, "Connection to JaipurLiving FTP Server Failed")
            return False

        sftp.get('/jaipur/Jaipur Living Master Data Template.xlsx',
                 FILEDIR + '/files/jaipurliving-master.xlsx')

        sftp.close()

        debug("JaipurLiving", 0,
              "JaipurLiving FTP Master Datasheet Download Completed")
        return True

    def getProducts(self):
        if not self.downloadDatasheet():
            return

        JaipurLiving.objects.all().delete()

        wb = xlrd.open_workbook(FILEDIR + '/files/jaipurliving-master.xlsx')
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            mpn = str(sh.cell_value(i, 7)).strip()

            try:
                JaipurLiving.objects.get(mpn=mpn)
                debug("JaipurLiving", 1,
                      "Produt Already exist. MPN: {}".format(mpn))
                continue
            except JaipurLiving.DoesNotExist:
                pass

            sku = "JL {}".format(mpn)

            name = str(sh.cell_value(i, 9)).strip().title()

            pattern = str(sh.cell_value(i, 13)).strip()
            if str(sh.cell_value(i, 53)).strip() != "" and str(sh.cell_value(i, 53)).strip() != "N/A":
                pattern = "{} {}".format(
                    pattern, str(sh.cell_value(i, 53)).strip())

            color = str(sh.cell_value(i, 56)).strip()
            if str(sh.cell_value(i, 57)).strip() != "" and str(sh.cell_value(i, 57)).strip() != "N/A":
                color = "{} / {}".format(color,
                                         str(sh.cell_value(i, 57)).strip())

            brand = "Jaipur Living"
            ptype = str(sh.cell_value(i, 0)).strip().title()
            manufacturer = "Jaipur Living"
            collection = str(sh.cell_value(i, 12))

            if ptype == "Accent Furniture":
                ptype = "Accents"
            if ptype == "Décor":
                ptype = "Decor"
            if ptype == "Rug Pad":
                ptype = "Rug"

            try:
                cost = round(float(sh.cell_value(i, 15)), 2)
            except:
                debug("JaipurLiving", 1, "Produt Cost error {}".format(mpn))
                continue

            try:
                map = round(float(sh.cell_value(i, 16)), 2)
            except:
                map = 0

            try:
                msrp = round(float(sh.cell_value(i, 17)), 2)
            except:
                msrp = 0

            uom = "Per Item"
            minimum = 1
            increment = ""

            description = str(sh.cell_value(i, 25)).strip()

            try:
                width = round(float(sh.cell_value(i, 21)), 2)
            except:
                width = 0

            try:
                length = round(float(sh.cell_value(i, 22)), 2)
            except:
                length = 0

            try:
                height = round(float(sh.cell_value(i, 24)), 2)
            except:
                height = 0

            featuresArr = []
            for id in range(26, 32):
                feature = str(sh.cell_value(i, id)).strip()
                if feature != "" and feature != "N/A":
                    featuresArr.append(feature)
            features = "<br>".join(featuresArr)

            material = "Front: {}".format(str(sh.cell_value(i, 35)).strip())
            if str(sh.cell_value(i, 36)).strip() != "" and str(sh.cell_value(i, 36)).strip() != "N/A":
                material = "{}, Back: {}".format(
                    material, str(sh.cell_value(i, 36)).strip())
            if str(sh.cell_value(i, 37)).strip() != "" and str(sh.cell_value(i, 37)).strip() != "N/A":
                material = "{}, Filling: {}".format(
                    material, str(sh.cell_value(i, 37)).strip())

            care = str(sh.cell_value(i, 39)).strip()

            country = str(sh.cell_value(i, 32)).strip()
            usage = ptype
            try:
                weight = float(sh.cell_value(i, 88))
            except:
                weight = 5
            upc = int(sh.cell_value(i, 6))

            style = str(sh.cell_value(i, 50)).strip()
            if str(sh.cell_value(i, 51)).strip() != "" and str(sh.cell_value(i, 51)).strip() != "N/A":
                style = "{}, {}".format(
                    style, str(sh.cell_value(i, 51)).strip())
            category = "{}, {}".format(pattern, description)
            colors = color

            status = True
            stock = 5

            thumbnail = str(sh.cell_value(i, 89)).strip()

            roomsetsArr = []
            for id in range(90, 104):
                roomset = str(sh.cell_value(i, id)).strip()
                if roomset != "":
                    roomsetsArr.append(roomset)
            roomsets = "|".join(roomsetsArr)

            JaipurLiving.objects.create(
                mpn=mpn,
                sku=sku,

                name=name,
                pattern=pattern,
                color=color,

                brand=brand,
                ptype=ptype,
                manufacturer=manufacturer,
                collection=collection,

                uom=uom,
                minimum=minimum,
                increment=increment,

                description=description,
                width=width,
                length=length,
                height=height,
                features=features,
                material=material,
                care=care,
                country=country,
                usage=usage,
                weight=weight,
                upc=upc,

                category=category,
                style=style,
                colors=colors,

                status=status,
                stock=stock,

                thumbnail=thumbnail,
                roomsets=roomsets,

                cost=cost,
                map=map,
                msrp=msrp
            )

            debug("JaipurLiving", 0,
                  "Success to get product details for MPN: {}".format(mpn))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Jaipur Living')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = JaipurLiving.objects.get(mpn=mpn)
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
                        "JaipurLiving", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "JaipurLiving", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except JaipurLiving.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "JaipurLiving", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("JaipurLiving", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = JaipurLiving.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                name = " | ".join((product.brand, product.pattern,
                                  product.color, product.ptype))
                title = product.name

                description = title
                vname = title
                hassample = 1
                gtin = product.upc
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
                if product.length != None and product.length != "" and float(product.length) != 0:
                    desc += "Length: {} in<br/>".format(product.length)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Height: {} in<br/><br/>".format(product.height)

                if product.features != None and product.features != "":
                    desc += "{}<br/><br/>".format(product.features)

                if product.material != None and product.material != "":
                    desc += "Material: {}<br/>".format(product.material)
                if product.care != None and product.care != "":
                    desc += "Product Care: {}<br/><br/>".format(product.care)

                if product.country != None and product.country != "":
                    desc += "Country of Origin: {}<br/>".format(
                        product.country)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                try:
                    price = common.formatprice(product.cost, markup_price)
                    if product.map > 0:
                        price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("JaipurLiving", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                try:
                    productType = Type.objects.get(name=product.ptype)
                    if productType.parentTypeId == 0:
                        ptype = productType.name
                    else:
                        parentType = Type.objects.get(
                            typeId=productType.parentTypeId)
                        if parentType.parentTypeId == 0:
                            ptype = parentType.name
                        else:
                            rootType = Type.objects.get(
                                typeId=parentType.parentTypeId)
                            ptype = rootType.name
                except:
                    ptype = product.name

                csr.execute("CALL CreateProduct ({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{})".format(
                    sq(product.sku),
                    sq(name),
                    sq(product.manufacturer),
                    sq(product.mpn),
                    sq(desc),
                    sq(title),
                    sq(description),
                    sq(ptype),
                    sq(vname),
                    hassample,
                    product.cost,
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

                debug("JaipurLiving", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = JaipurLiving.objects.all()

        idx = 0
        total = len(products)
        for product in products:
            idx += 1
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
                gtin = product.upc
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
                    desc += "Height: {} in<br/>".format(product.height)
                if product.depth != None and product.depth != "" and float(product.depth) != 0:
                    desc += "Depth: {} in<br/><br/>".format(product.depth)

                if product.features != None and product.features != "":
                    desc += "Feature: {}<br/><br/>".format(product.features)

                if product.material != None and product.material != "":
                    desc += "Material: {}<br/>".format(product.material)
                if product.disclaimer != None and product.disclaimer != "":
                    desc += "Disclaimer: {}<br/>".format(product.disclaimer)
                if product.care != None and product.care != "":
                    desc += "Product Care: {}<br/><br/>".format(product.care)

                if product.specs != None and product.specs != "":
                    desc += "Specs: {}<br/><br/>".format(product.specs)

                if product.country != None and product.country != "":
                    desc += "Country of Origin: {}<br/>".format(
                        product.country)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                try:
                    price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("JaipurLiving", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                productType = Type.objects.get(name=product.ptype)
                if productType.parentTypeId == 0:
                    ptype = productType.name
                else:
                    parentType = Type.objects.get(
                        typeId=productType.parentTypeId)
                    if parentType.parentTypeId == 0:
                        ptype = parentType.name
                    else:
                        rootType = Type.objects.get(
                            typeId=parentType.parentTypeId)
                        ptype = rootType.name

                csr.execute("CALL CreateProduct ({},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{})".format(
                    sq(product.sku),
                    sq(name),
                    sq(product.manufacturer),
                    sq(product.mpn),
                    sq(desc),
                    sq(title),
                    sq(description),
                    sq(ptype),
                    sq(vname),
                    hassample,
                    product.cost,
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

                debug("JaipurLiving", 0, "{}/{}: Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    idx, total, productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = JaipurLiving.objects.all()
        for product in products:
            sku = product.sku

            style = product.style
            colors = product.colors
            subtypes = "{}, {}".format(product.ptype, product.pattern)
            collection = product.collection

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("JaipurLiving", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("JaipurLiving", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

            if subtypes != None and subtypes != "":
                csr.execute("CALL AddToEditSubtype ({}, {})".format(
                    sq(sku), sq(str(subtypes).strip())))
                con.commit()

                debug("JaipurLiving", 0,
                      "Added Subtype. SKU: {}, Subtype: {}".format(sku, sq(subtypes)))

            if collection != None and collection != "":
                csr.execute("CALL AddToEditCollection ({}, {})".format(
                    sq(sku), sq(collection)))
                con.commit()

                debug("JaipurLiving", 0, "Added Collection. SKU: {}, Collection: {}".format(
                    sku, sq(collection)))

        csr.close()
        con.close()

    def downloadInvFile(self):
        debug("JaipurLiving", 0, "Download New CSV from JaipurLiving FTP")

        host = "18.206.49.64"
        port = 22
        username = "jaipurliving"
        password = "JY123!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("JaipurLiving", 2, "Connection to JaipurLiving FTP Server Failed")
            return False

        try:
            sftp.chdir(path='/jaipurliving')
            files = sftp.listdir()
        except:
            debug("JaipurLiving", 1, "No New Inventory File")
            return False

        for file in files:
            if "EDI" in file:
                continue
            sftp.get(file, FILEDIR + '/files/jaipurliving-inventory.csv')
            sftp.remove(file)

        sftp.close()

        debug("JaipurLiving", 0, "JaipurLiving FTP Inventory Download Completed")
        return True

    def updateStock(self):
        if not self.downloadInvFile():
            return

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM ProductInventory WHERE Brand = 'Jaipur Living'")
        con.commit()

        f = open(FILEDIR + '/files/jaipurliving-inventory.csv', "rt")
        cr = csv.reader(f)

        index = 0
        for row in cr:
            index += 1
            if index == 1:
                continue

            mpn = row[1]
            try:
                product = JaipurLiving.objects.get(mpn=mpn)
            except:
                continue

            sku = product.sku

            stock = int(row[2])

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Jaipur Living')".format(
                    sku, stock, product.boDate.replace("Lead Time:", "").strip()))
                con.commit()
                debug("JaipurLiving", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug(
                    "JaipurLiving", 2, "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Jaipur Living');""")

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
                product = JaipurLiving.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
                map = product.map
            except:
                debug("JaipurLiving", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(map, 1)
                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("JaipurLiving", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("JaipurLiving", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("JaipurLiving", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def images(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        hasImage = []
        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = 'JF Fabrics'")
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        products = JaipurLiving.objects.all()
        for product in products:
            if product.productId == None or product.productId in hasImage:
                continue

            if product.thumbnail and product.thumbnail.strip() != "":
                try:
                    common.picdownload2(
                        product.thumbnail, "{}.jpg".format(product.productId))
                except Exception as e:
                    print(e)
                    pass

            if product.roomsets and product.roomsets.strip() != "":
                idx = 2
                for roomset in product.roomsets.split("|"):
                    try:
                        common.roomdownload(
                            roomset, "{}_{}.jpg".format(product.productId, idx))
                        idx = idx + 1
                    except Exception as e:
                        print(e)
                        pass
