from shutil import copyfile
from django.core.management.base import BaseCommand
from brands.models import TresTintas

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

markup_price = markup.trestintas
markup_trade = markup.trestintas_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Tres Tintas Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "getProductIds" in options['functions']:
            self.getProductIds()

        if "addNew" in options['functions']:
            self.addNew()

        if "image" in options['functions']:
            self.image()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "updateStock" in options['functions']:
            self.updateStock()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def getProducts(self):
        TresTintas.objects.all().delete()

        trestintasFile = xlrd.open_workbook(
            FILEDIR + "/files/trestintas-master.xlsx")
        trestintasSheet = trestintasFile.sheet_by_index(0)

        for i in range(1, trestintasSheet.nrows):
            try:
                mpn = int(trestintasSheet.cell_value(i, 0))
            except:
                mpn = str(trestintasSheet.cell_value(i, 0))

            sku = "TT {}".format(mpn)

            try:
                TresTintas.objects.get(mpn=mpn)
                continue
            except TresTintas.DoesNotExist:
                pass

            brand = "Tres Tintas"
            ptype = "Wallpaper"

            collection = str(trestintasSheet.cell_value(i, 4)).capitalize()

            pattern = str(trestintasSheet.cell_value(
                i, 5)).strip().capitalize()
            color = str(trestintasSheet.cell_value(i, 6)).strip().lower()

            pattern = pattern.replace(color, "")
            color = color.capitalize()

            colors = color
            color = color.replace(", ", " & ")

            if mpn == '' or pattern == '' or color == '':
                continue

            cost = 50
            map = 149.5

            minimum = 1
            increment = ""

            uom = "Per Roll"

            width = 19.5
            usage = "Wallcovering"
            match = str(trestintasSheet.cell_value(i, 9))
            material = "{} / {}".format(str(trestintasSheet.cell_value(
                i, 11)), str(trestintasSheet.cell_value(i, 12)))
            rollLength = 11
            description = ''

            weight = 1

            style = str(trestintasSheet.cell_value(i, 7))
            category = str(trestintasSheet.cell_value(i, 7))

            manufacturer = "{} {}".format(brand, ptype)

            TresTintas.objects.create(
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
                rollLength=rollLength,
                description=description,
                material=material,
                match=match,
                cost=cost,
                map=map,
                weight=weight
            )

            debug("Tres Tintas", 0,
                  "Success to get product details for MPN: {}".format(mpn))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Tres Tintas')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = TresTintas.objects.get(mpn=mpn)
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
                        "Tres Tintas", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Tres Tintas", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except TresTintas.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Tres Tintas", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("Tres Tintas", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = TresTintas.objects.all()

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
                if product.width != None and product.width != "":
                    desc += "Width: {} in.<br/>".format(product.width)
                if product.rollLength != None and product.rollLength != "":
                    desc += "Roll Length: {} yds<br/>".format(
                        product.rollLength)
                if product.material != None and product.material != "":
                    desc += "Material: {}<br/><br/>".format(
                        product.material)
                if product.match != None and product.match != "":
                    desc += "Match: {}<br/>".format(
                        product.match)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Tres Tintas", 1,
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

                debug("Tres Tintas", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = TresTintas.objects.all()
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

                debug("Tres Tintas", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(sty)))

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("Tres Tintas", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if colors != None and colors != "":
                col = str(colors).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("Tres Tintas", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

        csr.close()
        con.close()

    def image(self):
        images = os.listdir(FILEDIR + "/files/images/trestintas/images")

        products = TresTintas.objects.all()
        for product in products:
            productId = product.productId

            if "{}.jpg".format(product.mpn) in images:
                print("{}.jpg".format(product.mpn))

                copyfile(FILEDIR + "/files/images/trestintas/images/{}.jpg".format(product.mpn), FILEDIR +
                         "/../../images/product/{}.jpg".format(productId))

                os.remove(
                    FILEDIR + "/files/images/trestintas/images/{}.jpg".format(product.mpn))

    def roomset(self):
        images = os.listdir(FILEDIR + "/files/images/trestintas/roomset")

        for image in images:
            image = image.replace(".jpg", "")

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Tres Tintas'")
        con.commit()

        products = TresTintas.objects.all()

        for product in products:
            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 3, '{}', 'Tres Tintas')".format(
                    product.sku, 5, ""))
                con.commit()
                debug("Tres Tintas", 0,
                      "Updated inventory for {} to {}.".format(product.sku, 5))
            except Exception as e:
                print(e)
                debug(
                    "Tres Tintas", 1, "Error Updating inventory for {} to {}.".format(product.sku, 5))

        csr.close()
        con.close()
