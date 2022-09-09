from django.core.management.base import BaseCommand
from brands.models import Brewster
from shopify.models import Product as ShopifyProduct

import sys
import os
import pymysql
import xlrd
import paramiko
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

markup_price2 = markup.brewster2
markup_trade1 = markup.brewster_trade1
markup_trade2 = markup.brewster_trade2

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Brewster Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()

        if "getProductIds" in options['functions']:
            self.getProductIds()

        if "addNew" in options['functions']:
            self.addNew()
            self.updateTags()

        if "updateExisting" in options['functions']:
            self.updateExisting()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "updateStock" in options['functions']:
            while True:
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

        if "fixImages" in options['functions']:
            self.fixImages()

        if "main" in options['functions']:
            while True:
                self.getProducts()
                self.getProductIds()
                self.updatePrice()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def downloadDatasheet(self):
        debug("Brewster", 0, "Download New CSV from Brewster FTP")

        host = "ftpimages.brewsterhomefashions.com"
        port = 22
        username = "dealers"
        password = "Brewster#1"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Brewster", 2, "Connection to Brewster FTP Server Failed")
            return False

        sftp.chdir(path='/WallpaperBooks')

        try:
            collections = sftp.listdir()
        except:
            debug("Brewster", 1, "No New Inventory File")
            return False

        for collection in collections:
            if "All Wallpaper Images" in collection:
                continue

            filename = ''
            collectionDir = sftp.listdir(collection)
            for file in collectionDir:
                if "xlsx" in file:
                    filename = file

            # Exception TheCottageData.xlsx download takes long
            if filename == 'TheCottageData.xlsx':
                continue

            if filename != '':
                try:
                    sftp.get(collection + "/" + filename, FILEDIR +
                             '/files/brewster/{}.xlsx'.format(collection))
                    print("Successfully downloaded {}.xlsx".format(collection))
                except Exception as e:
                    print(e)
                    print("Can't download {}".format(filename))
                    continue
            else:
                print("No datasheet in {}".format(collection))

        sftp.close()

        debug("Brewster", 0, "Brewster FTP Inventory Download Completed")
        return True

    def downloadImage(self, sftp, collection, mpn, productId):
        sftp.chdir(path='/WallpaperBooks/{}/Images/300dpi'.format(collection))
        files = sftp.listdir()

        if "{}.jpg".format(mpn) in files:
            sftp.get("{}.jpg".format(mpn), FILEDIR +
                     '/../../images/product/{}.jpg'.format(productId))

            print("downloaded product image {}.jpg".format(productId))

            # Only if thumbnail exists
            if "{}_Room.jpg".format(mpn) in files:
                sftp.get("{}_Room.jpg".format(mpn), FILEDIR +
                         '/../../images/roomset/{}_2.jpg'.format(productId))

                print("downloaded roomset image {}_2.jpg".format(productId))

            if "{}_Room_2.jpg".format(mpn) in files:
                sftp.get("{}_Room.jpg".format(mpn), FILEDIR +
                         '/../../images/roomset/{}_3.jpg'.format(productId))

                print("downloaded roomset image {}_3.jpg".format(productId))

            if "{}_Room_3.jpg".format(mpn) in files:
                sftp.get("{}_Room.jpg".format(mpn), FILEDIR +
                         '/../../images/roomset/{}_4.jpg'.format(productId))

                print("downloaded roomset image {}_4.jpg".format(productId))

            if "{}_Room_4.jpg".format(mpn) in files:
                sftp.get("{}_Room.jpg".format(mpn), FILEDIR +
                         '/../../images/roomset/{}_5.jpg'.format(productId))

                print("downloaded roomset image {}_5.jpg".format(productId))

    def getProducts(self):
        # Discontinued and Discount Table
        discontinued = []
        only50discount = []

        wb = xlrd.open_workbook(FILEDIR + "/files/brewster-discontinued.xlsx")
        discontinuedSheet = wb.sheet_by_index(0)

        for i in range(1, discontinuedSheet.nrows):
            mpn = discontinuedSheet.cell_value(i, 0)
            brand = discontinuedSheet.cell_value(i, 4)
            if brand == "A-Street Prints":
                sku = "Street {}".format(mpn)
            else:
                sku = "Brewster {}".format(mpn)

            if discontinuedSheet.cell_value(i, 14) == "Y":
                discontinued.append(sku)

        wb = xlrd.open_workbook(FILEDIR + "/files/brewster-discount.xlsx")
        discountSheet = wb.sheet_by_index(0)

        for i in range(1, discountSheet.nrows):
            collection = discountSheet.cell_value(i, 0)

            try:
                if int(discountSheet.cell_value(i, 3)) == 50:
                    only50discount.append(collection)
            except:
                continue

        # Download Datasheets
        if not self.downloadDatasheet():
            sys.exit(1)

        Brewster.objects.all().delete()

        files = os.listdir(FILEDIR + "/files/brewster")

        for file in files:
            print(file)
            if "$" in file or "~" in file:
                continue

            wb = xlrd.open_workbook(FILEDIR + "/files/brewster/" + file)
            sh = wb.sheet_by_index(0)

            # Get Ids
            collectionId = -1
            brandId = -1
            mpnId = -1
            nameId = -1
            typeId = -1
            descriptionId = -1
            msrpId = -1
            mapId = -1
            widthId = -1
            lengthId = -1
            coverageId = -1
            repeatId = -1
            matchId = -1
            pasteId = -1
            materialId = -1
            washId = -1
            removeId = -1
            colorId = -1
            colorFamilyId = -1
            styleId = -1
            patternId = -1
            themeId = -1
            bullet1Id = -1
            bullet2Id = -1
            bullet3Id = -1
            bullet4Id = -1
            bullet5Id = -1

            for i in range(0, sh.ncols):
                colName = sh.cell_value(0, i).strip()

                if colName == "Book Name":
                    collectionId = i
                elif colName == "Brand":
                    brandId = i
                elif colName == "Pattern" and i < 10:
                    mpnId = i
                elif colName == "Name":
                    nameId = i
                elif colName == "Product Type":
                    typeId = i
                elif colName == "Description":
                    descriptionId = i
                elif colName == "MSRP" or "Original Unit Retail" in colName:
                    msrpId = i
                elif colName == "MAP":
                    mapId = i
                elif "Width" in colName:
                    widthId = i
                elif "Length" in colName:
                    lengthId = i
                elif colName == "Coverage":
                    coverageId = i
                elif "Repeat" in colName:
                    repeatId = i
                elif colName == "Match":
                    matchId = i
                elif colName == "Paste":
                    pasteId = i
                elif colName == "Material":
                    materialId = i
                elif colName == "Washability":
                    washId = i
                elif colName == "Removability":
                    removeId = i
                elif colName == "Colorway":
                    colorId = i
                elif colName == "Color Family":
                    colorFamilyId = i
                elif colName == "Style":
                    styleId = i
                elif colName == "Pattern" and i > 10:
                    patternId = i
                elif colName == "Theme":
                    themeId = i
                elif colName == "Bullet Point 1":
                    bullet1Id = i
                elif colName == "Bullet Point 2":
                    bullet2Id = i
                elif colName == "Bullet Point 3":
                    bullet3Id = i
                elif colName == "Bullet Point 4":
                    bullet4Id = i
                elif colName == "Bullet Point 5":
                    bullet5Id = i

            for i in range(1, sh.nrows):
                try:
                    mpn = sh.cell_value(i, mpnId).strip()
                except:
                    mpn = int(sh.cell_value(i, mpnId))

                if mpn == "":
                    continue

                brand = sh.cell_value(i, brandId).strip()
                originalBrand = brand

                status = True

                # 3/7/22 From Ashley. Disable Eijffinger Brand and products
                if brand == "Eijffinger" or brand == "Eiffinger":
                    status = False

                if brand == "A-Street Prints":
                    brand = "A-Street Prints"
                    sku = "Street {}".format(mpn)
                else:
                    brand = "Brewster Home Fashions"
                    sku = "Brewster {}".format(mpn)

                if sku in discontinued:
                    status = False

                try:
                    Brewster.objects.get(sku=sku)
                    continue
                except Brewster.DoesNotExist:
                    pass

                isonly50discount = False
                for only50 in only50discount:
                    if collection in only50:
                        isonly50discount = True

                # collection = sh.cell_value(i, collectionId)
                # Fix collection name 5/24
                collection = file.replace('.xlsx', '')

                # 6/7 Bk - remove Brewster Scalamandre collection
                if collection == 'Scalamandre':
                    status = False

                ptype = "Wallpaper"
                usage = sh.cell_value(i, typeId)
                name = sh.cell_value(i, nameId)
                description = sh.cell_value(i, descriptionId)
                uom = "Per Roll"

                try:
                    msrp = common.formatprice(
                        float(str(sh.cell_value(i, msrpId)).replace("$", "")), 1)
                except:
                    debug("Brewster", 1, "MSRP Error SKU: {}".format(sku))
                    continue

                map = 0
                try:
                    if mapId > -1 and sh.cell_value(i, mapId) != '':
                        map = common.formatprice(
                            float(str(sh.cell_value(i, mapId)).replace("$", "")), 1)
                except:
                    debug("Brewster", 1, "MAP Error SKU: {}".format(sku))

                if isonly50discount:
                    cost = round(msrp * 0.5, 2)
                else:
                    cost = round(msrp * 0.4, 2)

                try:
                    width = sh.cell_value(i, widthId)
                except:
                    width = 0
                try:
                    height = float(sh.cell_value(i, lengthId))
                except:
                    height = 0
                try:
                    repeat = float(sh.cell_value(i, repeatId))
                except:
                    repeat = 0

                rollLength = round(height / 3, 2)

                if colorId != -1:
                    color = sh.cell_value(i, colorId)
                elif colorFamilyId != -1:
                    color = sh.cell_value(i, colorFamilyId)
                else:
                    debug("Brewster", 1, "Color Error: MPN: {}".format(mpn))
                    continue

                if color == "":
                    color = "Multicolor"

                style = sh.cell_value(i, styleId)
                try:
                    pattern = sh.cell_value(i, patternId)
                    if pattern == "":
                        pattern = mpn
                except:
                    pattern = mpn

                category = sh.cell_value(i, themeId)

                if bullet1Id != -1:
                    bullet1 = sh.cell_value(i, bullet1Id)
                    bullet2 = sh.cell_value(i, bullet2Id)
                    bullet3 = sh.cell_value(i, bullet3Id)
                    bullet4 = sh.cell_value(i, bullet4Id)
                    bullet5 = sh.cell_value(i, bullet5Id)
                else:
                    bullet1 = "Coverage: " + sh.cell_value(i, coverageId)
                    try:
                        bullet2 = "Match: " + sh.cell_value(i, matchId)
                    except:
                        bullet2 = ""
                    bullet3 = "Paste: " + \
                        sh.cell_value(i, pasteId) + "<br />Material: " + \
                        sh.cell_value(i, materialId)
                    bullet4 = "Washability: " + sh.cell_value(i, washId)
                    bullet5 = "Removability: " + sh.cell_value(i, removeId)

                # Fix Pattern Name issue
                temp = name.split(color)

                if len(temp) == 2:
                    spPattern = temp[0] + temp[1].split("Wallpaper")[0]
                else:
                    spPattern = temp[0].split("Wallpaper")[0]

                spPattern = spPattern.replace("  ", " ").strip()

                if spPattern == "":
                    spPattern = pattern
                ########################

                manufacturer = "{} {}".format(brand, ptype)

                # Tagging
                keywords = "{}, {}, {}, {}".format(
                    category, style, spPattern, collection)

                Brewster.objects.create(
                    mpn=mpn,
                    sku=sku,
                    collection=collection,
                    pattern=spPattern,
                    color=color,
                    manufacturer=manufacturer,
                    colors=color,
                    ptype=ptype,
                    originalBrand=originalBrand,
                    brand=brand,
                    uom=uom,
                    usage=usage,
                    category=keywords,
                    style=keywords,
                    width=width,
                    height=height,
                    repeat=repeat,
                    rollLength=rollLength,
                    description=description,
                    minimum=1,
                    increment="",
                    cost=cost,
                    map=map,
                    msrp=msrp,
                    bullet1=bullet1,
                    bullet2=bullet2,
                    bullet3=bullet3,
                    bullet4=bullet4,
                    bullet5=bullet5,
                    status=status,
                    only50Discount=isonly50discount
                )

                debug(
                    "Brewster", 0, "Success to get product details for MPN: {}".format(mpn))

        # Updated Prices
        for i in range(1, discontinuedSheet.nrows):
            mpn = discontinuedSheet.cell_value(i, 0)
            brand = discontinuedSheet.cell_value(i, 4)
            if brand == "A-Street Prints":
                sku = "Street {}".format(mpn)
            else:
                sku = "Brewster {}".format(mpn)

            try:
                product = Brewster.objects.get(sku=sku)
            except:
                continue

            try:
                msrp = float(
                    str(discontinuedSheet.cell_value(i, 11)).replace("$", ""))  # From Scott - FTP Datasheet price is double roll
            except:
                debug("Brewster", 1, "Updating Price Error SKU: {}".format(sku))
                continue

            try:
                map = float(
                    str(discontinuedSheet.cell_value(i, 12)).replace("$", ""))
            except:
                map = 0

            if product.only50Discount:
                cost = round(msrp * 0.5, 2)
            else:
                cost = round(msrp * 0.4, 2)

            product.cost = cost
            if map != 0:
                product.map = map
            product.msrp = msrp

            product.save()

            debug("Brewster", 0, "Price For SKU: {} has been updated".format(sku))

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Brewster');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Brewster.objects.get(sku=sku)
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
                        "Brewster", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Brewster", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Brewster.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Brewster", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Brewster", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        # For Image download
        host = "ftpimages.brewsterhomefashions.com"
        port = 22
        username = "dealers"
        password = "Brewster#1"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Brewster", 2, "Connection to Brewster FTP Server Failed")
            return False
        ###################################

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Brewster.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                collection = product.collection
                if product.originalBrand != "Brewster" and product.originalBrand != "A-Street Prints" and product.originalBrand not in collection:
                    collection = product.originalBrand + " " + collection

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
                if collection != None and collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        collection)
                if product.width != None and product.width != "" and float(product.width) != 0:
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Length: {} ft<br/>".format(product.height)
                if product.repeat != None and product.repeat != "" and float(product.repeat) != 0:
                    desc += "Repeat: {} in<br/>".format(product.repeat)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.feature != None and product.feature != "":
                    desc += "Feature: {}<br/>".format(product.feature)
                if product.rollLength != None and product.rollLength != "" and float(product.rollLength) != 0 and product.uom == "Per Roll":
                    desc += "<br/>Yard Per Roll: {} yds<br/>".format(
                        product.rollLength)
                desc += "<br/>{}<br/>{}<br/>{}<br/>{}<br/>{}<br/><br/>".format(
                    product.bullet1, product.bullet2, product.bullet3, product.bullet4, product.bullet5)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                map = product.map
                try:
                    if map > 0:
                        price = common.formatprice(map, 1)
                        priceTrade = common.formatprice(cost, markup_trade1)
                    else:
                        price = common.formatprice(cost, markup_price2)
                        priceTrade = common.formatprice(cost, markup_trade2)
                except:
                    debug("Brewster", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("Brewster", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))
            except Exception as e:
                print(e)
                continue

            try:
                self.downloadImage(sftp, product.collection,
                                   product.mpn, productId)
            except Exception as e:
                print(e)
                pass

        csr.close()
        con.close()
        sftp.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Brewster.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                collection = product.collection
                if product.originalBrand != "Brewster" and product.originalBrand != "A-Street Prints" and product.originalBrand not in collection:
                    collection = product.originalBrand + " " + collection

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
                if collection != None and collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        collection)
                if product.width != None and product.width != "" and float(product.width) != 0:
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "" and float(product.height) != 0:
                    desc += "Length: {} ft<br/>".format(product.height)
                if product.repeat != None and product.repeat != "" and float(product.repeat) != 0:
                    desc += "Repeat: {} in<br/>".format(product.repeat)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.feature != None and product.feature != "":
                    desc += "Feature: {}<br/>".format(product.feature)
                if product.rollLength != None and product.rollLength != "" and float(product.rollLength) != 0 and product.uom == "Per Roll":
                    desc += "<br/>Yard Per Roll: {} yds<br/>".format(
                        product.rollLength)
                desc += "<br/>{}<br/>{}<br/>{}<br/>{}<br/>{}<br/><br/>".format(
                    product.bullet1, product.bullet2, product.bullet3, product.bullet4, product.bullet5)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                map = product.map
                try:
                    if map > 0:
                        price = common.formatprice(map, 1)
                        priceTrade = common.formatprice(cost, markup_trade1)
                    else:
                        price = common.formatprice(cost, markup_price2)
                        priceTrade = common.formatprice(cost, markup_trade2)
                except:
                    debug("Brewster", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("Brewster", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))
            except Exception as e:
                print(e)
                continue

        csr.close()
        con.close()

    def downloadInvFile(self):
        debug("Brewster", 0, "Download New CSV from Brewster FTP")

        host = "34.203.121.151"
        port = 22
        username = "brewster"
        password = "Dec123Brewster!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Brewster", 2, "Connection to Brewster FTP Server Failed")
            return False

        try:
            files = sftp.listdir()
        except:
            debug("Brewster", 1, "No New Inventory File")
            return False

        for file in files:
            if "EDI" in file:
                continue
            sftp.get(file, FILEDIR + '/files/brewster-inventory.csv')
            sftp.remove(file)

        sftp.close()

        debug("Brewster", 0, "Brewster FTP Inventory Download Completed")
        return True

    def updateStock(self):
        if not self.downloadInvFile():
            return

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM ProductInventory WHERE Brand = 'Brewster'")
        con.commit()

        f = open(FILEDIR + '/files/brewster-inventory.csv', "rt")
        cr = csv.reader(f)

        index = 0
        for row in cr:
            index += 1
            if index == 1:
                continue

            mpn = row[0]
            brand = row[1]
            sku = "Brewster {}".format(mpn)
            if brand == "A-Street Prints":
                sku = "Street {}".format(mpn)

            stock = int(row[3])

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', 'Brewster')".format(
                    sku, stock, ""))
                con.commit()
                debug("Brewster", 0,
                      "Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                debug(
                    "Brewster", 2, "Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def fixImages(self):
        collections = Brewster.objects.values_list(
            'collection', flat=True).distinct()
        for collection in collections:
            # Socket is closed error. Re initialize the socket per collection
            host = "ftpimages.brewsterhomefashions.com"
            port = 22
            username = "dealers"
            password = "Brewster#1"

            try:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            except:
                debug("Brewster", 2, "Connection to Brewster FTP Server Failed")
                return False
            ###################################

            products = Brewster.objects.filter(collection=collection)

            print("Downloading images for collection: {}".format(collection))
            for product in products:
                productId = product.productId
                collection = product.collection
                mpn = product.mpn
                if productId == None or productId == "":
                    continue

                try:
                    self.downloadImage(sftp, collection, mpn, productId)
                except Exception as e:
                    print(e)
                    continue

            sftp.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Brewster');""")

        rows = csr.fetchall()
        for row in rows:
            productId = row[0]
            shopifyProduct = ShopifyProduct.objects.get(productId=productId)

            pv1 = shopifyProduct.variants.filter(
                isDefault=1).values('cost', 'price')[0]
            pv2 = shopifyProduct.variants.filter(
                name__startswith="Trade - ").values('price')[0]

            oldCost = pv1['cost']
            oldPrice = pv1['price']
            oldTradePrice = pv2['price']

            try:
                product = Brewster.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Brewster", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            map = product.map
            try:
                if map > 0:
                    newPrice = common.formatprice(map, 1)
                    newPriceTrade = common.formatprice(newCost, markup_trade1)
                else:
                    newPrice = common.formatprice(newCost, markup_price2)
                    newPriceTrade = common.formatprice(newCost, markup_trade2)
            except:
                debug("Brewster", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("Brewster", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Brewster", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Brewster.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(category)))
                con.commit()

                debug("Brewster", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("Brewster", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("Brewster", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

        csr.close()
        con.close()
