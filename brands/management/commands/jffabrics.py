from library import debug, common, shopify, markup
from django.core.management.base import BaseCommand
from brands.models import JFFabrics

import os
import paramiko
import pymysql
import time
import xlrd
from shutil import copyfile

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.jffabrics
markup_trade = markup.jffabrics_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build JFFabrics Database'

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

        if "fixMissingImages" in options['functions']:
            self.fixMissingImages()

        if "updateStock" in options['functions']:
            self.updateStock()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "roomset" in options['functions']:
            self.roomset()

        if "main" in options['functions']:
            while True:
                self.updateStock()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def getProducts(self):
        JFFabrics.objects.all().delete()

        # Disco Books
        discoBooks = []
        wb = xlrd.open_workbook(FILEDIR + "/files/jffabrics-disco-books.xls")
        sh = wb.sheet_by_index(0)
        for i in range(3, sh.nrows):
            book = str(sh.cell_value(i, 0))
            discoBooks.append(book)

        # Disco Skus
        discoSkus = []
        wb = xlrd.open_workbook(FILEDIR + "/files/jffabrics-disco-skus.xls")
        sh = wb.sheet_by_index(0)
        for i in range(9, sh.nrows):
            book = str(sh.cell_value(i, 3))
            pattern = str(sh.cell_value(i, 0))
            try:
                pattern = int(float(pattern))
            except:
                pass
            try:
                color = int(sh.cell_value(i, 1))
            except:
                pass
            mpn = "{}_{}{}".format(pattern, color, book)
            mpn = mpn.replace("-", "_")
            sku = "JF {}".format(mpn)
            discoSkus.append(sku)

        wb = xlrd.open_workbook(FILEDIR + "/files/jffabrics-master-new.xls")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                book = str(sh.cell_value(i, 1))
                if book in discoBooks:
                    debug("JF Fabrics", 1,
                          "Book: {} has been discontinued".format(book))
                    continue

                pattern = str(sh.cell_value(i, 2))

                try:
                    pattern = int(float(pattern))
                except:
                    pass

                try:
                    color = int(sh.cell_value(i, 3))
                except:
                    pass

                mpn = "{}_{}{}".format(pattern, color, book)
                mpn = mpn.replace("-", "_")

                sku = "JF {}".format(mpn)
                if sku in discoSkus:
                    debug("JF Fabrics", 1,
                          "SKU: {} has been discontinued".format(sku))
                    continue

                try:
                    JFFabrics.objects.get(mpn=mpn)
                    continue
                except JFFabrics.DoesNotExist:
                    pass

                statusText = str(sh.cell_value(i, 5))
                if statusText != None and "discontinued" in statusText.lower():
                    status = False
                else:
                    status = True

                colorList = str(sh.cell_value(i, 6))
                ptype = str(sh.cell_value(i, 8))
                content = str(sh.cell_value(i, 10))
                brand = "JF Fabrics"

                try:
                    price = float(
                        str(sh.cell_value(i, 76)).replace('$', '').strip())
                    map = float(
                        str(sh.cell_value(i, 74)).replace('$', '').strip())
                except:
                    debug("JF Fabrics", 1, "Failed produt data -- {}: {} {}".format(mpn,
                                                                                    sh.cell_value(i, 75), sh.cell_value(i, 74)))
                    continue

                uom = "Per Yard"
                minimum = 1
                increment = ""

                #  JFF is totally priced as SR or YD. 5/1
                # if sh.cell_value(i, 73) == "DR":
                #     uom = "Per Roll"
                #     minimum = 2
                #     increment = ",".join(
                #         [str(ii * 2) for ii in range(1, 21)])
                #     try:
                #         price = float(
                #             str(sh.cell_value(i, 77)).replace('$', '').strip())
                #         map = float(
                #             str(sh.cell_value(i, 75)).replace('$', '').strip())
                #     except:
                #         debug("JF Fabrics", 1, "Failed produt data -- {}: {} {}".format(mpn,
                #                                                                         sh.cell_value(i, 75), sh.cell_value(i, 74)))
                #         continue

                if sh.cell_value(i, 73) == "DR":
                    uom = "Per Roll"

                usage = str(sh.cell_value(i, 13))
                categoryList = str(sh.cell_value(i, 14))
                styleList = str(sh.cell_value(i, 22))
                country = str(sh.cell_value(i, 23))
                try:
                    width = float(sh.cell_value(i, 24))
                except:
                    width = 0
                try:
                    rollLength = float(sh.cell_value(i, 25))
                except:
                    rollLength = 0
                try:
                    hr = float(sh.cell_value(i, 30))
                except:
                    hr = 0
                try:
                    vr = float(sh.cell_value(i, 31))
                except:
                    vr = 0
                try:
                    weight = float(sh.cell_value(i, 34))
                except:
                    weight = 1
                description = str(sh.cell_value(i, 59))
                picLink = str(sh.cell_value(i, 78))

                if ptype.lower() == 'fabric':
                    ptype = 'Fabric'
                elif ptype.lower() == 'wallcovering':
                    ptype = 'Wallpaper'
                else:
                    debug("JF Fabrics", 1, "ptype error {}".format(mpn))
                    continue

                if ptype == "Wallpaper":
                    usage = "Wallcovering"

                manufacturer = "{} {}".format(brand, ptype)

                # 7/4 from BK. missing performance category
                if "performance" in description:
                    categoryList = "Performance Fabric, " + categoryList

                JFFabrics.objects.create(
                    mpn=mpn,
                    sku=sku,
                    collection=book,
                    pattern=pattern,
                    color=color,
                    status=status,
                    manufacturer=manufacturer,
                    colors=colorList,
                    ptype=ptype,
                    content=content,
                    brand=brand,
                    uom=uom,
                    minimum=minimum,
                    increment=increment,
                    weight=weight,
                    usage=usage,
                    category=categoryList,
                    style=styleList,
                    width=width,
                    rollLength=rollLength,
                    hr=hr,
                    vr=vr,
                    country=country,
                    description=description,
                    thumbnail=picLink,
                    cost=price,
                    map=map
                )

                debug("JF Fabrics", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("JF Fabrics", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'JF Fabrics')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = JFFabrics.objects.get(mpn=mpn)
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
                        "JF Fabrics", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "JF Fabrics", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except JFFabrics.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "JF Fabrics", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            # temp.
            csr.execute(
                "CALL AddToPendingUpdatePublish ({})".format(productID))
            con.commit()

        debug("JF Fabrics", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = JFFabrics.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("JF Fabrics", 1,
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
                if product.width != None and product.width != "":
                    desc += "Width: {}<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {}<br/>".format(product.height)
                if product.rollLength != None and product.rollLength != "":
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Yard per Roll: {}<br/>".format(
                            product.rollLength)
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {}<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {}<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.country != None and product.country != "":
                    desc += "Country of Origin: {}<br/>".format(
                        product.country)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/>".format(product.feature)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)

                    if product.map > 0 and price < product.map:
                        price = common.formatprice(product.map, 1)

                except:
                    debug("JF Fabrics", 2,
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

                debug("JF Fabrics", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = JFFabrics.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId == None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("JF Fabrics", 1,
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
                if product.width != None and product.width != "":
                    desc += "Width: {}<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {}<br/>".format(product.height)
                if product.rollLength != None and product.rollLength != "":
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Yard per Roll: {}<br/>".format(
                            product.rollLength)
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {}<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {}<br/>".format(product.vr)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
                if product.country != None and product.country != "":
                    desc += "Country of Origin: {}<br/>".format(
                        product.country)
                if product.feature != None and product.feature != "":
                    desc += "{}<br/>".format(product.feature)
                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/><br/>".format(product.usage)
                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format(product.brand, product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)

                    if product.map > 0 and price < product.map:
                        price = common.formatprice(product.map, 1)

                except:
                    debug("JF Fabrics", 2,
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

                debug("JF Fabrics", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = JFFabrics.objects.all()

        for product in products:
            mpn = product.mpn
            productId = product.productId
            cost = product.cost

            if productId != "" and productId != None:
                try:
                    price = common.formatprice(cost, markup_price)
                    priceTrade = common.formatprice(cost, markup_trade)

                    if product.map > 0 and price < product.map:
                        price = common.formatprice(product.map, 1)

                except:
                    debug("JF Fabrics", 2,
                          "Price Error: MPN: {}".format(product.mpn))
                    continue

                if price < 19.99:
                    price = 19.99
                    priceTrade = 16.99

                try:
                    csr.execute("SELECT PV1.Cost, PV1.Price, PV2.Price AS TradePrice FROM ProductVariant PV1, ProductVariant PV2 WHERE PV1.ProductID = {} AND PV2.ProductID = {} AND PV1.IsDefault = 1 AND PV2.Name LIKE 'Trade - %' AND PV1.Cost IS NOT NULL AND PV2.Cost IS NOT NULL".format(productId, productId))
                    tmp = csr.fetchone()
                    if tmp == None:
                        debug("JF Fabrics", 2, "Update Price Error: ProductId: {}, MPN: {}".format(
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

                        debug("JF Fabrics", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                            productId, cost, price, priceTrade))
                    else:
                        debug("JF Fabrics", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                            productId, price, priceTrade))
                except:
                    debug("JF Fabrics", 1, "Updating price error for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                        productId, cost, price, priceTrade))
                    continue

        csr.close()
        con.close()

    def fixMissingImages(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        hasImage = []

        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = 'JF Fabrics'")
        for row in csr.fetchall():
            hasImage.append(row[0])

        products = JFFabrics.objects.all()
        for product in products:
            if product.productId == None or product.productId in hasImage:
                continue

            if product.thumbnail and product.thumbnail.strip() != "":
                debug("JF Fabrics", 0, "Product productID: {} is missing pic. downloading from {}".format(
                    product.productId, product.thumbnail))

                try:
                    common.picdownload2(
                        product.thumbnail, "{}.jpg".format(product.productId))
                except Exception as e:
                    print(e)

        csr.close()
        con.close()

    def downloadcsv(self):
        host = "jfprod.sftp.wpengine.com"
        port = 2222
        username = "jfprod-DecoratorsBest"
        password = "DecoratorsBest26!)"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            print(e)
            return False

        try:
            sftp.stat('Decorating Best Inventory.xlsx')
        except Exception as e:
            print(e)
            return False

        sftp.get('Decorating Best Inventory.xlsx',
                 FILEDIR + '/files/jffabrics-inventory.xlsx')
        sftp.remove('Decorating Best Inventory.xlsx')
        sftp.close()

        print("Download completed")
        return True

    def updateStock(self):
        if not self.downloadcsv():
            return

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM ProductInventory WHERE Brand = 'JFF' or Brand = 'JF Fabrics'")
        con.commit()

        wb = xlrd.open_workbook(FILEDIR + '/files/jffabrics-inventory.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(2, sh.nrows):
            _sku = str(sh.cell_value(i, 0))
            if _sku[0] == '0':
                _sku = _sku[1:]

            sku = "JF " + _sku

            stock = str(sh.cell_value(i, 3))

            stockval = 0
            try:
                stockval = int(float(stock))
            except:
                stockval = 0

            try:
                csr.execute("CALL UpdateProductInventory ('{}', {}, 1, '{}', '{}')".format(
                    sku, stockval, "", 'JF Fabrics'))
                con.commit()
                print("Updated inventory for {} to {}.".format(sku, stock))
            except Exception as e:
                print(e)
                print("Error Updating inventory for {} to {}.".format(sku, stock))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = JFFabrics.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.color

            if category != None and category != "":
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(category)))
                con.commit()

                debug("JFFabrics", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(category)))

            if style != None and style != "":
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(style)))
                con.commit()

                debug("JFFabrics", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(style)))

            if colors != None and colors != "":
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(colors)))
                con.commit()

                debug("JFFabrics", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(colors)))

        csr.close()
        con.close()

    def roomset(self):
        fnames = os.listdir(FILEDIR + "/files/images/jf fabrics/")

        for fname in fnames:
            try:
                if "-" in fname:
                    mpn = fname.split("-")[0]
                    roomId = int(fname.split("-")[1].split(".")[0]) + 1

                    product = JFFabrics.objects.get(mpn=mpn)
                    productId = product.productId

                    if productId != None and productId != "":
                        copyfile(FILEDIR + "/files/images/jf fabrics/" + fname, FILEDIR +
                                 "/../../images/roomset/{}_{}.jpg".format(productId, roomId))

                        debug("JF Fabrics", 0, "Roomset Image {}_{}.jpg".format(
                            productId, roomId))

                        os.remove(
                            FILEDIR + "/files/images/jf fabrics/" + fname)
                    else:
                        print("No product found with MPN: {}".format(mpn))
                else:
                    continue

            except Exception as e:
                print(e)
                continue
