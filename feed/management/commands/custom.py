from django.core.management.base import BaseCommand
from django.db.models import Q

import os
import environ
import pymysql
import requests
import environ
import json
import time


from library import debug, shopify, common

from shopify.models import Variant, Product
from mysql.models import ProductSubtype, Type
from feed.models import Schumacher

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

env = environ.Env()
SHOPIFY_API_URL = f"https://decoratorsbest.myshopify.com/admin/api/{env('shopify_api_version')}"
SHOPIFY_PRODUCT_API_HEADER = {
    'X-Shopify-Access-Token': env('shopify_product_token'),
    'Content-Type': 'application/json'
}


class Command(BaseCommand):
    help = "Custom Commands"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "samplePrice" in options['functions']:
            processor = Processor()
            processor.updateSamplePrices()

        if "deleteSubtypeTags" in options['functions']:
            processor = Processor()
            processor.deleteSubtypeTags()

        if "getTypeList" in options['functions']:
            processor = Processor()
            processor.getTypeList()

        if "refreshPrices" in options['functions']:
            processor = Processor()
            processor.refreshPrices()

        if "removeTags" in options['functions']:
            processor = Processor()
            processor.removeTags()

        if "addTags" in options['functions']:
            processor = Processor()
            processor.addTags()

        if "removeSubTypes" in options['functions']:
            processor = Processor()
            processor.removeSubTypes()

        if "deleteProducts" in options['functions']:
            processor = Processor()
            processor.deleteProducts()

        if "syncHandle" in options['functions']:
            processor = Processor()
            processor.syncHandle()

        if "unpublishBrand" in options['functions']:
            processor = Processor()
            processor.unpublishBrand()


