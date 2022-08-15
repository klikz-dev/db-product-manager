from timeit import repeat
from django.core.management.base import BaseCommand
from brands.models import Mindthegap

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

markup_price = markup.mindthegap
markup_trade = markup.mindthegap_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build MindTheGap Database'

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

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def getProducts(self):
        Mindthegap.objects.all().delete()

        fabricFile = xlrd.open_workbook(
            FILEDIR + "/files/mainthegap-fabric-master.xlsx")
        fabricSheet = fabricFile.sheet_by_index(0)

        wallpaperFile = xlrd.open_workbook(
            FILEDIR + "/files/mainthegap-wallpaper-master.xlsx")
        wallpaperSheet = wallpaperFile.sheet_by_index(0)

        for i in range(1, fabricSheet.nrows):
            mpn = str(fabricSheet.cell_value(i, 1))
            sku = "MTG {}".format(mpn)

            try:
                Mindthegap.objects.get(mpn=mpn)
                continue
            except Mindthegap.DoesNotExist:
                pass

            brand = "MindTheGap"
            ptype = "Fabric"

            collection = str(fabricSheet.cell_value(i, 11))

            pattern = str(fabricSheet.cell_value(i, 4)).strip()
            color = str(fabricSheet.cell_value(i, 15)).strip()

            if mpn == '' or pattern == '' or color == '':
                continue

            cost = float(
                str(fabricSheet.cell_value(i, 6)).replace("$", ""))
            msrp = float(
                str(fabricSheet.cell_value(i, 7)).replace("$", ""))

            minimum = 1
            increment = ""

            uom = "Per Meter"

            content = str(fabricSheet.cell_value(i, 3))
            size = str(fabricSheet.cell_value(i, 5))
            usage = str(fabricSheet.cell_value(i, 13))
            repeat = str(fabricSheet.cell_value(i, 14))
            material = str(fabricSheet.cell_value(i, 8))
            description = str(fabricSheet.cell_value(i, 9))

            instruction = str(fabricSheet.cell_value(i, 16))
            country = str(fabricSheet.cell_value(i, 17))

            style = usage
            colors = color
            category = usage

            manufacturer = "{} {}".format(brand, ptype)

            Mindthegap.objects.create(
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
                repeat=repeat,
                instruction=instruction,
                description=description,
                content=content,
                material=material,
                country=country,
                cost=cost,
                msrp=msrp
            )

            debug("MindTheGap", 0,
                  "Success to get product details for MPN: {}".format(mpn))

        for i in range(1, wallpaperSheet.nrows):
            mpn = str(wallpaperSheet.cell_value(i, 2))
            sku = "MTG {}".format(mpn)

            try:
                Mindthegap.objects.get(mpn=mpn)
                continue
            except Mindthegap.DoesNotExist:
                pass

            brand = "MindTheGap"
            ptype = "Wallpaper"

            collection = str(wallpaperSheet.cell_value(i, 0))

            pattern = str(wallpaperSheet.cell_value(i, 3)).strip()
            color = str(wallpaperSheet.cell_value(i, 12)).strip()

            if mpn == '' or pattern == '' or color == '':
                continue

            cost = float(
                str(fabricSheet.cell_value(i, 5)).replace("$", ""))
            msrp = float(
                str(fabricSheet.cell_value(i, 6)).replace("$", ""))

            minimum = 1
            increment = ""

            uom = "Per 3 Rolls in a box"

            size = str(wallpaperSheet.cell_value(i, 4))
            usage = "Wallcovering"
            repeat = str(wallpaperSheet.cell_value(i, 13))
            material = str(wallpaperSheet.cell_value(i, 9))
            description = str(wallpaperSheet.cell_value(i, 18))
            rollLength = "52cm width and 300cm in length"

            weight = 2.2

            country = str(wallpaperSheet.cell_value(i, 14))

            style = str(wallpaperSheet.cell_value(i, 7))
            colors = color
            category = str(wallpaperSheet.cell_value(i, 7))

            manufacturer = "{} {}".format(brand, ptype)

            Mindthegap.objects.create(
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
                repeat=repeat,
                rollLength=rollLength,
                description=description,
                material=material,
                country=country,
                weight=weight,
                cost=cost,
                msrp=msrp
            )

            debug("Mindthegap", 0,
                  "Success to get product details for MPN: {}".format(mpn))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'MindTheGap')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = Mindthegap.objects.get(mpn=mpn)
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
                        "Mindthegap", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Mindthegap", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except Mindthegap.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Mindthegap", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("Mindthegap", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Mindthegap.objects.all()

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
                if product.rollLength != None and product.rollLength != "":
                    desc += "Roll Length: {}<br/>".format(
                        product.rollLength)
                if product.repeat != None and product.repeat != "":
                    desc += "Repeat: {}<br/>".format(product.repeat)
                if product.material != None and product.material != "":
                    desc += "Material: {}<br/>".format(
                        product.material)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.instruction != None and product.instruction != "":
                    desc += "Care Instructions: {} < br/>".format(
                        product.instruction)
                if product.country != None and product.country != "":
                    desc += "Country of Origin: {}<br/>".format(
                        product.country)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Mindthegap", 1,
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

                debug("Mindthegap", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()
