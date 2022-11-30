from timeit import repeat
from django.core.management.base import BaseCommand
from brands.models import Mindthegap

import os
import pymysql
import xlrd
import time
import paramiko

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

        if "updateSizeTags" in options['functions']:
            self.updateSizeTags()

        if "updateStock" in options['functions']:
            self.updateStock()

        if "images" in options['functions']:
            self.images()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def getProducts(self):
        Mindthegap.objects.all().delete()

        fabricFile = xlrd.open_workbook(
            FILEDIR + "/files/mindthegap-fabric-master.xlsx")
        fabricSheet = fabricFile.sheet_by_index(0)

        wallpaperFile = xlrd.open_workbook(
            FILEDIR + "/files/mindthegap-wallpaper-master.xlsx")
        wallpaperSheet = wallpaperFile.sheet_by_index(0)

        pillowFile = xlrd.open_workbook(
            FILEDIR + "/files/mindthegap-pillow-master.xlsx")
        pillowSheet = pillowFile.sheet_by_index(0)

        for i in range(1, fabricSheet.nrows):
            mpn = str(fabricSheet.cell_value(i, 0))
            sku = "MTG {}".format(mpn)

            try:
                Mindthegap.objects.get(mpn=mpn)
                continue
            except Mindthegap.DoesNotExist:
                pass

            brand = "MindTheGap"
            ptype = "Fabric"

            collection = str(fabricSheet.cell_value(i, 10))

            pattern = str(fabricSheet.cell_value(i, 3)).strip()
            color = str(fabricSheet.cell_value(i, 15)).strip()

            if mpn == '' or pattern == '' or color == '':
                continue

            cost = float(
                str(fabricSheet.cell_value(i, 5)).replace("$", "")) / 2
            msrp = float(
                str(fabricSheet.cell_value(i, 7)).replace("$", ""))

            minimum = 2
            increment = ""

            uom = "Per Yard"

            content = str(fabricSheet.cell_value(i, 2))
            # size = "{} cm".format(str(fabricSheet.cell_value(i, 4)))
            usage = str(fabricSheet.cell_value(i, 13))
            repeat = str(fabricSheet.cell_value(i, 14))
            material = str(fabricSheet.cell_value(i, 8))
            description = str(fabricSheet.cell_value(i, 9))

            instruction = str(fabricSheet.cell_value(i, 16))
            country = str(fabricSheet.cell_value(i, 17))

            style = "Global, {}".format(usage)
            colors = color
            category = "Boho, {}".format(usage)

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
                # size=size,
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
            color = str(wallpaperSheet.cell_value(i, 13)).strip()

            if mpn == '' or pattern == '' or color == '':
                continue

            cost = float(
                str(wallpaperSheet.cell_value(i, 6)).replace("$", ""))
            msrp = float(
                str(wallpaperSheet.cell_value(i, 7)).replace("$", ""))

            minimum = 1
            increment = ""

            uom = "Per Roll"

            if "Designer" in wallpaperSheet.cell_value(i, 1):
                size = "One full roll is the quantity purchased. One full roll measures 20.5 inches wide x 9.83 yards long. <br>The full roll is pre-cut and packaged into 3 small rolls to facilitate hanging which measure 20.5 inches wide x 3.28 yards long. <br>Each Pre-Cut Roll Width: 20.5 Inches. <br>Each Pre-Cut Roll Length:: 3.28 Yards"
                rollLength = 9.83
            elif "Complementary" in wallpaperSheet.cell_value(i, 1):
                size = 'sold as a single 20.5" wide x 10.9 yard roll'
                rollLength = 10.9
            else:
                continue

            usage = "Wallcovering"
            repeat = str(wallpaperSheet.cell_value(i, 14))
            material = str(wallpaperSheet.cell_value(i, 10))
            description = str(wallpaperSheet.cell_value(i, 19))

            weight = 2.2

            country = str(wallpaperSheet.cell_value(i, 15))

            style = "Global, {}".format(str(wallpaperSheet.cell_value(i, 8)))
            colors = color
            category = "Boho, {}".format(str(wallpaperSheet.cell_value(i, 8)))

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

        for i in range(1, pillowSheet.nrows):
            mpn = str(pillowSheet.cell_value(i, 0))
            sku = "MTG {}".format(mpn)

            try:
                Mindthegap.objects.get(mpn=mpn)
                continue
            except Mindthegap.DoesNotExist:
                pass

            brand = "MindTheGap"
            ptype = "Pillow"

            collection = str(pillowSheet.cell_value(i, 13))

            pattern = str(pillowSheet.cell_value(i, 3)).strip()
            color = str(pillowSheet.cell_value(i, 7)
                        ).strip().replace(", ", "/")

            if mpn == '' or pattern == '' or color == '':
                continue

            cost = float(
                str(pillowSheet.cell_value(i, 8)).replace("$", ""))
            msrp = float(
                str(pillowSheet.cell_value(i, 9)).replace("$", ""))

            minimum = 1
            increment = ""

            uom = "Per Item"

            size = '{}"'.format(
                str(pillowSheet.cell_value(i, 5)).replace(",", ".")).replace("x", '" x ')
            usage = "Pillow"
            material = str(pillowSheet.cell_value(i, 10))
            description = str(pillowSheet.cell_value(i, 11))

            instruction = str(pillowSheet.cell_value(i, 15))
            country = str(pillowSheet.cell_value(i, 18))

            colors = color

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
                colors=colors,
                size=size,
                instruction=instruction,
                description=description,
                material=material,
                country=country,
                cost=cost,
                msrp=msrp
            )

            debug("MindTheGap", 0,
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
                    desc += "Care Instructions: {} <br/>".format(
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
                if productId == None:
                    continue

                product.productId = productId
                product.save()

                debug("Mindthegap", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Mindthegap.objects.all()

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
                    desc += "Care Instructions: {} <br/>".format(
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
                productId = product.productId

                csr.execute(
                    "CALL AddToPendingUpdateProduct ({})".format(productId))
                con.commit()

                debug("Mindthegap", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def images(self):
        host = "18.206.49.64"
        port = 22
        username = "mindthegap"
        password = "DecbestMTG123!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Brewster", 2, "Connection to Brewster FTP Server Failed")
            return False

        sftp.chdir(path='/mindthegap')

        try:
            files = sftp.listdir()
        except:
            debug("MadcapCottage", 1, "No New Inventory File")
            return False

        for file in files:
            if "_" in file:
                try:
                    mpn = str(file).split("_")[0]
                    roomId = int(str(file).split("_")[1].split(".")[0]) + 1
                except Exception as e:
                    print(e)
                    continue

                try:
                    product = Mindthegap.objects.get(mpn=mpn)
                except Mindthegap.DoesNotExist:
                    continue

                sftp.get(file, FILEDIR +
                         '/../../images/roomset/{}_{}.jpg'.format(product.productId, roomId))

            else:
                try:
                    mpn = str(file).split(".")[0]
                except Exception as e:
                    print(e)
                    continue

                try:
                    product = Mindthegap.objects.get(mpn=mpn)
                except Mindthegap.DoesNotExist:
                    continue

                sftp.get(file, FILEDIR +
                         '/../../images/product/{}.jpg'.format(product.productId))

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Mindthegap.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(category)))
                con.commit()

                debug("Mindthegap", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("Mindthegap", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("Mindthegap", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

        csr.close()
        con.close()

    def updateSizeTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Mindthegap.objects.all()
        for product in products:
            sku = product.sku
            ptype = product.ptype
            size = product.size

            if size != None and size != "" and ptype == "Pillow":
                csr.execute("CALL AddToEditSize ({}, {})".format(
                    sq(sku), sq(size)))
                con.commit()

                debug("Mindthegap", 0,
                      "Added Size. SKU: {}, Size: {}".format(sku, sq(size)))

        csr.close()
        con.close()

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Mindthegap'")
        con.commit()

        host = "18.206.49.64"
        port = 22
        username = "mindthegap"
        password = "DecbestMTG123!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Brewster", 2, "Connection to Brewster FTP Server Failed")
            return False

        sftp.chdir(path='/mindthegap/Inventory')
        files = sftp.listdir()
        for file in files:
            if "cushions" in file:
                sftp.get(file, FILEDIR +
                         '/files/mindthegap-pillow-inventory.xlsx')
            if "fabrics" in file:
                sftp.get(file, FILEDIR +
                         '/files/mindthegap-fabric-inventory.xlsx')

        fabricFile = xlrd.open_workbook(
            FILEDIR + "/files/mindthegap-fabric-inventory.xlsx")
        pillowFile = xlrd.open_workbook(
            FILEDIR + "/files/mindthegap-pillow-inventory.xlsx")
        fabricSheet = fabricFile.sheet_by_index(0)
        pillowSheet = pillowFile.sheet_by_index(0)

        for i in range(1, fabricSheet.nrows):
            try:
                mpn = str(fabricSheet.cell_value(i, 1))
                stock = int(fabricSheet.cell_value(i, 7))

                product = Mindthegap.objects.get(mpn=mpn)
                product.stock = stock
                product.save()
            except:
                continue

        for i in range(1, pillowSheet.nrows):
            try:
                mpn = str(pillowSheet.cell_value(i, 1))
                stock = int(pillowSheet.cell_value(i, 5))

                product = Mindthegap.objects.get(mpn=mpn)
                product.stock = stock
                product.save()
            except:
                continue

        products = Mindthegap.objects.all()

        for product in products:
            if product.ptype == "Wallpaper":
                try:
                    csr.execute("CALL UpdateProductInventory ('{}', {}, 3, '{}', 'Mindthegap')".format(
                        product.sku, 5, ''))
                    con.commit()
                    debug("Mindthegap", 0,
                          "Updated inventory for {} to {}.".format(product.sku, 5))
                except Exception as e:
                    print(e)
                    debug(
                        "Mindthegap", 1, "Error Updating inventory for {} to {}.".format(product.sku, 5))
            else:
                try:
                    csr.execute("CALL UpdateProductInventory ('{}', {}, 2, '{}', 'Mindthegap')".format(
                        product.sku, product.stock, ''))
                    con.commit()
                    debug("Mindthegap", 0,
                          "Updated inventory for {} to {}.".format(product.sku, product.stock))
                except Exception as e:
                    print(e)
                    debug(
                        "Mindthegap", 1, "Error Updating inventory for {} to {}.".format(product.sku, product.stock))

        csr.close()
        con.close()
