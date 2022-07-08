import paramiko
from django.core.management.base import BaseCommand
from brands.models import MadcapCottage
from shopify.models import Product as ShopifyProduct

import os
import pymysql
import xlrd
from shutil import copyfile

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.madcapcottage
markup_trade = markup.madcapcottage_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build MaterialWorks Database'

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

        if "updateStock" in options['functions']:
            self.updateStock()

        if "image" in options['functions']:
            self.image()

        if "roomset" in options['functions']:
            self.roomset()

        if "fixImages" in options['functions']:
            self.fixImages()

    def getProducts(self):
        MadcapCottage.objects.all().delete()

        wb = xlrd.open_workbook(FILEDIR + "/files/madcapcottage-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                ptype = str(sh.cell_value(i, 3)).strip()
                if "Wallpaper" in ptype:
                    ptype = "Wallpaper"
                elif "Fabric" in ptype:
                    ptype = "Fabric"
                elif "Trim" in ptype:
                    ptype = "Trim"
                else:
                    debug("MadcapCottage", 1, "Type Error. {}".format(ptype))
                    continue

                pattern = str(sh.cell_value(i, 4)).strip()
                color = str(sh.cell_value(i, 5)).strip()

                mpn = "{}_{}".format(pattern.lower().replace(
                    " ", "_"), color.lower().replace(" ", "_"))

                ptype = str(sh.cell_value(i, 3)).strip()
                if "Wallpaper" in ptype:
                    ptype = "Wallpaper"
                    mpn = "w_{}".format(mpn)
                elif "Fabric" in ptype:
                    ptype = "Fabric"
                    mpn = "f_{}".format(mpn)
                elif "Trim" in ptype:
                    ptype = "Trim"
                    mpn = "t_{}".format(mpn)
                else:
                    debug("MadcapCottage", 1, "Type Error. {}".format(ptype))
                    continue

                sku = "MDC {}".format(mpn)

                try:
                    MadcapCottage.objects.get(mpn=mpn)
                    debug("MadcapCottage", 1,
                          "MPN Already exists. {}".format(mpn))
                    continue
                except MadcapCottage.DoesNotExist:
                    pass

                brand = "Madcap Cottage"
                collection = str(sh.cell_value(i, 2)).strip()

                ptype = str(sh.cell_value(i, 3)).strip()
                if "Wallpaper" in ptype:
                    ptype = "Wallpaper"
                elif "Fabric" in ptype:
                    ptype = "Fabric"
                elif "Trim" in ptype:
                    ptype = "Trim"
                else:
                    debug("MadcapCottage", 1, "Type Error. {}".format(ptype))
                    continue

                cost = float(str(sh.cell_value(i, 6)).replace("$", ""))
                map = float(str(sh.cell_value(i, 7)).replace("$", ""))
                msrp = float(str(sh.cell_value(i, 8)).replace("$", ""))

                uom = str(sh.cell_value(i, 23)).strip()
                rollLength = 0
                if uom == "Yard":
                    uom = "Per Yard"
                elif uom == "11 yd Roll":
                    uom = "Per Roll"
                    rollLength = 11
                else:
                    debug("MadcapCottage", 1, "UOM error {}".format(mpn))
                    continue

                # minimum = int(str(sh.cell_value(i, 25)).replace(
                #     "roll", "").replace("yd", "").strip())
                minimum = 2  # 7/8 from BK
                increment = ''

                usage = str(sh.cell_value(i, 24)).strip()

                width = str(sh.cell_value(i, 10)).strip()
                if "trims" not in width and width != "":
                    width = "{}\"".format(width)

                height = ""

                vr = str(sh.cell_value(i, 17)).strip()
                hr = str(sh.cell_value(i, 18)).strip()

                description = ""

                content = str(sh.cell_value(i, 12)).strip()
                if str(sh.cell_value(i, 13)).strip() != "" and str(sh.cell_value(i, 14)).strip() != "":
                    content = "{}% {}".format(
                        str(sh.cell_value(i, 13)).strip(), str(sh.cell_value(i, 14)).strip())
                if str(sh.cell_value(i, 15)).strip() != "" and str(sh.cell_value(i, 16)).strip() != "":
                    content = "{}, {}% {}".format(content, str(sh.cell_value(
                        i, 15)).strip(), str(sh.cell_value(i, 16)).strip())

                feature = "{}, {}, {}, {}".format(
                    str(sh.cell_value(i, 19)).strip(), str(sh.cell_value(i, 20)).strip(), str(sh.cell_value(i, 21)).strip(), str(sh.cell_value(i, 22)).strip())

                thumbnail = str(sh.cell_value(i, 30)).strip()
                roomset = str(sh.cell_value(i, 31)).strip()

                style = str(sh.cell_value(i, 27)).strip()
                colors = str(sh.cell_value(i, 28)).strip()
                category = str(sh.cell_value(i, 29)).strip()

                keywords = "{}, {}, {}, {}".format(
                    usage, style, category, str(sh.cell_value(i, 9)).strip())

                manufacturer = "{} {}".format(brand, ptype)

                MadcapCottage.objects.create(
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
                    category=keywords,
                    style=keywords,
                    colors=colors,
                    width=width,
                    height=height,
                    hr=hr,
                    vr=vr,
                    rollLength=rollLength,
                    description=description,
                    content=content,
                    feature=feature,
                    cost=cost,
                    map=map,
                    msrp=msrp,
                    thumbnail=thumbnail,
                    roomset=roomset,
                )

                debug("MadcapCottage", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("MadcapCottage", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Madcap Cottage')""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            mpn = row[1]
            published = row[2]

            try:
                product = MadcapCottage.objects.get(mpn=mpn)
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
                        "MadcapCottage", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "MadcapCottage", 0, "Enabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

            except MadcapCottage.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "MadcapCottage", 0, "Disabled product -- ProductID: {}, mpn: {}".format(productID, mpn))

        debug("MadcapCottage", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = MadcapCottage.objects.all()

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
                    desc += "Width: {}<br/>".format(product.width)

                if product.height != None and product.height != "":
                    desc += "Length: {}<br/>".format(product.height)

                if product.rollLength != None and product.rollLength != "":
                    desc += "Roll Length: {} yds<br/>".format(
                        product.rollLength)

                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)

                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)

                if product.content != None and product.content != "":
                    desc += "Content: {}<br/><br/>".format(product.content)

                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)

                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)

                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format("DecoratorsBest", product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("MadcapCottage", 1,
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
                            product.thumbnail, "{}.jpg".format(productId))
                    except:
                        pass

                if product.roomset and product.roomset.strip() != "":
                    try:
                        common.picdownload2(
                            product.roomset, "{}_2.jpg".format(productId))
                    except:
                        pass

                debug("MadcapCottage", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = MadcapCottage.objects.all()

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

                if product.width != None and product.width != "":
                    desc += "Width: {}<br/>".format(product.width)

                if product.height != None and product.height != "":
                    desc += "Length: {}<br/>".format(product.height)

                if product.rollLength != None and product.rollLength != "":
                    desc += "Roll Length: {} yds<br/>".format(
                        product.rollLength)

                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)

                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)

                if product.content != None and product.content != "":
                    desc += "Content: {}<br/><br/>".format(product.content)

                if product.usage != None and product.usage != "":
                    desc += "Usage: {}<br/>".format(product.usage)

                if product.feature != None and product.feature != "":
                    desc += "{}<br/><br/>".format(product.feature)

                if product.ptype != None and product.ptype != "":
                    desc += "{} {}".format("DecoratorsBest", product.ptype)

                cost = product.cost
                try:
                    price = common.formatprice(product.map, 1)
                    priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("MadcapCottage", 1,
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

                debug("MadcapCottage", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'MadcapCottage');""")

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
                product = MadcapCottage.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("MadcapCottage", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            try:
                newPrice = common.formatprice(newCost, markup_price)
                if newPrice < product.map:
                    newPrice = common.formatprice(product.map, 1)

                newPriceTrade = common.formatprice(newCost, markup_trade)
            except:
                debug("MadcapCottage", 1,
                      "Price Error: SKU: {}".format(product.sku))
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

                debug("MadcapCottage", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("MadcapCottage", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def downloadInvFile(self):
        debug("MadcapCottage", 0, "Download New CSV from MadcapCottage FTP")

        host = "18.206.49.64"
        port = 22
        username = "madcapcottage"
        password = "MWDecor1!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("MadcapCottage", 2,
                  "Connection to MadcapCottage FTP Server Failed")
            return False

        sftp.chdir(path='/madcapcottage')

        try:
            files = sftp.listdir()
        except:
            debug("MadcapCottage", 1, "No New Inventory File")
            return False

        for file in files:
            if "EDI" in file:
                continue
            sftp.get(file, FILEDIR + '/files/madcapcottage-inventory.csv')
            sftp.remove(file)

        sftp.close()

        debug("MadcapCottage", 0, "MadcapCottage FTP Inventory Download Completed")
        return True

    def updateStock(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM ProductInventory WHERE Brand = 'Madcap Cottage'")
        con.commit()

        products = MadcapCottage.objects.all()

        for product in products:
            stock = 10

            try:
                csr.execute('CALL UpdateProductInventory ("{}", {}, 3, "{}", "Madcap Cottage")'.format(
                    product.sku, stock, "Ships in 2-3 weeks"))
                con.commit()
                debug("MadcapCottage", 0,
                      "Updated inventory for {} to {}.".format(product.sku, stock))
            except Exception as e:
                print(e)
                debug(
                    "MadcapCottage", 1, "Error Updating inventory for {} to {}.".format(product.sku, stock))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=int(db_port), user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = MadcapCottage.objects.all()
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

                debug("MadcapCottage", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(sty)))

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("MadcapCottage", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if colors != None and colors != "":
                col = str(colors).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("MadcapCottage", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

        csr.close()
        con.close()

    def image(self):
        fnames = os.listdir(FILEDIR + "/files/images/madcapcottage/")
        print(fnames)
        for fname in fnames:
            try:
                mpn = fname.split(".")[0]

                product = MadcapCottage.objects.get(mpn=mpn)
                productId = product.productId

                if productId != None and productId != "":
                    copyfile(FILEDIR + "/files/images/madcapcottage/" + fname, FILEDIR +
                             "/../../images/product/{}.jpg".format(productId))

                os.remove(FILEDIR + "/files/images/madcapcottage/" + fname)
            except:
                continue

    def roomset(self):
        products = MadcapCottage.objects.all()

        for product in products:
            if product.roomset != None and product.roomset != "":
                try:
                    common.roomdownload(
                        product.roomset, "{}_2.jpg".format(product.productId))
                except Exception as e:
                    print(e)
                    pass
            else:
                continue

    def fixImages(self):
        products = MadcapCottage.objects.all()

        for product in products:
            productId = product.productId

            if product.thumbnail and product.thumbnail.strip() != "":
                if "https" in product.thumbnail:
                    try:
                        common.picdownload2(
                            product.thumbnail, "{}.jpg".format(productId))
                    except:
                        pass
                else:
                    try:
                        copyfile("/var/sftp/madcapcottage/madcapcottage/{}/{}".format(product.pattern,
                                                                                      product.thumbnail), FILEDIR + "/../../images/product/{}.jpg".format(productId))
                        print("downloaded {}.jpg".format(productId))
                    except:
                        try:
                            copyfile("/var/sftp/madcapcottage/madcapcottage/{}/{}".format(product.pattern,
                                                                                          product.thumbnail.replace("-", "- ")), FILEDIR + "/../../images/product/{}.jpg".format(productId))
                            print("downloaded {}.jpg".format(productId))
                        except:
                            print("no such file".format(product.thumbnail))
                            continue

            if product.roomset and product.roomset.strip() != "":
                if "https" in product.roomset:
                    try:
                        common.picdownload2(
                            product.roomset, "{}_2.jpg".format(productId))
                    except:
                        pass
                else:
                    copyfile("/var/sftp/madcapcottage/madcapcottage/{}/{}".format(product.pattern,
                             product.thumbnail), FILEDIR + "/../../images/roomset/{}_2.jpg".format(productId))
