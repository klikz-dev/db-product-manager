from django.core.management.base import BaseCommand
from brands.models import Zoffany

import os
import paramiko
import pymysql
import time
import xlrd
import csv
import codecs
from shutil import copyfile

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.zoffany
markup_trade = markup.zoffany_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Zoffany Database'

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

        if "fixMissingImages" in options['functions']:
            self.fixMissingImages()

        if "updateStock" in options['functions']:
            self.updateStock()

        if "roomset" in options['functions']:
            self.roomset()

        if "bestSellers" in options['functions']:
            self.bestSellers()

        if "main" in options['functions']:
            while True:
                # self.getProducts()
                # self.getProductIds()
                self.updateStock()

                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def getProducts(self):
        Zoffany.objects.all().delete()

        wb = xlrd.open_workbook(
            FILEDIR + "/files/zoffany-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                mpn = str(sh.cell_value(i, 1))

                pattern = str(sh.cell_value(i, 7)).strip()
                color = str(sh.cell_value(i, 8))

                sku = "ZOF {}".format(mpn)

                try:
                    Zoffany.objects.get(mpn=mpn)
                    continue
                except Zoffany.DoesNotExist:
                    pass

                brand = str(sh.cell_value(i, 20)).lower().capitalize()
                collection = str(sh.cell_value(i, 6)).lower().capitalize()

                ptype = str(sh.cell_value(i, 11))
                if ptype == "WP":
                    ptype = "Wallpaper"
                elif ptype == "FB":
                    ptype = "Fabric"
                else:
                    debug("Zoffany", 1, "Produt type error {}".format(mpn))
                    continue

                try:
                    price = round(float(
                        str(sh.cell_value(i, 3)).replace('$', '').strip()), 2)
                    map = round(float(
                        str(sh.cell_value(i, 4)).replace('$', '').strip()), 2)
                    msrp = round(float(
                        str(sh.cell_value(i, 5)).replace('$', '').strip()), 2)
                except:
                    debug("Zoffany", 1, "Produt price error {}".format(mpn))
                    continue

                uom = str(sh.cell_value(i, 10))
                if uom.lower() == "yard":
                    uom = "Per Yard"
                elif uom.lower() == "roll":
                    uom = "Per Roll"
                elif uom.lower() == "panel":
                    uom = "Per Panel"
                else:
                    debug("Zoffany", 1, "Produt uom error {}".format(mpn))
                    continue

                minimum = 2

                # Zoffany has no increment. 1/19 from Barbara
                increment = ''

                usage = str(sh.cell_value(i, 12)).lower().capitalize()
                category = str(sh.cell_value(i, 9)).lower().capitalize()

                try:
                    width = round(float(sh.cell_value(i, 17)), 2)
                except:
                    width = 0
                try:
                    rollLength = round(float(sh.cell_value(i, 16)), 2)
                except:
                    rollLength = 0
                try:
                    hr = round(float(sh.cell_value(i, 19)), 2)
                except:
                    hr = 0
                try:
                    vr = round(float(sh.cell_value(i, 18)), 2)
                except:
                    vr = 0
                match = str(sh.cell_value(i, 13)).lower().capitalize()
                reversible = str(sh.cell_value(i, 14))
                if reversible == "Y":
                    feature = "Reversible: No"
                else:
                    feature = "Reversible: No"
                weight = 1
                description = str(sh.cell_value(i, 24))
                picLink = str(sh.cell_value(i, 23))

                manufacturer = "{} {}".format(brand, ptype)

                keywords = "{}, {}, {}, {}".format(
                    collection, usage, category, description)
                if "outdoor" in keywords.lower():
                    keywords = "{}, Performance Fabric".format(keywords)

                Zoffany.objects.create(
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
                    weight=weight,
                    usage=usage,
                    category=keywords,
                    style=keywords,
                    colors=color,
                    width=width,
                    rollLength=rollLength,
                    hr=hr,
                    vr=vr,
                    match=match,
                    feature=feature,
                    description=description,
                    thumbnail=picLink,
                    cost=price,
                    map=map,
                    msrp=msrp
                )

                debug("Zoffany", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("Zoffany", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Zoffany')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = Zoffany.objects.get(mpn=mpn)
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
                        "Zoffany", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Zoffany", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except Zoffany.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Zoffany", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("Zoffany", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Zoffany.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Zoffany", 1,
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
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                msrp = product.msrp
                map = product.map
                try:
                    if msrp != None and msrp > 0:
                        price = common.formatprice(msrp, 1)
                    else:
                        price = common.formatprice(cost, markup_price)
                        if price < map:
                            price = common.formatprice(map, 1)

                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Zoffany", 2,
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

                if product.thumbnail and product.thumbnail.strip() != "":
                    try:
                        common.picdownload2(
                            product.thumbnail, "{}.jpg".format(product.productId))
                    except Exception as e:
                        print(e)
                        pass

                debug("Zoffany", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Zoffany.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Zoffany", 1,
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
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                msrp = product.msrp
                map = product.map

                try:
                    if msrp != None and msrp > 0:
                        price = common.formatprice(msrp, 1)
                    else:
                        price = common.formatprice(cost, markup_price)
                        if price < map:
                            price = common.formatprice(map, 1)

                    priceTrade = common.formatprice(product.cost, markup_trade)
                except:
                    debug("Zoffany", 2,
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

                if product.thumbnail and product.thumbnail.strip() != "":
                    try:
                        common.picdownload2(
                            product.thumbnail, "{}.jpg".format(productId))
                    except:
                        pass

                debug("Zoffany", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Zoffany.objects.all()

        for product in products:
            mpn = product.mpn
            cost = product.cost
            map = product.map
            msrp = product.msrp
            productId = product.productId

            if productId != "" and productId != None:
                cost = product.cost
                try:
                    if msrp != None and msrp > 0:
                        price = common.formatprice(msrp, 1)
                    else:
                        price = common.formatprice(cost, markup_price)
                        if price < map:
                            price = common.formatprice(map, 1)

                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Zoffany", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99

                try:
                    csr.execute("SELECT PV1.Cost, PV1.Price, PV2.Price AS TradePrice FROM ProductVariant PV1, ProductVariant PV2 WHERE PV1.ProductID = {} AND PV2.ProductID = {} AND PV1.IsDefault = 1 AND PV2.Name LIKE 'Trade - %' AND PV1.Cost IS NOT NULL AND PV2.Cost IS NOT NULL".format(productId, productId))
                    tmp = csr.fetchone()
                    if tmp == None:
                        debug("Zoffany", 2, "Update Price Error: ProductId: {}, MPN: {}".format(
                            productId, mpn))
                        continue
                    oCost = float(tmp[0])
                    oPrice = float(tmp[1])
                    oTrade = float(tmp[2])

                    if cost != oCost or price != oPrice or priceTrade != oTrade:
                        csr.execute("CALL UpdatePriceAndTrade ({}, {}, {}, {})".format(
                            productId, cost, price, priceTrade))
                        con.commit()
                        csr.execute(
                            "CALL AddToPendingUpdatePrice ({})".format(productId))
                        con.commit()

                        debug("Zoffany", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                            productId, cost, price, priceTrade))
                    else:
                        debug("Zoffany", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                            productId, price, priceTrade))

                except:
                    debug("Zoffany", 1, "Updating price error for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                        productId, cost, price, priceTrade))
                    continue

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # Mural Subtypes
        murals = []

        wb = xlrd.open_workbook(
            FILEDIR + "/files/zoffany-master.xlsx")
        sh = wb.sheet_by_index(2)

        for i in range(1, sh.nrows):
            mpn = str(sh.cell_value(i, 1))
            murals.append(mpn)

        products = Zoffany.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("Zoffany", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if style != None and style != "":
                sty = str(style).strip()
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(sty)))
                con.commit()

                debug("Zoffany", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(sty)))

            if colors != None and colors != "":
                col = str(colors).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("Zoffany", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

            if product.mpn in murals:
                csr.execute("CALL AddToEditSubtype ({}, {})".format(
                    sq(sku), sq(str('Murals').strip())))
                con.commit()

                debug("York", 0,
                      "Added Subtype. SKU: {}, Subtype: {}".format(sku, sq('Murals')))

        csr.close()
        con.close()

    def fixMissingImages(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        hasImage = []

        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = 'Zoffany'")
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        products = Zoffany.objects.all()
        for product in products:
            if product.productId == None or product.productId in hasImage:
                continue

            if product.thumbnail and product.thumbnail.strip() != "":
                debug("Zoffany", 0, "Product productID: {} is missing pic. downloading from {}".format(
                    product.productId, product.thumbnail))

                try:
                    common.picdownload2(
                        product.thumbnail, "{}.jpg".format(product.productId))
                except Exception as e:
                    print(e)

        csr.close()
        con.close()

    def downloadcsv(self):
        host = "34.203.121.151"
        port = 22
        username = "zoffany"
        password = "Zof!Dec123"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            print(e)
            return False

        try:
            files = sftp.listdir()
            for file in files:
                sftp.get(file, FILEDIR + '/files/zoffany-inventory.csv')
                sftp.remove(file)

            sftp.close()
            print("Download completed")
            return True
        except:
            return False

    def updateStock(self):
        if not self.downloadcsv():
            return

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM ProductInventory WHERE Brand = 'Zoffany'")
        con.commit()

        f = open(FILEDIR + "/files/zoffany-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))

        index = 0
        for row in cr:
            index += 1
            if index == 1:
                continue

            mpn = str(row[1]).strip()
            sku = "ZOF {}".format(mpn)

            stock = int(float(row[2]))

            stockval = 0
            try:
                stockval = int(float(stock))
            except:
                stockval = 0

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', '{}')".format(
                    sku, stockval, "", 'Zoffany'))
                con.commit()
                print("Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                print("Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def roomset(self):
        fnames = os.listdir(FILEDIR + "/files/images/zoffany/")

        for fname in fnames:
            try:
                if "_" in fname:
                    mpn = fname.split("_")[0]
                    roomId = int(fname.split("_")[1].split(".")[0]) + 1

                    product = Zoffany.objects.get(mpn=mpn)
                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "/files/images/zoffany/" + fname, FILEDIR +
                                 "/../../images/roomset/{}_{}.jpg".format(productId, roomId))

                        debug("Zoffany", 0, "Roomset Image {}_{}.jpg".format(
                            productId, roomId))

                        os.remove(
                            FILEDIR + "/files/images/zoffany/" + fname)
                    else:
                        print("No product found with MPN: {}".format(mpn))
                else:
                    continue

            except Exception as e:
                print(e)
                continue

    def bestSellers(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        wb = xlrd.open_workbook(FILEDIR + "/files/zoffany-bestsellers.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(3, sh.nrows):
            try:
                mpn = str(sh.cell_value(i, 1))
            except:
                continue

            if mpn == 'Product Code' or mpn == '':
                continue

            sku = "ZOF {}".format(mpn)

            try:
                product = Zoffany.objects.get(sku=sku)
            except Zoffany.DoesNotExist:
                continue

            csr.execute("CALL AddToProductTag ({}, {})".format(
                sq(sku), sq("Best Selling")))
            con.commit()

            csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                product.productId))
            con.commit()

            debug('Zoffany', 0, "Added to Best selling. SKU: {}".format(sku))

        csr.close()
        con.close()
