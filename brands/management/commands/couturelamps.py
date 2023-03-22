from django.core.management.base import BaseCommand
from brands.models import CoutureLamps
from shopify.models import Product as ShopifyProduct
from mysql.models import Type

import os
import paramiko
import pymysql
import xlrd
import time
from datetime import datetime
from shutil import copyfile

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.couturelamps
markup_trade = markup.couturelamps_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Couture Lamps Database'

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
            self.updateStock()

        if "updatePrice" in options['functions']:
            self.updatePrice()

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
        CoutureLamps.objects.all().delete()

        wb = xlrd.open_workbook(FILEDIR + '/files/couture-lamps-master.xlsx')
        sh = wb.sheet_by_index(0)

        for i in range(2, sh.nrows):
            mpn = str(sh.cell_value(i, 0)).strip()

            try:
                CoutureLamps.objects.get(mpn=mpn)
                debug("CoutureLamps", 1,
                      "Produt Already exist. MPN: {}".format(mpn))
                continue
            except CoutureLamps.DoesNotExist:
                pass

            sku = "CL {}".format(mpn)

            pattern = str(sh.cell_value(i, 2)).split("-")[0].strip()
            color = str(sh.cell_value(i, 7)).strip()

            pattern = pattern.replace("Lamp", "").replace(
                "Table", "").replace("  ", "").strip()

            brand = "Couture"
            ptype = str(sh.cell_value(i, 3)).strip().title()
            manufacturer = "Couture Lamps"
            collection = ptype

            if ptype == "":
                continue
            if ptype == "Accent Lamp":
                ptype = "Accent Lamps"
            if ptype == "Accent Table":
                ptype = "Accent Tables"
            if ptype == "Decorative Accessories":
                ptype = "Decorative Accents"
            if ptype == "Table Lamp":
                ptype = "Table Lamps"

            try:
                cost = round(float(sh.cell_value(i, 9)), 2)
            except:
                debug("CoutureLamps", 1, "Produt Cost error {}".format(mpn))
                continue

            try:
                map = round(float(sh.cell_value(i, 10)), 2)
            except:
                debug("CoutureLamps", 1, "Produt MAP error {}".format(mpn))
                continue

            uom = "Per Item"
            minimum = 1
            increment = ""

            description = str(sh.cell_value(i, 4)).strip()

            width = str(sh.cell_value(i, 13))
            height = str(sh.cell_value(i, 16))
            depth = str(sh.cell_value(i, 15))

            material = str(sh.cell_value(i, 6)).strip()
            care = str(sh.cell_value(i, 5)).strip()

            features = str(sh.cell_value(i, 8)).strip()

            specs = ""
            if sh.cell_value(i, 17) != "":
                specs += "Voltage: {}<br>".format(sh.cell_value(i, 17))
            if sh.cell_value(i, 19) != "":
                specs += "Switch Type: {}<br>".format(
                    sh.cell_value(i, 19))
            if sh.cell_value(i, 20) != "":
                specs += "Switch Location: {}<br>".format(sh.cell_value(i, 20))
            if sh.cell_value(i, 24) != "":
                specs += "Cord Length: {}<br>".format(sh.cell_value(i, 24))
            if sh.cell_value(i, 25) != "":
                specs += "Cord Color: {}<br>".format(
                    sh.cell_value(i, 25))
            if sh.cell_value(i, 26) != "":
                specs += "Wattage: {}<br>".format(
                    sh.cell_value(i, 26))

            country = str(sh.cell_value(i, 1)).strip()

            usage = ptype

            try:
                weight = float(sh.cell_value(i, 12))
            except:
                weight = 5

            upc = int(sh.cell_value(i, 38))

            style = description
            category = ""
            colors = color

            status = True
            stock = 5
            try:
                boDate = "Lead Time: {}".format(
                    str(sh.cell_value(i, 37)).strip())
            except:
                boDate = ""

            CoutureLamps.objects.create(
                mpn=mpn,
                sku=sku,

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
                height=height,
                depth=depth,
                features=features,
                material=material,
                care=care,
                specs=specs,
                country=country,
                usage=usage,
                weight=weight,
                upc=upc,

                category=category,
                style=style,
                colors=colors,

                status=status,
                stock=stock,
                boDate=boDate,

                cost=cost,
                map=map,
            )

            debug("CoutureLamps", 0,
                  "Success to get product details for MPN: {}".format(mpn))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Couture')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = CoutureLamps.objects.get(mpn=mpn)
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
                        "CoutureLamps", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "CoutureLamps", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except CoutureLamps.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "CoutureLamps", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("CoutureLamps", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = CoutureLamps.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                name = " | ".join(
                    (product.brand, product.pattern, product.color, product.ptype))
                title = " ".join(
                    (product.brand, product.pattern, product.color, product.ptype))
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

                if product.width != None and product.width != "":
                    desc += "Width: {}<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {}<br/>".format(product.height)
                if product.depth != None and product.depth != "":
                    desc += "Depth: {}<br/><br/>".format(product.depth)

                if product.material != None and product.material != "":
                    desc += "Material: {}<br/>".format(product.material)
                if product.care != None and product.care != "":
                    desc += "Finish: {}<br/>".format(product.care)

                if product.features != None and product.features != "":
                    desc += "Feature: {}<br/><br/>".format(product.features)
                if product.specs != None and product.specs != "":
                    desc += "Feature: {}<br/><br/>".format(product.specs)

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
                    debug("CoutureLamps", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                try:
                    productType = Type.objects.get(name=product.ptype)
                except Type.DoesNotExist:
                    productType = Type.objects.get(name="Accents")

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
                productId = shopify.NewProductBySku(product.sku, con)
                if productId == None:
                    continue

                product.productId = productId
                product.save()

                debug("CoutureLamps", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = CoutureLamps.objects.all()

        idx = 0
        total = len(products)
        for product in products:
            idx += 1
            try:
                if product.productId == None:
                    continue

                name = " | ".join(
                    (product.brand, product.pattern, product.color, product.ptype))
                title = " ".join(
                    (product.brand, product.pattern, product.color, product.ptype))
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

                if product.width != None and product.width != "":
                    desc += "Width: {}<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {}<br/>".format(product.height)
                if product.depth != None and product.depth != "":
                    desc += "Depth: {}<br/><br/>".format(product.depth)

                if product.material != None and product.material != "":
                    desc += "Material: {}<br/>".format(product.material)
                if product.care != None and product.care != "":
                    desc += "Finish: {}<br/>".format(product.care)

                if product.features != None and product.features != "":
                    desc += "Feature: {}<br/><br/>".format(product.features)
                if product.specs != None and product.specs != "":
                    desc += "Feature: {}<br/><br/>".format(product.specs)

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
                    debug("CoutureLamps", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                try:
                    productType = Type.objects.get(name=product.ptype)
                except Type.DoesNotExist:
                    productType = Type.objects.get(name="Accents")

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

                debug("CoutureLamps", 0, "{}/{}: Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    idx, total, productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = CoutureLamps.objects.all()
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

                debug("CoutureLamps", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("CoutureLamps", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

            if subtypes != None and subtypes != "":
                csr.execute("CALL AddToEditSubtype ({}, {})".format(
                    sq(sku), sq(str(subtypes).strip())))
                con.commit()

                debug("CoutureLamps", 0,
                      "Added Subtype. SKU: {}, Subtype: {}".format(sku, sq(subtypes)))

            if collection != None and collection != "":
                csr.execute("CALL AddToEditCollection ({}, {})".format(
                    sq(sku), sq(collection)))
                con.commit()

                debug("CoutureLamps", 0, "Added Collection. SKU: {}, Collection: {}".format(
                    sku, sq(collection)))

        csr.close()
        con.close()

    def downloadInvFile(self):
        debug("CoutureLamps", 0, "Download New CSV from CoutureLamps FTP")

        host = "18.206.49.64"
        port = 22
        username = "couture"
        password = "Couture123!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("CoutureLamps", 2, "Connection to CoutureLamps FTP Server Failed")
            return False

        try:
            sftp.chdir(path='/couture')
            files = sftp.listdir()
        except:
            debug("CoutureLamps", 1, "No New Inventory File")
            return False

        for file in files:
            sftp.get(file, FILEDIR + '/files/couture-lamps-inventory.xlsm')
            sftp.remove(file)

        sftp.close()

        debug("CoutureLamps", 0, "CoutureLamps FTP Inventory Download Completed")
        return True

    def updateStock(self):
        if not self.downloadInvFile():
            return

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # csr.execute(
        #     "DELETE FROM ProductInventory WHERE Brand = 'Couture'")
        # con.commit()

        wb = xlrd.open_workbook(
            FILEDIR + '/files/couture-lamps-inventory.xlsm')
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            mpn = str(sh.cell_value(i, 0)).strip()
            stock = int(sh.cell_value(i, 1))

            boDate = sh.cell_value(i, 2)
            if boDate:
                date_tuple = xlrd.xldate_as_tuple(boDate, wb.datemode)
                date_obj = datetime(*date_tuple)
                boDate = date_obj.date()

            try:
                product = CoutureLamps.objects.get(mpn=mpn)
            except CoutureLamps.DoesNotExist:
                continue

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Couture')".format(
                    product.sku, stock, boDate))
                con.commit()
                debug("CoutureLamps", 0,
                      "Updated inventory for {} to {}. boDate: {}".format(product.sku, stock, boDate))
            except Exception as e:
                print(e)
                debug(
                    "CoutureLamps", 2, "Error Updating inventory for {} to {}.".format(product.sku, stock))

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Couture');""")

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
                product = CoutureLamps.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
                map = product.map
            except:
                debug("CoutureLamps", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(map, 1)
                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("CoutureLamps", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("CoutureLamps", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("CoutureLamps", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def image(self):
        fnames = os.listdir(FILEDIR + "/files/images/couturelamps/")

        products = CoutureLamps.objects.all()
        for product in products:
            mpnStr = product.mpn

            for fname in fnames:
                if ".jpg" in fname.lower() and mpnStr in fname:
                    copyfile(FILEDIR + "/files/images/couturelamps/" + fname, FILEDIR +
                             "/../../images/product/{}.jpg".format(product.productId))
