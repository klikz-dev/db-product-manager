from django.core.management.base import BaseCommand
from brands.models import RalphLauren

import os
import sys
import pymysql
import urllib.request
import zipfile
import csv
import codecs
import time
import xlrd

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = env('MYSQL_PORT')

markup_price = markup.ralphLauren
markup_trade = markup.ralphLauren_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build RalphLauren Database'

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

        if "discoSamples" in options['functions']:
            self.discoSamples()

        if "updateStock" in options['functions']:
            while True:
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def downloadcsv(self):

        if os.path.isfile(FILEDIR + "/files/item_info.csv"):
            os.remove(FILEDIR + "/files/item_info.csv")
        if os.path.isfile(FILEDIR + "/files/decbest.zip"):
            os.remove(FILEDIR + "/files/decbest.zip")

        try:
            urllib.request.urlretrieve(
                "ftp://decbest:mArker999@file.kravet.com/decbest.zip", FILEDIR + "/files/decbest.zip")
            z = zipfile.ZipFile(FILEDIR + "/files/decbest.zip", "r")
            z.extractall(FILEDIR + "/files/")
            z.close()
        except Exception as e:
            debug("RalphLauren", 2, "Download Failed. Exiting")
            print(e)
            return False

        debug("RalphLauren", 0, "Download Completed")
        return True

    def getProducts(self):
        if not self.downloadcsv():
            sys.exit(2)

        RalphLauren.objects.all().delete()

        sample_available = []

        # 4/8 from BK: All RL products don't have samples

        # wb = xlrd.open_workbook(FILEDIR + "/files/rl-price.xlsx")
        # sh = wb.sheet_by_index(0)

        # for i in range(6, sh.nrows):
        #     sku = str(sh.cell_value(i, 3)).strip()
        #     sample_available.append(sku)

        f = open(FILEDIR + "/files/item_info.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            try:
                if row[3] == "RALPH LAUREN":
                    brand = "Ralph Lauren"
                else:
                    continue

                temp = row[0].strip().split(".")

                if len(temp) != 3 or temp[2] != "0":
                    continue
                if row[12] == "LEATHER - 100%":
                    continue

                mpn = row[0].strip()
                collection = row[16]
                picLoc = row[25]

                sku = row[0].replace(".RL.0", "")

                try:
                    RalphLauren.objects.get(mpn=mpn)
                    continue
                except RalphLauren.DoesNotExist:
                    pass

                try:
                    RalphLauren.objects.create(
                        mpn=mpn,
                        sku=sku,
                        brand=brand
                    )
                    product = RalphLauren.objects.get(mpn=mpn)
                except:
                    print("create object error")
                    continue

                if row[1] == "." or row[1] == ".." or row[1] == "..." or row[1] == "" or row[1].find("KF ") >= 0 or "KRAVET " in row[1]:
                    product.pattern = temp[0]
                else:
                    product.pattern = row[1]

                try:
                    if row[2] == "." or row[2] == "" or row[2] == "NONE" or "KRAVET " in row[1]:
                        product.color = temp[1]
                    else:
                        product.color = row[2]
                except:
                    pass

                if row[17] == "WALLCOVERING":
                    product.ptype = "Wallpaper"
                elif row[17] == "TRIM":
                    product.ptype = "Trim"
                else:
                    product.ptype = "Fabric"

                product.usage = row[17]

                try:
                    product.vr = float(row[4])
                except:
                    product.vr = 0

                try:
                    product.hr = float(row[5])
                except:
                    product.hr = 0

                try:
                    product.width = float(row[7])
                except:
                    product.width = 0

                try:
                    product.cost = float(str(row[10]).strip())
                    if row[32] != "":
                        product.cost = float(str(row[32]).strip())
                except:
                    debug("Kravet", 1, "Price Error for MPN: {}".format(mpn))
                    continue

                product.content = row[12]
                product.collection = collection

                product.uom = "Per " + row[11]
                if row[11] == "ROLL":
                    product.uom = "Per Roll"
                elif row[11] == "YARD":
                    product.uom = "Per Yard"
                elif row[11] == "EACH":
                    product.uom = "Per Item"
                elif row[11] == "SQUARE FOOT":
                    product.uom = "Per Square Foot"
                else:
                    debug("Kravet", 1, "UOM Error for MPN: {}".format(mpn))
                    continue

                product.category = ",".join((row[20], row[21]))
                product.colors = ",".join((row[26], row[27], row[28]))
                product.weight = " ".join((row[29], row[30]))
                product.statusText = row[31]

                try:
                    product.rollLength = float(row[37])
                except:
                    product.rollLength = 0

                try:
                    product.minimum = int(float(row[38]))
                except:
                    product.minimum = 1
                    pass
                try:
                    if int(float(row[39])) > 1:
                        product.increment = ",".join(
                            [str(ii * int(float(row[39]))) for ii in range(1, 21)])
                except:
                    product.increment = ""
                    pass

                product.thumbnail = picLoc

                # if row[43].strip != "YES":
                #     product.sample = False

                if sku not in sample_available:
                    product.sample = False

                product.manufacturer = "{} {}".format(brand, product.ptype)

                if row[23] == "Out of Stock":
                    product.status = False

                product.stock = int(float(row[46]))

                # 1/24 Disable backorder items
                if int(float(row[46])) < 3:
                    product.status = False

                product.stockNote = row[47]

                product.save()

                debug("RalphLauren", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                debug("RalphLauren", 1,
                      "Failed to get product details for MPN: {}".format(mpn))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Ralph Lauren');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = RalphLauren.objects.get(sku=sku)
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
                        "RalphLauren", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "RalphLauren", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except RalphLauren.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "RalphLauren", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("RalphLauren", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = RalphLauren.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("RalphLauren", 1,
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
                if product.width != None and product.width != "" and float(product.width) != 0:
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Height: {} in<br/>".format(product.height)
                if product.hr != None and product.hr != "" and float(product.hr) != 0:
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "" and float(product.vr) != 0:
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("RalphLauren", 2,
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

                if product.roomset and product.roomset.strip() != "":
                    try:
                        common.roomdownload(
                            product.roomset, "{}_2.jpg".format(product.productId))
                    except Exception as e:
                        print(e)
                        pass

                debug("RalphLauren", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = RalphLauren.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("RalphLauren", 1,
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
                if product.width != None and product.width != "" and float(product.width) != 0:
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Height: {} in<br/>".format(product.height)
                if product.hr != None and product.hr != "" and float(product.hr) != 0:
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "" and float(product.vr) != 0:
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("RalphLauren", 2,
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

                debug("RalphLauren", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = RalphLauren.objects.all()

        for product in products:
            mpn = product.mpn
            cost = product.cost
            productId = product.productId

            if productId != "" and productId != None:
                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("RalphLauren", 1,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99

                try:
                    csr.execute("SELECT PV1.Cost, PV1.Price, PV2.Price AS TradePrice FROM ProductVariant PV1, ProductVariant PV2 WHERE PV1.ProductID = {} AND PV2.ProductID = {} AND PV1.IsDefault = 1 AND PV2.Name LIKE 'Trade - %' AND PV1.Cost IS NOT NULL AND PV2.Cost IS NOT NULL".format(productId, productId))
                    tmp = csr.fetchone()
                    if tmp == None:
                        debug("RalphLauren", 2, "Update Price Error: ProductId: {}, MPN: {}".format(
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

                        debug("RalphLauren", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                            productId, cost, price, priceTrade))
                    else:
                        debug("RalphLauren", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                            productId, price, priceTrade))
                except:
                    debug("RalphLauren", 1, "Updating price error for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                        productId, cost, price, priceTrade))
                    continue

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = RalphLauren.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            color = product.color

            if category != None and category != "":
                categories = str(category).split(",")
                for cat in categories:
                    cat = str(cat).strip()
                    csr.execute("CALL AddToEditCategory ({}, {})".format(
                        sq(sku), sq(cat)))
                    con.commit()

                    debug("RalphLauren", 0, "Added Category. SKU: {}, Category: {}".format(
                        sku, sq(cat)))

            if color != None and color != "":
                colors = str(color).split(",")
                for col in colors:
                    col = str(col).strip()
                    csr.execute("CALL AddToEditColor ({}, {})".format(
                        sq(sku), sq(col)))
                    con.commit()

                    debug("RalphLauren", 0,
                          "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

        csr.close()
        con.close()

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Ralph Lauren'")
        con.commit()

        products = RalphLauren.objects.all()

        for product in products:
            sku = product.sku
            stock = product.stock
            if stock < 3:
                stock = 0

            leadtime = "{} days".format(product.stockNote)

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Ralph Lauren')".format(
                    sku, stock, leadtime))
                con.commit()
                debug("RalphLauren", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug(
                    "RalphLauren", 2, "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def discoSamples(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = RalphLauren.objects.all()
        for product in products:
            sku = product.sku

            if product.sample == False and product.productId:
                csr.execute("CALL AddToProductTag ({}, {})".format(
                    sq(sku), sq("NoSample")))
                con.commit()

                csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                    product.productId))
                con.commit()

                debug('RalphLauren', 0, "Added No Sample Tag. SKU: {}".format(sku))

        csr.close()
        con.close()