class Processor:
    def __init__(self):
        self.env = environ.Env()

        self.con = pymysql.connect(host=self.env('MYSQL_HOST'), user=self.env('MYSQL_USER'), passwd=self.env(
            'MYSQL_PASSWORD'), db=self.env('MYSQL_DATABASE'), connect_timeout=5)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def updateSamplePrices(self):
        samples = Variant.objects.filter(
            name__icontains='Sample - ').exclude(name__icontains='Free Sample -').filter(price=5)

        total = len(samples)
        for index, sample in enumerate(samples):
            try:
                typeId = sample.product.productTypeId

                if typeId == 1 or typeId == 2 or typeId == 5:
                    newPrice = 7
                elif typeId == 4:
                    newPrice = 15
                else:
                    continue

                sample.price = newPrice
                sample.save()

                requests.put(f"{SHOPIFY_API_URL}/variants/{sample.variantId}.json", headers=SHOPIFY_PRODUCT_API_HEADER,
                             json={"variant": {'id': sample.variantId, 'price': sample.price}})

                debug.debug(
                    "Custom", 0, f"{index}/{total} -- updated '{sample.name}' price to ${sample.price}")

            except Exception as e:
                debug.debug("Custom", 1, str(e))
                continue

    def deleteSubtypeTags(self):
        csr = self.con.cursor()

        subtypeId = 65
        products = Schumacher.objects.filter(
            Q(type="Wallpaper") | Q(type="Fabric"))

        for product in products:
            sku = product.sku
            productId = product.productId

            if not sku or not productId:
                continue

            try:
                productSubtype = ProductSubtype.objects.get(
                    sku=sku, subtypeId=subtypeId)
                productSubtype.delete()

                csr.execute(
                    f"CALL AddToPendingUpdateTagBodyHTML ({productId})")
                self.con.commit()

                debug.debug(
                    "Custom", 0, f"Deleted Subtype {subtypeId} for SKU: {sku}, ProductId: {productId}")

            except ProductSubtype.DoesNotExist:
                continue

        csr.close()

    def getTypeList(self):
        types = Type.objects.filter(Q(parentTypeId=6) | Q(parentTypeId=7) | Q(
            parentTypeId=8) | Q(parentTypeId=40) | Q(parentTypeId=41))
        for type in types:
            print(type.name)
        print(len(types))

    def refreshPrices(self):
        csr = self.con.cursor()

        brandsRefreshed = ["Surya", "Kravet", "Brewster",
                           "Phillip Jeffries", "Scalamandre", "Pindler"]
        brandsToRefresh = [
            "Brewster",
            "Couture",
            "Covington",
            "DanaGibson",
            "ElaineSmith",
            "JaipurLiving",
            "JamieYoung",
            "JFFabrics",
            "Kasmir",
            "Kravet",
            "KravetDecor",
            "MadcapCottage",
            "Materialworks",
            "Maxwell",
            "MindTheGap",
            "Phillips",
            "PhillipJeffries",
            "Pindler",
            "Port68",
            "PremierPrints",
            "Scalamandre",
            "Schumacher",
            "Seabrook",
            "StarkStudio",
            "Stout",
            "Surya",
            "TresTintas",
            "York",
            "Zoffany",
        ]

        for brand in brandsToRefresh:
            if brand in brandsRefreshed:
                continue

            csr.execute(f"""
                SELECT P.ProductId
                FROM Product P
                LEFT JOIN ProductManufacturer PM ON PM.SKU = P.SKU
                LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
                WHERE M.BRAND = "{brand}" AND P.ProductId IS NOT NULL
            """)
            products = csr.fetchall()

            for product in products:
                productId = product[0]
                csr.execute(
                    "CALL AddToPendingUpdatePrice ({})".format(productId))
                self.con.commit()

                debug.debug(
                    "Custom", 0, f"Updated {brand} prices. Product {productId}")

        csr.close()

    def addTags(self):
        tag = "NoSample"
        con = self.con
        csr = con.cursor()

        products = Product.objects.filter(Q(productTypeId=5) | Q(productTypeId=23) | Q(productTypeId=24) | Q(
            productTypeId=90) | Q(productTypeId=91) | Q(productTypeId=92) | Q(productTypeId=95) | Q(productTypeId=96))

        for product in products:
            if product.productId:
                csr.execute("CALL AddToProductTag ({}, {})".format(
                    common.sq(product.sku), common.sq(tag)))
                con.commit()
                debug.debug(
                    "Custom", 0, "{} Tag has been applied to {}".format(tag, product.sku))

                csr.execute("CALL AddToPendingUpdateTagBodyHTML ({})".format(
                    product.productId))
                con.commit()

    def removeTags(self):
        tagId = 282

        csr = self.con.cursor()

        csr.execute(f"""
            SELECT DISTINCT P.ProductId, P.SKU, P.Title
            FROM Product P
            LEFT JOIN ProductTag PT ON P.SKU = PT.SKU
            WHERE PT.TagId = {tagId} AND P.ProductTypeId != 5
        """)
        rows = csr.fetchall()

        for row in rows:
            productId = row[0]
            sku = row[1]
            title = row[2]

            csr.execute(
                f"DELETE FROM ProductTag WHERE SKU = '{sku}' AND TagId = {tagId}")
            self.con.commit()

            csr.execute(f"CALL AddToPendingUpdateTagBodyHTML ({productId})")
            self.con.commit()

            debug.debug("Custom", 0, f"Removed tag {tagId} from {title}")

        csr.close()

    def removeSubTypes(self):
        subtypId = 94

        csr = self.con.cursor()

        csr.execute(f"""
            SELECT DISTINCT P.ProductId, P.SKU, P.Title
            FROM Product P
            LEFT JOIN ProductSubtype PT ON P.SKU = PT.SKU
            LEFT JOIN ProductManufacturer PM ON PM.SKU = P.SKU
            LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
            WHERE PT.SubtypeId = {subtypId} AND P.ProductTypeId = 4 AND M.Brand = 'Jaipur Living'
        """)
        rows = csr.fetchall()

        for row in rows:
            productId = row[0]
            sku = row[1]
            title = row[2]

            csr.execute(
                f"DELETE FROM ProductSubtype WHERE SKU = '{sku}' AND SubtypeId = {subtypId}")
            self.con.commit()

            csr.execute(f"CALL AddToPendingUpdateTagBodyHTML ({productId})")
            self.con.commit()

            debug.debug(
                "Custom", 0, f"Removed subtype {subtypId} from {title}")

        csr.close()

    def deleteProducts(self):
        csr = self.con.cursor()

        productIDs = [
            '6898897256494',
        ]

        for productID in productIDs:
            csr.execute("""SELECT P.ProductID, P.SKU 
                FROM Product P LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                WHERE P.ProductID = '{}'""".format(productID))

            # try:
            if True:
                row = csr.fetchone()
                productID = row[0]
                sku = row[1]
            # except Exception as e:
            #     print(e)

            # try:
            if True:
                shopify.DeleteProductByProductID(productID)
            # except Exception as e:
            #     print(e)

            try:
                csr.execute(
                    "DELETE from Product where productID={}".format(productID))
                self.con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductImage where productID='{}';".format(productID))
                self.con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductInventory where SKU='{}';".format(sku))
                self.con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductManufacturer where SKU='{}';".format(sku))
                self.con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductSubcategory where SKU='{}';".format(sku))
                self.con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductSubtype where SKU='{}';".format(sku))
                self.con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductTag where SKU='{}';".format(sku))
                self.con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductVariant where SKU='{}'".format(sku))
                self.con.commit()
            except Exception as e:
                print(e)
                pass

            debug.debug(
                "Custom", 0, f"Deleted --- ProductID: {productID}, sku: {sku}")

        csr.close()

    def syncHandle(self):
        csr = self.con.cursor()

        brand = "Surya"

        csr.execute(f"""
            SELECT P.ProductId, P.Handle
            FROM Product P
            LEFT JOIN ProductManufacturer PM ON PM.SKU = P.SKU
            LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
            WHERE M.Brand = '{brand}' AND P.ProductId IS NOT NULL
        """)
        products = csr.fetchall()

        total = len(products)
        for index, product in enumerate(products):
            try:
                productId = product[0]
                productHandle = product[1]

                res = requests.get(
                    f"{SHOPIFY_API_URL}/products/{productId}.json?fields=handle", headers=SHOPIFY_PRODUCT_API_HEADER)
                data = json.loads(res.text)

                if data.get("errors"):
                    debug.debug(
                        "Custom", 1, f"Getting product {productId} Error: {data.get('errors')}")
                    time.sleep(5)
                    continue

                handle = data['product']['handle']

                if handle != productHandle:
                    csr.execute(
                        "UPDATE Product SET Handle = %s WHERE ProductID = %s", (handle, productId))
                    self.con.commit()

                    debug.debug(
                        "Custom", 0, f"{index}/{total}: Update product {productId} handle to {handle}.")

                else:
                    debug.debug(
                        "Custom", 0, f"{index}/{total}: Already Good {productId} handle {handle}.")

            except Exception as e:
                debug.debug("Custom", 1, str(e))
                time.sleep(5)
                continue

        csr.close()

    def unpublishBrand(self):
        brand = "Tres Tintas"

        debug.debug(brand, 0, f"Started unpublishing {brand}")

        csr = self.con.cursor()
        csr.execute(f"""SELECT P.ProductID,P.ManufacturerPartNumber,P.Published
                    FROM Product P
                    WHERE P.ManufacturerPartNumber<>'' AND P.ProductID IS NOT NULL AND P.ProductID != 0
                    AND P.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = '{brand}')""")
        rows = csr.fetchall()

        for row in rows:
            productID = row[0]
            mpn = row[1]

            csr.execute(
                "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
            self.con.commit()
            csr.execute(
                "CALL AddToPendingUpdatePublish ({})".format(productID))
            self.con.commit()

            debug.debug(
                brand, 0, f"Disabled product -- Brand: {brand}, ProductID: {productID}, mpn: {mpn}")

        debug.debug(
            brand, 0, f"Finished unpublishing {brand}. total: {len(rows)}")

        csr.close()
