from django.core.management.base import BaseCommand
from brands.models import Fabricut

import os
import pymysql
import requests
import xlrd
import json

from library import config, debug, common, shopify, markup

db_host = config.db_endpoint
db_username = config.db_username
db_password = config.db_password
db_name = config.db_name
db_port = config.db_port

markup_price = markup.fabricut
markup_trade = markup.fabricut_trade

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Discountinued
class Command(BaseCommand):
    help = 'Build Fabricut Database'

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

    def getProducts(self):
        s = requests.Session()

        Fabricut.objects.all().delete()

        wb = xlrd.open_workbook(FILEDIR + "/files/fabricut-master-new.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(0, sh.nrows):
            mpn = int(sh.cell_value(i, 0))

            try:
                Fabricut.objects.get(mpn=mpn)
                continue
            except Fabricut.DoesNotExist:
                pass

            debug("Fabricut", 0, "Got MPN: {}".format(mpn))

            Fabricut.objects.create(
                mpn=mpn
            )

        products = Fabricut.objects.all()
        for product in products:
            try:
                r = s.get(
                    "https://api.fabricut.com/v1E/9f4f8cea2ab44c6195440325d1c3e841/product/" + product.mpn)
                if "false" == r.text:
                    product.delete()
                    continue
                j = json.loads(r.text)

                dtype = ""
                if "fabric_data" in j:
                    dtype = "fabric_data"
                    product.width = str(j["fabric_data"]["width"])
                elif "wallcovering_data" in j:
                    dtype = "wallcovering_data"
                    product.width = str(j["wallcovering_data"]["width"])
                elif "trimming_data" in j:
                    dtype = "trimming_data"
                    if "width_total" in j[dtype] and float(j["trimming_data"]["width_total"]) != 0:
                        product.width = str(j["trimming_data"]["width_total"])
                    if "length_total" in j[dtype] and float(j["trimming_data"]["length_total"]) != 0:
                        product.width = str(j["trimming_data"]["length_total"])
                else:
                    debug("Fabricut", 1,
                          "Data type error for MPN: {}".format(product.mpn))

                if "repeat_h" in j[dtype] and float(j[dtype]["repeat_h"]) != 0:
                    product.hr = str(j[dtype]["repeat_h"])
                if "repeat_v" in j[dtype] and float(j[dtype]["repeat_v"]) != 0:
                    product.vr = str(j[dtype]["repeat_v"])

                if "book" in j and j["book"]:
                    product.collection = j["book"]["name"]
                if "collection" in j and j["collection"]:
                    product.category = j["collection"]["name"]

                patternName = j["pattern_name"]
                colorName = j["color_name"]
                brandName = ""

                if "fabricut" == j["brand_name"]:
                    brandName = "Fabricut"
                    sku = "FBC " + product.mpn
                elif "stroheim" == j["brand_name"]:
                    brandName = "Stroheim"
                    sku = "STROHEIM " + product.mpn
                elif "s-harris" == j["brand_name"]:
                    brandName = "S. Harris"
                    sku = "SH " + product.mpn
                elif "vervain" == j["brand_name"]:
                    brandName = "Vervain"
                    sku = "VERVAIN " + product.mpn
                elif "trend" == j["brand_name"]:
                    brandName = "Trend"
                    sku = "TREND " + product.mpn
                elif "clarencehouse" == j["brand_name"]:
                    brandName = "Clarence House"
                    sku = "CL " + product.mpn
                else:
                    continue

                typeName = j["product_type"]
                uom = j["measured_unit"]["long"]["singular"]

                if j["is_discontinued"]:
                    status = False
                else:
                    status = True

                content = " ".join(j["content"])
                usage = " ".join(j[dtype]["uses"])
                baseColor = " ".join(j["base_colors"])
                design = " ".join(j[dtype]["designs"])
                category = " ".join(j[dtype]["categories"])
                try:
                    minimum = int(float(j["order_minimum"]))
                except:
                    minimum = 1
                increment = j["order_increment"]
                picLink = j["images"]["main"]

                if typeName == "fabric":
                    typeName = "Fabric"
                    usage = "Fabric"
                elif typeName == "trimming":
                    typeName = "Trim"
                    usage = "Trimming"
                elif typeName == "wallcovering":
                    typeName = "Wallpaper"
                    usage = "Wallcovering"

                if "Double Roll" in uom:
                    uom = "Per Roll"
                    minimum = 2
                    increment = 2
                elif "3 Panel Set" in uom:
                    uom = "Per Panel"
                    minimum = 3
                    increment = 3
                else:
                    uom = "Per " + uom

                product.sku = sku
                product.pattern = patternName
                product.color = colorName
                product.brand = brandName
                product.ptype = typeName
                product.uom = uom
                product.status = status
                product.content = content
                product.usage = usage
                product.colors = baseColor
                product.design = design
                product.minimum = minimum
                product.category = category
                try:
                    if int(float(increment)) > 1:
                        product.increment = ",".join(
                            [str(ii * int(float(increment))) for ii in range(1, 21)])
                    else:
                        product.increment = ""
                except:
                    product.increment = ""
                    pass
                product.thumbnail = picLink

                rs = s.get(
                    "https://api.fabricut.com/v1E/9f4f8cea2ab44c6195440325d1c3e841/product/" + product.mpn + "/stock+")
                js = json.loads(rs.text)
                # Stock and Price
                stock = js["stock"]["current"]["total"]
                cost = js["pricing"]["per_unit"]

                if status == False and stock > 0:
                    product.statusText = "Limited"
                else:
                    cost *= 1.25

                product.stock = stock
                product.cost = cost

                product.manufacturer = "{} {}".format(brandName, typeName)

                product.save()

                debug("Fabricut", 0, "Success to get product details for MPN: {}".format(
                    product.mpn))

            except Exception as e:
                print(e)
                debug("Fabricut", 1,
                      "Failed to get product details for MPN: {}".format(mpn))
                continue

    def getProductIds(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE M.Brand = 'Fabricut');""")
        rows = csr.fetchall()

        total, pb, upb = len(rows), 0, 0

        for row in rows:
            productID = row[0]
            sku = row[1]
            published = row[2]

            try:
                product = Fabricut.objects.get(sku=sku)
                product.productId = productID
                product.save()

                # 2/2 disable out of stock or backordered items
                if published == 1 and (product.status == False or int(product.stock) < 10):
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Fabricut", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

                if published == 0 and product.status == True and product.cost != None:
                    csr.execute(
                        "UPDATE Product SET Published=1 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    pb = pb + 1
                    debug(
                        "Fabricut", 0, "Enabled product -- ProductID: {}, SKU: {}".format(productID, sku))

            except Fabricut.DoesNotExist:
                if published == 1:
                    csr.execute(
                        "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    upb = upb + 1
                    debug(
                        "Fabricut", 0, "Disabled product -- ProductID: {}, SKU: {}".format(productID, sku))

        debug("Fabricut", 0, "Total {} Products. Published {} Products, Unpublished {} Products.".format(
            total, pb, upb))

        csr.close()
        con.close()

    def addNew(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Fabricut.objects.all()

        for product in products:
            try:
                if product.status == False or product.productId != None:
                    continue

                if product.thumbnail == None or product.thumbnail == "":
                    debug("Fabricut", 1,
                          "No product Image for MPN: {}".format(product.mpn))
                    continue

                # Bug. Collection or Increment None
                if product.collection == None:
                    collection = ""
                else:
                    collection = product.collection

                if product.increment == None:
                    increment = ""
                else:
                    increment = product.increment

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
                if collection != None and collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        collection)
                if product.width != None and product.width != "":
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {} in<br/>".format(product.height)
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)
                if product.rollLength != None and product.rollLength != "":
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} yds<br/>".format(
                            product.rollLength)
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
                        priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Fabricut", 1, "Price Error: SKU: {}".format(product.sku))
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
                    sq(increment),
                    sq(product.uom),
                    sq(product.usage),
                    sq(collection),
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

                debug("Fabricut", 0, "Created New product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))

            except Exception as e:
                print(e)

        csr.close()
        con.close()

    def updateExisting(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Fabricut.objects.all()

        for product in products:
            try:
                if product.collection != "Collective Threads Trimmings":
                    continue

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
                if product.collection != None and product.collection != "":
                    desc += "Collection: {}<br/><br/>".format(
                        product.collection)
                if product.width != None and product.width != "":
                    desc += "Width: {} in<br/>".format(product.width)
                if product.height != None and product.height != "":
                    desc += "Height: {} in<br/>".format(product.height)
                if product.hr != None and product.hr != "":
                    desc += "Horizontal Repeat: {} in<br/>".format(product.hr)
                if product.vr != None and product.vr != "":
                    desc += "Vertical Repeat: {} in<br/>".format(product.vr)
                if product.rollLength != None and product.rollLength != "":
                    if "Yard" in product.uom and product.minimum < 2:
                        pass
                    else:
                        desc += "Roll Length: {} yds<br/>".format(
                            product.rollLength)
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
                        priceTrade = common.formatprice(cost, markup_trade)
                except:
                    debug("Fabricut", 1, "Price Error: SKU: {}".format(product.sku))
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

                debug("Fabricut", 0, "Updated Existing product ProductID: {}, SKU: {}, Title: {}, Type: {}, Price: {}".format(
                    productId, product.sku, title, product.ptype, price))
            except Exception as e:
                print(e)
                pass

        csr.close()
        con.close()

    def updatePrice(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        products = Fabricut.objects.all()

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
                    debug("Fabricut", 1, "Price Error: SKU: {}".format(product.sku))
                    continue

                try:
                    csr.execute("SELECT PV1.Cost, PV1.Price, PV2.Price AS TradePrice FROM ProductVariant PV1, ProductVariant PV2 WHERE PV1.ProductID = {} AND PV2.ProductID = {} AND PV1.IsDefault = 1 AND PV2.Name LIKE 'Trade - %' AND PV1.Cost IS NOT NULL AND PV2.Cost IS NOT NULL".format(productId, productId))
                    tmp = csr.fetchone()
                    if tmp == None:
                        debug("Fabricut", 2, "Update Price Error: ProductId: {}, MPN: {}".format(
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

                        debug("Fabricut", 0, "Updated price for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                            productId, cost, price, priceTrade))
                    else:
                        debug("Fabricut", 0, "Price is already updated. ProductId: {}, Price: {}, Trade Price: {}".format(
                            productId, price, priceTrade))
                except:
                    debug("Fabricut", 1, "Updating price error for ProductID: {}. COST: {}, Price: {}, Trade Price: {}".format(
                        productId, cost, price, priceTrade))
                    continue

        csr.close()
        con.close()
