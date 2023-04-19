from django.core.management.base import BaseCommand
from brands.models import Seabrook
from shopify.models import Product as ShopifyProduct

import os
import pymysql
import requests
import xlrd

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.seabrook
markup_trade = markup.seabrook_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Seabrook Database'

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

        if "updatePrice" in options['functions']:
            self.updatePrice()

        if "updateTags" in options['functions']:
            self.updateTags()

        if "image" in options['functions']:
            self.image()

        if "bestSellers" in options['functions']:
            self.bestSellers()

        if "main" in options['functions']:
            self.getProducts()
            self.getProductIds()

    def getProducts(self):
        Seabrook.objects.all().delete()

        wb = xlrd.open_workbook(
            FILEDIR + "/files/seabrook-master-1-27-23.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(2, sh.nrows):
            try:
                brand = "Seabrook"
                mpn = str(sh.cell_value(i, 3))

                try:
                    Seabrook.objects.get(mpn=mpn)
                    debug("Seabrook", 1,
                          " MPN: {} is already exist".format(mpn))
                    continue
                except Seabrook.DoesNotExist:
                    pass

                sku = "SB {}".format(mpn)

                ptype = str(sh.cell_value(i, 18))
                usage = "Fabric"
                if ptype == "Sidewall":
                    ptype = "Wallpaper"
                    usage = "Sidewall"
                elif ptype == "Mural":
                    ptype = "Wallpaper"
                    usage = "Mural"
                elif ptype == "Residential Use":
                    ptype = "Wallpaper"
                    usage = "Residential Use"
                elif ptype == "Fabric":
                    ptype == "Fabric"
                    usage = "Fabric"
                else:
                    debug(
                        "Seabrook", 1, "Invalid product type. mpn: {}, Type: {}".format(mpn, ptype))
                    continue

                try:
                    minimum = int(str(sh.cell_value(i, 42)).split(' ')[0])
                except:
                    minimum = 1

                if 'S/R' in sh.cell_value(i, 42):
                    pricing = "Per Roll"
                elif 'Bolt' in sh.cell_value(i, 42):
                    pricing = "Per Roll"
                    minimum = 2
                elif 'Yd' in sh.cell_value(i, 42):
                    pricing = 'Per Yard'
                elif 'Mural' in sh.cell_value(i, 42):
                    pricing = 'Per Yard'
                else:
                    debug("Seabrook", 1, "Pricing Error for MPN: {}. MOQ: {}".format(
                        mpn, sh.cell_value(i, 42)))
                    continue

                if minimum > 1:
                    increment = ",".join([str(ii * minimum)
                                          for ii in range(1, 21)])
                else:
                    increment = ""

                pattern = str(sh.cell_value(i, 5))
                color = str(sh.cell_value(i, 10))

                collection = str(sh.cell_value(i, 2))

                # Disable Lillian August Grasscloth Binder products. 1/5/23 from Ashely
                # New Hampton and Indigo collections have been discontinued. 2/13/23 from Seabrook
                status = True
                if collection == 'Lillian August Grasscloth Binder' or collection == 'Indigo' or collection == 'New Hampton':
                    status = False

                try:
                    price = str(sh.cell_value(i, 12)).replace(" / yd", "")
                    if price == "N/A":
                        price = 0
                    else:
                        price = round(float(price), 2)
                except:
                    debug("Seabrook", 1, "Price Error for MPN: {}".format(mpn))
                    price = 0

                try:
                    map = str(sh.cell_value(i, 14)).replace(" / yd", "")
                    if map == "N/A":
                        map = 0
                    else:
                        map = round(float(map), 2)
                except:
                    debug("Seabrook", 1, "MAP Error for MPN: {}".format(mpn))
                    map = 0

                #####################################################################
                # 2/15: Seabrook metrics are based on MOQ.
                # Treat "2 S/R" products as single roll and double up the prices.
                #####################################################################
                if minimum == 2:
                    try:
                        price = str(sh.cell_value(i, 13)
                                    ).replace(" / yd", "")
                        if price == "N/A":
                            price = 0
                        else:
                            price = round(float(price), 2)
                    except:
                        debug("Seabrook", 1,
                              "Price Error for MPN: {}".format(mpn))
                        price = 0

                    try:
                        map = str(sh.cell_value(i, 15)
                                  ).replace(" / yd", "")
                        if map == "N/A":
                            map = 0
                        else:
                            map = round(float(map), 2)
                    except:
                        debug("Seabrook", 1,
                              "MAP Error for MPN: {}".format(mpn))
                        map = 0

                minimum = 1
                increment = ""
                #####################################################################

                description = str(sh.cell_value(i, 6))

                weight = str(sh.cell_value(i, 21))
                width = "{} in. / {} cm".format(str(sh.cell_value(i, 28)),
                                                str(sh.cell_value(i, 22)))
                length = "{} ft.".format(str(sh.cell_value(i, 27)))

                if float(sh.cell_value(i, 33)) != 0 and float(sh.cell_value(i, 32)) != 0:
                    repeat = "{} in. / {} cm".format(float(sh.cell_value(i, 33)),
                                                     float(sh.cell_value(i, 32)))
                else:
                    repeat = ""

                if pricing == "Per Roll":
                    rollLength = round(
                        float(str(sh.cell_value(i, 27))) / 3, 2)
                else:
                    rollLength = 0

                area = float(str(sh.cell_value(i, 31)))
                finish = str(sh.cell_value(i, 11))
                material = str(sh.cell_value(i, 39))
                clean = str(sh.cell_value(i, 37))
                remove = str(sh.cell_value(i, 38))
                country = str(sh.cell_value(i, 41))

                feature = "<br/>Area: {} sqft<br />Finish: {}<br />Material: {}<br />Cleaning: {}<br />Removal: {}<br />Country: {}<br />".format(
                    area, finish, material, clean, remove, country)

                category = str(sh.cell_value(i, 7))
                style = str(sh.cell_value(i, 8))
                colors = str(sh.cell_value(i, 9))

                thumbnail = str(sh.cell_value(i, 44))
                roomset = str(sh.cell_value(i, 45))

                usage = "Fabric"
                if ptype == "Wallpaper":
                    usage = "Wallcovering"

                manufacturer = "{} {}".format(brand, ptype)

                Seabrook.objects.create(
                    mpn=mpn,
                    sku=sku,
                    collection=collection,
                    pattern=pattern,
                    color=color,
                    manufacturer=manufacturer,
                    ptype=ptype,
                    brand=brand,
                    uom=pricing,
                    usage=usage,
                    description=description,
                    category=category,
                    style=style,
                    colors=colors,
                    width=width,
                    height=length,
                    rollLength=rollLength,
                    weight=weight,
                    repeat=repeat,
                    thumbnail=thumbnail,
                    roomset=roomset,
                    cost=price,
                    map=map,
                    minimum=minimum,
                    increment=increment,
                    feature=feature,
                    status=status
                )

                debug("Seabrook", 0,
                      "Success to get product details for MPN: {}".format(mpn))

            except Exception as e:
                print(e)
                debug("Seabrook", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Seabrook');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Seabrook.objects.get(sku=sku)
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
                        "Seabrook", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Seabrook", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Seabrook.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Seabrook", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Seabrook", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Seabrook.objects.all()

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
                if product.rollLength != None and product.rollLength != "" and product.rollLength != 0 and product.uom == "Per Roll":
                    desc += "Roll Length: {} yds<br/>".format(
                        product.rollLength)
                if product.repeat != None and product.repeat != "":
                    desc += "Repeat: {}<br/>".format(product.repeat)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
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

                    if product.map > 0:
                        price = common.formatprice(product.map, 1)
                except:
                    debug("Seabrook", 2, "Price Error: SKU: {}".format(product.sku))
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

                if product.thumbnail and product.thumbnail.strip() != "":
                    try:
                        common.picdownload2(
                            product.thumbnail, "{}.jpg".format(productId))
                    except:
                        pass

                if product.roomset and product.roomset.strip() != "":
                    try:
                        common.roomdownload(
                            product.roomset, "{}_2.jpg".format(productId))
                    except:
                        pass

                debug("Seabrook", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Seabrook.objects.all()

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
                if product.rollLength != None and product.rollLength != "" and product.rollLength != 0 and product.uom == "Per Roll":
                    desc += "Roll Length: {} yds<br/>".format(
                        product.rollLength)
                if product.repeat != None and product.repeat != "":
                    desc += "Repeat: {}<br/>".format(product.repeat)
                if product.content != None and product.content != "":
                    desc += "Content: {}<br/>".format(product.content)
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

                    if product.map > 0:
                        price = common.formatprice(product.map, 1)
                except:
                    debug("Seabrook", 2, "Price Error: SKU: {}".format(product.sku))
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

                if product.roomset and product.roomset.strip() != "":
                    try:
                        common.roomdownload(
                            product.roomset, "{}_2.jpg".format(productId))
                    except:
                        pass

                debug("Seabrook", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
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
        WHERE M.Brand = 'Seabrook');""")

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
                product = Seabrook.objects.get(
                    productId=shopifyProduct.productId)
                newCost = product.cost
            except:
                debug("Seabrook", 1, "Discontinued Product: SKU: {}".format(
                    shopifyProduct.sku))
                continue

            map = product.map
            try:
                newPrice = common.formatprice(newCost, markup_price)
                newPriceTrade = common.formatprice(newCost, markup_trade)

                if map > 0:
                    newPrice = common.formatprice(map, 1)
            except:
                debug("Seabrook", 2, "Price Error: SKU: {}".format(product.sku))
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

                debug("Seabrook", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newCost, newPrice, newPriceTrade))
            else:
                debug("Seabrook", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                    shopifyProduct.productId, newPrice, newPriceTrade))

        csr.close()
        con.close()

    def updateTags(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Seabrook.objects.all()
        for product in products:
            sku = product.sku

            category = product.category
            style = product.style
            colors = product.colors
            collection = product.collection

            if category != None and category != "":
                cat = str(category).strip()
                csr.execute("CALL AddToEditCategory ({}, {})".format(
                    sq(sku), sq(cat)))
                con.commit()

                debug("Seabrook", 0, "Added Category. SKU: {}, Category: {}".format(
                    sku, sq(cat)))

            if style != None and style != "":
                sty = str(style).strip()
                csr.execute("CALL AddToEditStyle ({}, {})".format(
                    sq(sku), sq(sty)))
                con.commit()

                debug("Seabrook", 0, "Added Style. SKU: {}, Style: {}".format(
                    sku, sq(sty)))

            if colors != None and colors != "":
                col = str(colors).strip()
                csr.execute("CALL AddToEditColor ({}, {})".format(
                    sq(sku), sq(col)))
                con.commit()

                debug("Seabrook", 0,
                      "Added Color. SKU: {}, Color: {}".format(sku, sq(col)))

            if collection != None and collection != "":
                csr.execute("CALL AddToEditCollection ({}, {})".format(
                    sq(sku), sq(collection)))
                con.commit()

                debug("Seabrook", 0, "Added Collection. SKU: {}, Collection: {}".format(
                    sku, sq(collection)))

        csr.close()
        con.close()

    def image(self):
        products = Seabrook.objects.all()

        for product in products:
            productId = product.productId

            if product.thumbnail and product.thumbnail.strip() != "":
                try:
                    common.picdownload2(
                        product.thumbnail, "{}.jpg".format(productId))
                except:
                    pass

            if product.roomset and product.roomset.strip() != "":
                try:
                    common.roomdownload(
                        product.roomset, "{}_2.jpg".format(productId))
                except:
                    pass

    def bestSellers(self):
        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        mpns = [
            'LN11312',
            'BV35464',
            'LN11827',
            'LN11101',
            'TC75415',
            'LN11310',
            'LN10602',
            'BV30108',
            'LN11846',
            'LN11112',
            'MB31302',
            'TC70107',
            'TC75404',
            'TC70600',
            'BV35308',
            'LN11122',
            'TC70618',
            'RY31000',
            'BV30432',
            'TC75010',
            'LN11865',
            'BV35315',
            'MB30034',
            'BV30110',
        ]

        for mpn in mpns:
            sku = "SB {}".format(mpn)

            try:
                product = Seabrook.objects.get(sku=sku)
            except Seabrook.DoesNotExist:
                continue

            csr.execute("CALL AddToProductTag ({}, {})".format(
                sq(sku), sq("Best Selling")))
            con.commit()

            csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                product.productId))
            con.commit()

            debug('Seabrook', 0, "Added to Best selling. SKU: {}".format(sku))

        csr.close()
        con.close()
