from datetime import datetime
from shutil import copyfile
from django.core.management.base import BaseCommand
from brands.models import ElaineSmith

import os
import pymysql
import xlrd
import time

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.elainesmith
markup_trade = markup.elainesmith_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Elaine Smith Database'

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

        if "image" in options['functions']:
            self.image()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "updateSizeTags" in options['functions']:
            self.updateSizeTags()

        if "main" in options['functions']:
            self.getProducts()
            self.getProductIds()
            self.updateStock()

    def getProducts(self):
        ElaineSmith.objects.all().delete()

        elainesmithFile = xlrd.open_workbook(
            FILEDIR + "/files/elainesmith-master.xlsx")
        elainesmithSheet = elainesmithFile.sheet_by_index(0)

        for i in range(1, elainesmithSheet.nrows):
            mpn = str(elainesmithSheet.cell_value(i, 0))
            sku = "ES {}".format(mpn)

            try:
                ElaineSmith.objects.get(mpn=mpn)
                continue
            except ElaineSmith.DoesNotExist:
                pass

            brand = "Elaine Smith"
            ptype = "Pillow"

            collection = ''

            pattern = str(elainesmithSheet.cell_value(i, 1)).strip()
            color = str(elainesmithSheet.cell_value(i, 16)).strip()

            if mpn == '' or pattern == '' or color == '':
                continue

            cost = round(float(
                str(elainesmithSheet.cell_value(i, 4)).replace("$", "")), 2)
            map = round(float(
                str(elainesmithSheet.cell_value(i, 5)).replace("$", "")), 2)
            msrp = round(float(
                str(elainesmithSheet.cell_value(i, 6)).replace("$", "")), 2)

            minimum = 1
            increment = ""

            uom = "Per Item"

            size = str(elainesmithSheet.cell_value(i, 2)).strip()
            usage = "Pillow"
            description = str(elainesmithSheet.cell_value(i, 15)).strip()

            thumbnail = elainesmithSheet.cell_value(i, 7)
            roomset1 = elainesmithSheet.cell_value(i, 8)
            roomset2 = elainesmithSheet.cell_value(i, 9)
            roomset3 = elainesmithSheet.cell_value(i, 10)
            roomset4 = elainesmithSheet.cell_value(i, 11)
            roomset5 = elainesmithSheet.cell_value(i, 12)
            roomset6 = elainesmithSheet.cell_value(i, 13)
            roomset7 = elainesmithSheet.cell_value(i, 14)

            weight = 1

            style = "{}, {}".format(str(elainesmithSheet.cell_value(
                i, 17)), str(elainesmithSheet.cell_value(i, 18)))
            category = "Outdoor," + style
            colors = color

            manufacturer = "{} {}".format(brand, ptype)

            ElaineSmith.objects.create(
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
                size=size,
                description=description,
                cost=cost,
                map=map,
                msrp=msrp,
                weight=weight,
                thumbnail=thumbnail,
                roomset1=roomset1,
                roomset2=roomset2,
                roomset3=roomset3,
                roomset4=roomset4,
                roomset5=roomset5,
                roomset6=roomset6,
                roomset7=roomset7,
            )

            debug("Elaine Smith", 0,
                  "Success to get product details for MPN: {}".format(mpn))

        # Update Inventory
        elainesmithInventoryFile = xlrd.open_workbook(
            FILEDIR + "/files/elainesmith-inventory.xlsx")
        elainesmithInventorySheet = elainesmithInventoryFile.sheet_by_index(0)

        for i in range(1, elainesmithInventorySheet.nrows):
            mpn = str(elainesmithInventorySheet.cell_value(i, 0))

            try:
                product = ElaineSmith.objects.get(mpn=mpn)
            except ElaineSmith.DoesNotExist:
                continue

            statusText = str(elainesmithInventorySheet.cell_value(i, 3))

            status = True
            boDate = ""

            if "discontinued" in statusText.lower():
                status = False
            elif "in stock" in statusText.lower():
                pass
            else:
                boDateTuple = xlrd.xldate_as_tuple(
                    elainesmithInventorySheet.cell_value(i, 3), elainesmithInventoryFile.datemode)
                boDate = datetime(*boDateTuple)
                boDate = boDate.strftime("%m/%d/%Y")

            product.status = status
            product.boDate = boDate
            product.save()

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Elaine Smith')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = ElaineSmith.objects.get(mpn=mpn)
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
                        "Elaine Smith", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Elaine Smith", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except ElaineSmith.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Elaine Smith", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("Elaine Smith", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = ElaineSmith.objects.all()

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
                gtin = ""
                weight = product.weight

                desc = ""
                if product.description != None and product.description != "":
                    desc += "{}<br/><br/>".format(
                        product.description)
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.size != None and product.size != "":
                    desc += "Size: {}<br/>".format(product.size)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Elaine Smith", 1,
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

                debug("Elaine Smith", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

                # Download Image
                if product.thumbnail != "":
                    try:
                        common.picdownload2(
                            str(product.thumbnail).strip(), "{}.jpg".format(productId))
                    except Exception as e:
                        print(e)

                # Download Roomsets
                idx = 2

                if product.roomset1 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset1).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset2 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset2).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset3 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset3).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset4 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset4).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset5 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset5).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset6 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset6).strip(), "{}_{}.jpg".format(productId, idx))
                    except Exception as e:
                        print(e)

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = ElaineSmith.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                name = " | ".join((product.brand, product.pattern,
                                  product.color, product.ptype))
                title = " ".join((product.brand, product.pattern,
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
                if product.size != None and product.size != "":
                    desc += "Size: {}<br/>".format(product.size)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Elaine Smith", 1,
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

                debug("Elaine Smith", 0, "Update ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

                # Download Image
                if product.thumbnail != "":
                    try:
                        common.picdownload2(
                            str(product.thumbnail).strip(), "{}.jpg".format(productId))
                    except Exception as e:
                        print(e)

                # Download Roomsets
                idx = 2

                if product.roomset1 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset1).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset2 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset2).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset3 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset3).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset4 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset4).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset5 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset5).strip(), "{}_{}.jpg".format(productId, idx))
                        idx += 1
                    except Exception as e:
                        print(e)

                if product.roomset6 != "":
                    try:
                        common.roomdownload(
                            str(product.roomset6).strip(), "{}_{}.jpg".format(productId, idx))
                    except Exception as e:
                        print(e)

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = ElaineSmith.objects.all()
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

                debug("Elaine Smith", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(sty)))

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("Elaine Smith", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if colors != None and colors != "":
                col = str(colors).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("Elaine Smith", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

        csr.close()
        con.close()

    def updateSizeTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = ElaineSmith.objects.all()
        for product in products:
            sku = product.sku
            ptype = product.ptype
            size = product.size

            if size != None and size != "" and ptype == "Pillow":
                csr.execute("CALL AddToEditSize ({}, {})".format(
                    sq(sku), sq(size)))
                con.commit()

                debug("Elaine Smith", 0,
                      "Added Size. SKU: {}, Size: {}".format(sku, sq(size)))

        csr.close()
        con.close()

    def image(self):
        images = os.listdir(FILEDIR + "/files/images/elainesmith/images")

        products = ElaineSmith.objects.all()
        for product in products:
            productId = product.productId

            if "{}.jpg".format(product.mpn) in images:
                print("{}.jpg".format(product.mpn))

                copyfile(FILEDIR + "/files/images/elainesmith/images/{}.jpg".format(product.mpn), FILEDIR +
                         "/../../images/product/{}.jpg".format(productId))

                os.remove(
                    FILEDIR + "/files/images/elainesmith/images/{}.jpg".format(product.mpn))

    def roomset(self):
        images = os.listdir(FILEDIR + "/files/images/elainesmith/roomset")

        for image in images:
            image = image.replace(".jpg", "")

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Elaine Smith'")
        con.commit()

        products = ElaineSmith.objects.all()

        for product in products:
            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 3, '{}', 'Elaine Smith')".format(
                    product.sku, 5, product.boDate))
                con.commit()
                debug("Elaine Smith", 0,
                      "Updated inventory for {} to {}.".format(product.sku, 5))
            except Exception as e:
                print(e)
                debug(
                    "Elaine Smith", 1, "Error Updating inventory for {} to {}.".format(product.sku, 5))

        csr.close()
        con.close()
