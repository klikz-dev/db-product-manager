from django.core.management.base import BaseCommand
import xlrd
from brands.models import Kravet
from shopify.models import Product as ShopifyProduct

import os
import pymysql
import urllib.request
import zipfile
import csv
import requests
import codecs
import time
from bs4 import BeautifulSoup

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.kravet
markup_trade = markup.kravet_trade
markup_price_pillow = markup.kravet_pillow
markup_trade_pillow = markup.kravet_pillow_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Kravet Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "getPillowProducts" in options['functions']:
            self.getPillowProducts()

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

        if "updateSizeTags" in options['functions']:
            self.updateSizeTags()

        if "outlet" in options['functions']:
            self.outlet()

        if "fixMissingImages" in options['functions']:
            self.fixMissingImages()

        if "bestSeller" in options['functions']:
            self.bestSeller()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getPillowProducts()
                self.getProductIds()
                self.updateStock()
                print("Completed stock update process. Waiting for next run.")
                time.sleep(43200)

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
            debug("Kravet", 2, "Download Failed. Exiting")
            print(e)
            return False

        debug("Kravet", 0, "Download Completed")
        return True

    def getProducts(self):
        if not self.downloadcsv():
            return

        Kravet.objects.all().delete()

        f = open(FILEDIR + "/files/item_info.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        unknownBrands = []

        for row in cr:
            temp = row[0].strip().split(".")

            if len(temp) != 3 or temp[2] != "0":
                continue
            if row[12] == "LEATHER - 100%":
                continue

            mpn = row[0].strip()
            collection = row[16]

            status = True
            if str(row[22]).strip() != 'Y':
                status = False

            picLoc = str(row[24]).strip()
            if picLoc == "":
                picLoc = str(row[25]).strip()

            if "LEE JOFA" in row[3] or row[3] == "FIRED EARTH" or row[3] == "MONKWELL" or row[3] == "PARKERTEX" or row[3] == "SEACLOTH" or row[3] == "WARNER LONDON":
                brand = "Lee Jofa"
                sku = "LJ " + temp[0] + "-" + temp[1]
            elif row[3] == "KRAVET SMART" or row[3] == "KRAVET DESIGN" or row[3] == "KRAVET BASICS" or row[3] == "KRAVET COUTURE" or row[3] == "KRAVET CONTRACT":
                if "ANDREW MARTIN" in row[16]:
                    brand = "Andrew Martin"
                    sku = "AM " + temp[0] + "-" + temp[1]
                elif "LIZZO" in row[16]:
                    brand = "Lizzo"
                    sku = "LI " + temp[0] + "-" + temp[1]
                else:
                    brand = "Kravet"
                    sku = "K " + temp[0] + "-" + temp[1]
            elif row[3] == "BAKER LIFESTYLE":
                brand = "Baker Lifestyle"
                sku = temp[0] + "-" + temp[1]
            elif row[3] == "MULBERRY":
                brand = "Mulberry"
                sku = temp[0] + "-" + temp[1]
            elif row[3] == "G P & J BAKER":
                brand = "G P & J Baker"
                sku = "GPJ " + temp[0] + "-" + temp[1]
            elif row[3] == "COLE & SON":
                brand = "Cole & Son"
                sku = "CS " + temp[0]
            elif row[3] == "GROUNDWORKS":
                brand = "Groundworks"
                sku = "GW " + temp[0] + "-" + temp[1]
            elif row[3] == "THREADS":
                brand = "Threads"
                sku = temp[0] + "-" + temp[1]
            elif row[3] == "AVONDALE":
                brand = "Avondale"
                sku = "AV " + temp[0] + "-" + temp[1]
            elif row[3] == "LAURA ASHLEY":
                brand = "Laura Ashley"
                sku = "LA " + temp[0] + "-" + temp[1]
            elif row[3] == "BRUNSCHWIG & FILS":
                brand = "Brunschwig & Fils"
                sku = "BF " + temp[0] + "-" + temp[1]
            elif row[3] == "GASTON Y DANIELA":
                brand = "Gaston Y Daniela"
                sku = "GD " + temp[0] + "-" + temp[1]
            elif row[3] == "WINFIELD THYBONY":
                brand = "Winfield Thybony"
                sku = "WF " + temp[0]
                r = requests.get(
                    "http://www.winfieldthybony.com/home/products/details?sku=" + sku.replace("WF ", ""))
                soup = BeautifulSoup(r.content, "lxml")
                collection = ""
                try:
                    collection = soup.find(
                        "span", id="ctl00_mainContent_C001_collectionName").string
                except:
                    pass
                try:
                    picLoc = soup.find(
                        "a", id="ctl00_mainContent_C001_downloadRoomShotImageUrl2")["href"]
                except:
                    pass
            elif row[3] == "CLARKE AND CLARKE":
                brand = "Clarke & Clarke"
                sku = "CC " + temp[0]
            else:
                if row[3] not in unknownBrands:
                    unknownBrands.append(row[3])
                debug("Kravet", 1, "Brand Error for MPN: {}".format(mpn))
                continue

            sku = sku.replace("'", "")

            try:
                Kravet.objects.get(mpn=mpn)
                continue
            except Kravet.DoesNotExist:
                pass

            if row[1] == "." or row[1] == ".." or row[1] == "..." or row[1] == "" or row[1].find("KF ") >= 0 or "KRAVET " in row[1]:
                pattern = temp[0]
            else:
                pattern = row[1]

            try:
                if row[2] == "." or row[2] == "" or row[2] == "NONE" or "KRAVET " in row[1]:
                    color = temp[1]
                else:
                    color = row[2]
            except:
                pass

            if row[17] == "WALLCOVERING":
                ptype = "Wallpaper"
            elif row[17] == "TRIM":
                ptype = "Trim"
            else:
                ptype = "Fabric"

            usage = row[17]

            try:
                vr = float(row[4])
            except:
                vr = 0

            try:
                hr = float(row[5])
            except:
                hr = 0

            try:
                width = float(row[7])
            except:
                width = 0

            try:
                cost = float(str(row[10]).strip())
                if row[32] != "":
                    cost = float(str(row[32]).strip())
            except Exception as e:
                print(e)
                debug("Kravet", 1, "Price Error for MPN: {}".format(mpn))
                continue

            try:
                map = float(str(row[49]).strip())
            except Exception as e:
                print(e)
                debug("Kravet", 1, "Price Error for MPN: {}".format(mpn))
                continue

            content = row[12]
            collection = collection

            uom = "Per " + row[11]
            if row[11] == "ROLL":
                uom = "Per Roll"
            elif row[11] == "YARD":
                uom = "Per Yard"
            elif row[11] == "EACH":
                uom = "Per Item"
            elif "FOOT" in row[11]:
                uom = "Per Square Foot"
            elif row[11] == "PANEL":
                uom = "Per Panel"
            else:
                debug("Kravet", 1, "UOM Error for MPN: {}".format(mpn))
                continue

            category = ",".join((row[20], row[21]))
            style = ",".join((row[20], row[21]))
            colors = ",".join((row[26], row[27], row[28]))
            statusText = row[31]

            # Custom Tagging rules
            # 5/1 from BK. Add CLARKE & CLARKE BOTANICAL WONDERS to Florals page
            if collection and "CLARKE & CLARKE BOTANICAL WONDERS" in collection:
                category = "{},{}".format(category, "Floral")

            try:
                rollLength = float(row[37])
            except:
                rollLength = 0

            try:
                minimum = int(float(row[38]))
            except:
                minimum = 1
                pass

            increment = ""
            try:
                if int(float(row[39])) > 1:
                    increment = ",".join(
                        [str(ii * int(float(row[39]))) for ii in range(1, 21)])
            except:
                pass

            thumbnail = picLoc

            if row[43].strip() != "YES":
                sample = False
            else:
                sample = True

            manufacturer = "{} {}".format(brand, ptype)

            stock = int(float(row[46]))
            sampleStock = int(float(row[50]))
            stockNote = row[47]

            try:
                Kravet.objects.create(
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
                    hr=hr,
                    vr=vr,
                    content=content,
                    cost=cost,
                    map=map,
                    thumbnail=thumbnail,
                    status=status,
                    statusText=statusText,
                    sample=sample,
                    stock=stock,
                    stockNote=stockNote,
                    sampleStock=sampleStock,
                )
            except Exception as e:
                print(e)
                continue

            debug("Kravet", 0,
                  "Success to get product details for MPN: {}".format(mpn))

        print(unknownBrands)

    def getPillowProducts(self):
        wb = xlrd.open_workbook(FILEDIR + "/files/kravet-pillow.xlsx")
        sh = wb.sheet_by_index(1)

        for i in range(2, sh.nrows):
            try:
                mpn = str(sh.cell_value(i, 0)).strip()

                mpnCheck = mpn.split(".")
                if len(mpnCheck) != 3 or mpnCheck[2] != "0":
                    debug("Kravet", 1, "Produt MPN error {}".format(mpn))
                    continue

                pattern = str(sh.cell_value(i, 1)).replace(
                    "Pillow", "").strip()
                color = str(sh.cell_value(i, 7)).replace(";", "/")

                brand = "Kravet"

                sku = "K {}".format(mpn)

                try:
                    Kravet.objects.get(mpn=mpn)
                    continue
                except Kravet.DoesNotExist:
                    pass

                status = str(sh.cell_value(i, 4))
                if status != "Active":
                    debug("Kravet", 1, "Produt discontinued {}".format(mpn))
                    continue

                collection = "Decorative Pillows"

                ptype = "Pillow"

                try:
                    price = float(sh.cell_value(i, 14))
                except:
                    debug("Kravet", 1, "Produt price error {}".format(mpn))
                    continue

                uom = "Per Item"

                minimum = 1
                increment = ""

                usage = "Accessory"
                categoryList = str(sh.cell_value(i, 5))

                try:
                    width = round(float(sh.cell_value(i, 9)), 2)
                except:
                    width = 0
                try:
                    height = round(float(sh.cell_value(i, 11)), 2)
                except:
                    height = 0

                if ptype == "Pillow" and width != 0 and height != 0:
                    size = '{}" x {}"'.format(int(width), int(height))
                else:
                    size = ""

                content = str(sh.cell_value(i, 19))

                country = str(sh.cell_value(i, 20))
                lead = str(sh.cell_value(i, 17))
                care = str(sh.cell_value(i, 23))
                if lead != "":
                    feature = "Lead Time: {}<br>Care Instructions: {}<br>Country: {}".format(
                        lead, care, country)

                description = str(sh.cell_value(i, 2))

                picLink = str(sh.cell_value(i, 34))
                roomLink = str(sh.cell_value(i, 35))

                manufacturer = "{} {}".format(brand, ptype)

                Kravet.objects.create(
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
                    category=categoryList,
                    style=categoryList,
                    colors=color,
                    width=width,
                    height=height,
                    size=size,
                    content=content,
                    feature=feature,
                    description=description,
                    thumbnail=picLink,
                    roomset=roomLink,
                    cost=price,
                )

                debug("Kravet", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("Kravet", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Kravet');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Kravet.objects.get(sku=sku)
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
                        "Kravet", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Kravet", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Kravet.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Kravet", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Kravet", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Kravet.objects.all()

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
                weight = 1

                desc = ""
                if product.description != None and product.description != "":
                    desc += "{}<br/><br/>".format(
                        product.description)
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.ptype == "Pillow" and product.size != "":
                    desc += "Size: {}<br/>".format(product.size)
                else:
                    if product.width != None and product.width != "" and float(product.width) != 0:
                        desc += "Width: {} in<br/>".format(product.width)
                    if product.height != None and product.height != "" and float(product.height) != 0:
                        desc += "Height: {} in<br/>".format(product.height)
                if product.hr != None and product.hr != "" and float(product.hr) != 0:
                    desc += "Horizontal Repeat: {} in<br/>".format(
                        product.hr)
                if product.vr != None and product.vr != "" and float(product.vr) != 0:
                    desc += "Vertical Repeat: {} in<br/>".format(
                        product.vr)
                if product.rollLength != None and product.rollLength != "" and float(product.rollLength) != 0:
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} yds<br/>".format(
                            product.rollLength)
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
                    if product.ptype == "Pillow":
                        price = common.formatprice(cost, markup_price_pillow)
                        priceTrade = common.formatprice(
                            cost, markup_trade_pillow)
                    else:
                        price = common.formatprice(cost, markup_price)
                        priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Kravet", 2,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                increment = ""
                if product.increment != None:
                    increment = product.increment

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
                    sq(increment),
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

                if product.ptype == "Pillow":
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
                else:
                    if product.thumbnail and product.thumbnail.strip() != "":
                        try:
                            urllib.request.urlretrieve("ftp://decbest:mArker999@file.kravet.com{}".format(
                                product.thumbnail), FILEDIR + "/../../images/product/{}.jpg".format(product.productId))
                            debug("Kravet", 0, "Successfully downloaded {}.".format(
                                product.thumbnail))
                        except Exception as e:
                            print(e)
                            debug("Kravet", 1, "Downloaded failed {}.".format(
                                product.thumbnail))
                            pass

                debug("Kravet", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # Update All Products
        products = Kravet.objects.all()

        # Update Specific products
        # products = Kravet.objects.filter(collection="COLE & SON NEW CONTEMPORARY II")

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
                weight = 1

                desc = ""
                if product.description != None and product.description != "":
                    desc += "{}<br/><br/>".format(
                        product.description)
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.ptype == "Pillow" and product.size != "":
                    desc += "Size: {}<br/>".format(product.size)
                else:
                    if product.width != None and product.width != "" and float(product.width) != 0:
                        desc += "Width: {} in<br/>".format(product.width)
                    if product.height != None and product.height != "" and float(product.height) != 0:
                        desc += "Height: {} in<br/>".format(product.height)
                if product.hr != None and product.hr != "" and float(product.hr) != 0:
                    desc += "Horizontal Repeat: {} in<br/>".format(
                        product.hr)
                if product.vr != None and product.vr != "" and float(product.vr) != 0:
                    desc += "Vertical Repeat: {} in<br/>".format(
                        product.vr)
                if product.rollLength != None and product.rollLength != "" and float(product.rollLength) != 0:
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} yds<br/>".format(
                            product.rollLength)
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
                    if product.ptype == "Pillow":
                        price = common.formatprice(cost, markup_price_pillow)
                        priceTrade = common.formatprice(
                            cost, markup_trade_pillow)
                    else:
                        price = common.formatprice(cost, markup_price)
                        priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Kravet", 2,
                          "Price Error: SKU: {}".format(product.sku))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99
                priceSample = 5

                increment = ""
                if product.increment != None:
                    increment = product.increment

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
                    sq(increment),
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

                if product.ptype == "Pillow":
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
                else:
                    if product.thumbnail and product.thumbnail.strip() != "":
                        try:
                            urllib.request.urlretrieve("ftp://decbest:mArker999@file.kravet.com{}".format(
                                product.thumbnail), FILEDIR + "/../../images/product/{}.jpg".format(product.productId))
                            debug("Kravet", 0, "Successfully downloaded {}.".format(
                                product.thumbnail))
                        except Exception as e:
                            print(e)
                            debug("Kravet", 1, "Downloaded failed {}.".format(
                                product.thumbnail))
                            pass

                debug("Kravet", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Kravet');""")

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
                product = Kravet.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Kravet", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                if product.ptype == "Pillow":
                    newPrice = common.formatprice(newCost, markup_price_pillow)
                    newPriceTrade = common.formatprice(
                        newCost, markup_trade_pillow)
                else:
                    newPrice = common.formatprice(newCost, markup_price)
                    newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("Kravet", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("Kravet", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Kravet", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Kravet.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors
            ptype = product.ptype
            size = product.size

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(category)))
                con.commit()

                debug("Kravet", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("Kravet", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("Kravet", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

        csr.close()
        con.close()

    def updateSizeTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Kravet.objects.all()
        for product in products:
            sku = product.sku
            ptype = product.ptype
            size = product.size
            width = product.width

            if size != None and size != "" and ptype == "Pillow":
                csr.execute("CALL AddToEditSize ({}, {})".format(
                    sq(sku), sq(size)))
                con.commit()

                debug("Kravet", 0,
                      "Added Size. SKU: {}, Size: {}".format(sku, sq(size)))

            if width != None and width != "" and ptype == "Trim":
                try:
                    width = float(str(width).replace('"', ''))
                except:
                    continue

                widthTag = '5" & Up'
                if width < 1:
                    widthTag = 'Less than 1"'
                if width >= 1 and width < 2:
                    widthTag = '1" to 2"'
                if width >= 2 and width < 3:
                    widthTag = '2" to 3"'
                if width >= 3 and width < 4:
                    widthTag = '3" to 4"'
                if width >= 4 and width < 5:
                    widthTag = '4" to 5"'

                csr.execute("CALL AddToEditSize ({}, {})".format(
                    sq(sku), sq(widthTag)))
                con.commit()

                debug("Kravet", 0,
                      "Added Width. SKU: {}, Width: {}, Width Tag: {}".format(sku, width, widthTag))

        csr.close()
        con.close()

    def outlet(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Kravet.objects.all()
        for product in products:
            if product.productId == None or product.productId == "":
                continue

            csr.execute(
                "SELECT IsOutlet From Product WHERE ProductID = {}".format(product.productId))
            oOutlet = (csr.fetchone())[0]

            if oOutlet == 0 and product.statusText == "Outlet":
                try:
                    csr.execute(
                        "UPDATE Product SET IsOutlet = 1 WHERE ProductID = {}".format(product.productId))
                    con.commit()

                    csr.execute(
                        "CALL AddToPendingUpdateProduct ({})".format(product.productId))
                    con.commit()

                    debug("Kravet", 0, "Outlet Status enabled for product: {}".format(
                        product.productId))
                except Exception as e:
                    print(e)

            if oOutlet == 1 and product.statusText != "Outlet":
                try:
                    csr.execute(
                        "UPDATE Product SET IsOutlet = 0 WHERE ProductID = {}".format(product.productId))
                    con.commit()

                    csr.execute(
                        "CALL AddToPendingUpdateProduct ({})".format(product.productId))
                    con.commit()

                    debug("Kravet", 0, "Outlet Status disabled for product: {}".format(
                        product.productId))
                except Exception as e:
                    print(e)

        csr.close()
        con.close()

    def fixMissingImages(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()
        hasImage = []
        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = 'Kravet'")
        for row in csr.fetchall():
            hasImage.append(row[0])

        products = Kravet.objects.all()
        for product in products:
            if product.productId == None:
                continue

            if int(product.productId) in hasImage:
                continue

            if product.thumbnail == "":
                continue

            if product.brand == "Winfield Thybony":
                common.picdownload2(product.thumbnail, str(
                    product.productId) + ".jpg")
            else:
                try:
                    debug("Kravet", 0, "Downloading {}.".format(product.thumbnail))
                    urllib.request.urlretrieve("ftp://decbest:mArker999@file.kravet.com{}".format(
                        product.thumbnail), FILEDIR + "/../../images/product/{}.jpg".format(product.productId))
                except Exception as e:
                    print(e)
                    continue
        csr.close()
        con.close()

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Kravet'")
        con.commit()

        products = Kravet.objects.all()

        for product in products:
            sku = product.sku
            stock = product.stock
            if stock < 3:
                stock = 0

            leadtime = "{} days".format(product.stockNote)

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Kravet')".format(
                    sku, stock, leadtime))
                con.commit()
                debug("Kravet", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug(
                    "Kravet", 2, "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def bestSeller(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        s = requests.Session()

        hrefs = []

        for href in hrefs:
            soup = BeautifulSoup(
                s.get("https://www.decoratorsbest.com{}".format(href)).text, "html.parser")
            sku = soup.find("span", {"class": "variant-sku"}).encode_contents()

            try:
                product = Kravet.objects.get(sku=sku)
            except Kravet.DoesNotExist:
                continue

            csr.execute("CALL AddToProductTag ({}, {})".format(
                sq(sku), sq("Best Selling")))
            con.commit()

            csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                product.productId))
            con.commit()

            debug(0, "Added to Best selling. SKU: {}".format(sku))

        csr.close()
        con.close()
