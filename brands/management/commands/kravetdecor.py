from django.core.management.base import BaseCommand
from brands.models import KravetDecor
from shopify.models import Product as ShopifyProduct
from mysql.models import Type

import os
import urllib.request
import zipfile
import pymysql
import codecs
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

markup_price = markup.kravetdecor
markup_trade = markup.kravetdecor_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Kravet Decor Database'

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
                print("Completed stock update process. Waiting for next run.")
                time.sleep(86400)

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "main" in options['functions']:
            self.getProducts()
            self.getProductIds()

    def getProducts(self):
        KravetDecor.objects.all().delete()

        f = open(FILEDIR + "/files/kravet-decor-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "sku":
                continue

            mpn = str(row[0]).strip()
            try:
                KravetDecor.objects.get(mpn=mpn)
                debug("KravetDecor", 1,
                      "Produt Already exist. MPN: {}".format(mpn))
                continue
            except KravetDecor.DoesNotExist:
                pass

            sku = "KD {}".format(mpn.replace(".0", "").replace(".", "-"))

            pattern = str(row[1]).strip().replace(",", "")
            color = sku.split("-")[2].title()

            brand = "Kravet Decor"
            ptype = str(row[6]).strip().title()
            manufacturer = "Kravet Decor"
            collection = str(row[3]).strip()

            try:
                cost = round(float(row[15]), 2)
            except:
                debug("KravetDecor", 1, "Produt Cost error {}".format(mpn))
                continue

            uom = "Per Item"
            minimum = 1
            increment = ""

            description = str(row[2]).strip()

            try:
                width = round(float(row[11]), 2)
            except:
                width = 0

            try:
                height = round(float(row[10]), 2)
            except:
                height = 0

            try:
                depth = round(float(row[12]), 2)
            except:
                depth = 0

            features = str(row[25]).strip()

            material = str(row[20]).strip()
            care = str(row[24]).strip()

            country = str(row[21]).strip()
            usage = str(row[5]).strip()

            try:
                weight = round(float(row[14]), 2)
            except:
                weight = 5

            upc = str(row[34]).strip()

            keywords = "{}, {}, {}, {}".format(
                usage, pattern, collection, description)

            style = keywords
            category = keywords
            colors = str(row[7]).strip().replace(";", " / ")

            status = False
            if str(row[4]) == "Active":
                status = True

            stock = 5
            boDate = str(row[18]).strip()

            thumbnail = str(row[35]).strip()

            roomsetsArr = []
            for id in range(36, 40):
                roomset = str(row[id]).strip()
                if roomset != "":
                    roomsetsArr.append(roomset)
            roomsets = "|".join(roomsetsArr)

            # Pattern Name
            ptypeTmp = ptype
            if ptypeTmp[len(ptypeTmp) - 1] == "s":
                ptypeTmp = ptypeTmp[:-1]

            for typeword in ptypeTmp.split(" "):
                pattern = pattern.replace(typeword, "")

            pattern = pattern.replace("  ", " ").strip()
            ##############

            KravetDecor.objects.create(
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

                thumbnail=thumbnail,
                roomsets=roomsets,

                cost=cost,
            )

            debug("KravetDecor", 0,
                  "Success to get product details for MPN: {}".format(mpn))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Kravet Decor')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = KravetDecor.objects.get(mpn=mpn)
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
                        "KravetDecor", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "KravetDecor", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except KravetDecor.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "KravetDecor", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("KravetDecor", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = KravetDecor.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
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
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("KravetDecor", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                if "Pillow" in product.ptype:
                    ptype = "Pillows"
                elif product.ptype == "Benches & Ottomans":
                    ptype = "Furniture"
                else:
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
                productId = shopify.NewProductBySku(product.sku, con)
                if productId == None:
                    continue

                product.productId = productId
                product.save()

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

                debug("KravetDecor", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = KravetDecor.objects.all()

        idx = 0
        total = len(products)
        for product in products:
            idx += 1
            try:
                if product.productId == None:
                    continue

                # Update Mirrors, Accents, Wall Art, Chandeliers
                if product.ptype == "Mirrors" or product.ptype == "Accents" or product.ptype == "Wall Art" or product.ptype == "Chandeliers":
                    pass
                else:
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
                    price = common.formatprice(product.cost, markup_price)
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("KravetDecor", 1,
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

                debug("KravetDecor", 0, "{}/{}: Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    idx, total, productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = KravetDecor.objects.all()
        for product in products:
            sku = product.sku

            # category = product.category
            style = product.style
            colors = product.colors
            subtypes = "{}, {}".format(product.ptype, product.pattern)

            # Hide Category for JY. 1/25/23 from BK.
            # if category != None and category != "":
            #     csr.execute("CALL AddToEditCategory ({}, {})".format(
            #         sq(sku), sq(category)))
            #     con.commit()

            #     debug("KravetDecor", 0, "Added Category. SKU: {}, Category: {}".format(
            #         sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("KravetDecor", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("KravetDecor", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

            if subtypes != None and subtypes != "":
                csr.execute("CALL AddToEditSubtype ({}, {})".format(
                    sq(sku), sq(str(subtypes).strip())))
                con.commit()

                debug("KravetDecor", 0,
                      "Added Subtype. SKU: {}, Subtype: {}".format(sku, sq(subtypes)))

        csr.close()
        con.close()

    def downloadcsv(self):
        if os.path.isfile(FILEDIR + "/files/curated_onhand_info.csv"):
            os.remove(FILEDIR + "/files/curated_onhand_info.csv")
        if os.path.isfile(FILEDIR + "/files/curated_onhand_info.zip"):
            os.remove(FILEDIR + "/files/curated_onhand_info.zip")

        try:
            urllib.request.urlretrieve(
                "ftp://decbest:mArker999@file.kravet.com/curated_onhand_info.zip", FILEDIR + "/files/curated_onhand_info.zip")
            z = zipfile.ZipFile(
                FILEDIR + "/files/curated_onhand_info.zip", "r")
            z.extractall(FILEDIR + "/files/")
            z.close()
        except Exception as e:
            debug("Kravet", 2, "Download Failed. Exiting")
            print(e)
            return False

        debug("KravetDecor", 0, "Download Completed")
        return True

    def updateStock(self):
        if not self.downloadcsv():
            return

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Kravet Decor'")
        con.commit()

        f = open(FILEDIR + "/files/curated_onhand_info.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Item":
                continue

            mpn = str(row[0]).strip()
            stock = int(row[1])

            try:
                product = KravetDecor.objects.get(mpn=mpn)

                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Kravet Decor')".format(
                    product.sku, stock, product.boDate))
                con.commit()
                debug("KravetDecor", 0,
                      "Updated inventory for {} to {}.".format(product.sku, stock))
            except Exception as e:
                print(e)
                debug(
                    "KravetDecor", 1, "Error Updating inventory for {} to {}.".format(product.sku, stock))

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Kravet Decor');""")

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
                product = KravetDecor.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("KravetDecor", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(newCost, markup_price)
                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("KravetDecor", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("KravetDecor", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("KravetDecor", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()
