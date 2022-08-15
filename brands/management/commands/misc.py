import json
import random
from monitor.models import Log
from mysql.models import PendingUpdateTag
from shopify.models import Product, Variant
from django.core.management.base import BaseCommand

import os
import pymysql
import time
import requests

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

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Misc commands'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "deleteBuggyVariants" in options['functions']:
            self.deleteBuggyVariants()

        if "deleteBuggyProducts" in options['functions']:
            self.deleteBuggyProducts()

        if "deleteProduct" in options['functions']:
            self.deleteProduct(None)

        if "deleteProducts" in options['functions']:
            self.deleteProducts()

        if "disableBrand" in options['functions']:
            self.disableBrand()

        if "removeNewTag" in options['functions']:
            while True:
                self.removeNewTag()
                print("waiting for next run for 1 week. ")
                time.sleep(86400 * 7)

        if "clearLog" in options['functions']:
            self.clearLog()

        if "deleteShopifyProductsNotInDatabase" in options['functions']:
            self.deleteShopifyProductsNotInDatabase()

        if "colorCollection" in options['functions']:
            self.colorCollection()

    def deleteBuggyVariants(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""DELETE FROM ProductVariant
        WHERE VariantId IS NULL OR VariantId = '' OR ProductId IS NULL OR ProductId = '' OR SKU IS NULL OR SKU = '';""")
        con.commit()

        csr.execute("""DELETE FROM Product
        WHERE ProductId IS NULL OR ProductId = '' OR SKU IS NULL OR SKU = '';""")
        con.commit()

        # csr.execute("""DELETE v1 FROM ProductVariant v1
        # INNER JOIN ProductVariant v2
        # WHERE v1.VariantId = v2.VariantId AND v1.Position IS NULL AND v2.Position IS NOT NULL;""")
        # con.commit()

        # csr.execute("""DELETE v1 FROM ProductVariant v1
        # INNER JOIN ProductVariant v2
        # WHERE v1.VariantId = v2.VariantId AND v1.IsDefault != 1 AND v2.IsDefault = 1;""")
        # con.commit()

        # csr.execute("""DELETE v1 FROM ProductVariant v1
        # INNER JOIN ProductVariant v2
        # WHERE v1.VariantId = v2.VariantId AND v1.IsDefault = v2.IsDefault AND v1.Position = v2.Position AND v1.createdAt < v2.createdAt;""")
        # con.commit()

    def disableBrand(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # brands_to_disable = ["Robert Allen", "Duralee", "Beacon Hill", "Highland Court",
        #                      "Jamie Young", "Cyan", "Noir", "Kravet Decor", "Nature's Decoration", "DecoratorsBest", "Fabricut", "Fabric"]  # 2/14 Disable Fabricut
        brands_to_disable = ["Fabric"]

        for brand in brands_to_disable:
            debug("Misc", 0, "--- Started Disabling {} ---".format(brand))

            csr.execute("""SELECT P.ProductID, P.Title, M.Brand
            FROM Product P LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID 
            WHERE P.ProductID IS NOT NULL And P.ProductID != 0 AND P.Published != 0 AND M.Brand = "{}";""".format(brand, brand))

            success = 0
            failed = 0

            for product in csr.fetchall():
                productID = product[0]
                productTitle = product[1]

                try:
                    csr.execute(
                        "UPDATE Product SET Published=0 WHERE ProductID={}".format(productID))
                    con.commit()
                    csr.execute(
                        "CALL AddToPendingUpdatePublish ({})".format(productID))
                    con.commit()

                    debug("Misc", 0, "Disable Brand: {}. Unpublished --- ProductID: {}, Title: {}, Brand: {}".format(
                        brand, productID, productTitle, brand))
                    success += 1
                except:
                    failed += 1
                    continue

            debug("Misc", 0, "--- Completed Disabling {}. Success: {}, Failed: {} ---".format(brand, success, failed))

        csr.close()
        con.close()

    # Bug code. Locking the Tagging queue. Do NOT run
    def removeNewTag(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT ProductID, SKU, Published FROM Product
        WHERE ManufacturerPartNumber<>'' AND ProductID IS NOT NULL AND ProductID != 0
        AND SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        );""")
        rows = csr.fetchall()

        for row in rows:
            productId = row[0]
            try:
                PendingUpdateTag.objects.create(productId=productId)
                debug("Misc", 0, "Success adding {} to pending tags".format(
                    productId))
            except Exception as e:
                print(e)
                debug("Misc", 1, "Failed adding {} to pending tags".format(
                    productId))

    def clearLog(self):
        Log.objects.all().delete()

    def deleteBuggyProducts(self):
        products = ['6759024164910', '6759024295982',
                    '6759024492590', '6759024656430', '6759024885806', '6759025082414', ]

        for productId in products:
            self.deleteProduct(productId)

    def deleteProduct(self, productID):
        # productID = "6811404959790"

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID, P.SKU 
        FROM Product P LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE P.ProductID = '{}'""".format(productID))

        total, success, failed = 0, 0, 0

        row = csr.fetchone()

        productID = row[0]
        sku = row[1]

        total += 1
        try:
            success += 1
            shopify.DeleteProductByProductID(productID)
        except Exception as e:
            failed += 1
            print(e)

        try:
            csr.execute(
                "DELETE from Product where productID={}".format(productID))
            con.commit()
        except Exception as e:
            print(e)
            pass

        try:
            csr.execute(
                "DELETE from ProductImage where productID='{}';".format(productID))
            con.commit()
        except Exception as e:
            print(e)
            pass

        try:
            csr.execute(
                "DELETE from ProductInventory where SKU='{}';".format(sku))
            con.commit()
        except Exception as e:
            print(e)
            pass

        try:
            csr.execute(
                "DELETE from ProductManufacturer where SKU='{}';".format(sku))
            con.commit()
        except Exception as e:
            print(e)
            pass

        try:
            csr.execute(
                "DELETE from ProductSubcategory where SKU='{}';".format(sku))
            con.commit()
        except Exception as e:
            print(e)
            pass

        try:
            csr.execute(
                "DELETE from ProductSubtype where SKU='{}';".format(sku))
            con.commit()
        except Exception as e:
            print(e)
            pass

        try:
            csr.execute(
                "DELETE from ProductTag where SKU='{}';".format(sku))
            con.commit()
        except Exception as e:
            print(e)
            pass

        try:
            csr.execute(
                "DELETE from ProductVariant where SKU='{}'".format(sku))
            con.commit()
        except Exception as e:
            print(e)
            pass

        debug("Misc", 0, "Deleted --- ProductID: {}, sku: {}".format(productID, sku))

        csr.close()
        con.close()

    def deleteProducts(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ProductID, P.SKU 
        FROM Product P LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        WHERE P.ProductID IS NOT NULL AND P.ProductID != 0 AND M.Name = 'P/K Lifestyles Wallpaper';""")

        total, success, failed = 0, 0, 0

        deleteList = csr.fetchall()
        print(deleteList)
        length = len(deleteList)

        for row in deleteList:
            productID = row[0]
            sku = row[1]

            total += 1
            try:
                success += 1
                shopify.DeleteProductByProductID(productID)
            except Exception as e:
                failed += 1
                print(e)
                continue

            try:
                csr.execute(
                    "DELETE from Product where productID={}".format(productID))
                con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductImage where productID='{}';".format(productID))
                con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductInventory where SKU='{}';".format(sku))
                con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductManufacturer where SKU='{}';".format(sku))
                con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductSubcategory where SKU='{}';".format(sku))
                con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductSubtype where SKU='{}';".format(sku))
                con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductTag where SKU='{}';".format(sku))
                con.commit()
            except Exception as e:
                print(e)
                pass

            try:
                csr.execute(
                    "DELETE from ProductVariant where SKU='{}'".format(sku))
                con.commit()
            except Exception as e:
                print(e)
                pass

            debug("Misc", 0, "{} out of {}: Deleted --- ProductID: {}, sku: {}".format(
                total, length, productID, sku))

        csr.close()
        con.close()

    def deleteShopifyProductsNotInDatabase(self):
        products = shopify.getProductsByVendor("Sure Strip Wallpaper")

        print(products)

    def randSubcolorCollectionHTML(self, parentColorTitle, subColorTitle, parentColorType, parentColorHandle):
        typePlural = "fabrics"
        typeSinglar = "fabric"
        if parentColorType == "Wallpaper":
            typePlural = "wallpapers"
            typeSinglar = "wallpaper"

        otherType = "Wallpapers"
        otherHandle = parentColorHandle
        if parentColorType == "Wallpaper":
            otherType = "Fabrics"
            otherHandle = otherHandle.replace('wallpaper', 'fabrics')
        else:
            otherHandle = otherHandle.replace('fabrics', 'wallpaper')

        htmls = [
            "Looking for <strong>{} {} {}</strong>? You've come to the right place. DecoratorsBest has the widest and finest collection of {} {} {}. Discover our collection of unique brand {} available to help you create the look you want in any room.".format(
                subColorTitle, parentColorTitle, parentColorType, subColorTitle.lower(), parentColorTitle.lower(), typePlural, typePlural),

            "You've come to the right place for <strong>{} {} {}</strong>. DecoratorsBest has the largest collection of {} {} {} at the best prices. Discover a unique selection of designer {} available to help create the personal look you desire for any room in your home.".format(
                subColorTitle, parentColorTitle, parentColorType, subColorTitle.lower(), parentColorTitle.lower(), typePlural, typePlural),

            "Searching for <strong>{} {} {}</strong>? DecoratorsBest has the largest collection of {} {} {} at the best prices. Discover a unique selection of designer {} available to buy online to create your own look for any room in your house.".format(
                subColorTitle, parentColorTitle, parentColorType, subColorTitle.lower(), parentColorTitle.lower(), typePlural, typePlural),
        ]

        html = htmls[random.choice([0, 1, 2])]

        realted = "<em>Related {} collections: <a href='/collections/{}/' style='text-decoration: underline;'>{} {}</a></em>".format(
            typeSinglar, parentColorHandle, parentColorTitle, parentColorType)
        other = "<em>{} to go with these {}: <a href='/collections/{}/' style='text-decoration: underline;'>{} {}</a></em>".format(
            otherType, typePlural, otherHandle, parentColorTitle, otherType)

        html = "<p>" + html + "</p><p>" + realted + "</p><p>" + other + "</p>"

        return html

    def colorCollection(self):
        API_VERSION = env('shopify_api_version')
        API_KEY = env('shopify_general_key')
        API_PASS = env('shopify_general_password')

        API_URL = "https://{}:{}@decoratorsbest.myshopify.com/admin/api/{}".format(
            API_KEY, API_PASS, API_VERSION)

        parentCollectionIds = [
            # '96296697923',  # Beige Wallpaper
            # '96291717187',  # Beige Fabrics
            # '96296435779',  # Black Wallpaper
            # '96291258435',  # Black Fabrics
            # '96296501315',  # Blue Wallpaper
            # '96291389507',  # Blue Fabrics
            # '96296534083',  # Blue-Green Wallpaper
            # '96291422275',  # Blue/Green Fabrics
            # '96296566851',  # Brown Wallpaper
            # '96291487811',  # Brown Fabrics
            # '96296599619',  # Green Wallpaper
            # '96291553347',  # Green Fabrics
            # '96296632387',  # Grey Wallpaper
            # '96291618883',  # Grey Fabrics
            # '96296665155',  # Multi-Colored Wallpaper
            # '96291651651',  # Multi-Colored Fabrics
            # '96296730691',  # Orange Wallpaper
            # '96291782723',  # Orange Fabrics
            # '96296763459',  # Pink Wallpaper
            # '96291848259',  # Pink Fabrics
            # '96296861763',  # Tan Wallpaper
            # '96291979331',  # Tan Fabrics
            # '96296927299',  # Yellow Wallpaper
            # '96292077635',  # Yellow Fabrics
            '96296828995',  # Red Wallpaper
            '96291946563',  # Red Fabrics
            '96296796227',  # Purple Wallpaper
            '96291881027',  # Purple Fabrics
        ]

        for parentCollectionId in parentCollectionIds:
            parentCollectionRes = requests.request(
                "GET", "{}/smart_collections/{}.json".format(API_URL, parentCollectionId), headers={}, data={})

            parentCollection = json.loads(parentCollectionRes.text)
            parentColorTitle = str(
                parentCollection['smart_collection']['title']).split(' ')[0]
            parentColorType = str(
                parentCollection['smart_collection']['title']).split(' ')[1]
            parentColorHandle = parentCollection['smart_collection']['handle']

            parentCollectionMetaRes = requests.request(
                "GET", "{}/smart_collections/{}/metafields.json".format(API_URL, parentCollectionId), headers={}, data={})
            parentCollectionMeta = json.loads(parentCollectionMetaRes.text)

            subColors = []
            for meta in parentCollectionMeta['metafields']:
                if meta['key'] == 'colors':
                    subColors = json.loads(meta['value'])
                    break

            for subColor in subColors['relatives']:
                subColorTitle = str(subColor['title']).replace(
                    parentColorType, '')
                subColorSlug = str(subColor['slug']).replace(
                    '/collections/', '')

                subColorCollectionRes = requests.request(
                    "GET", "{}/smart_collections.json?handle={}".format(API_URL, subColorSlug), headers={}, data={})
                subColorCollection = json.loads(subColorCollectionRes.text)

                subColorCollectionId = subColorCollection['smart_collections'][0]['id']

                body = self.randSubcolorCollectionHTML(
                    parentColorTitle, subColorTitle, parentColorType, parentColorHandle)

                try:
                    requests.request(
                        "PUT",
                        "{}/smart_collections/{}.json".format(
                            API_URL, subColorCollectionId),
                        headers={'Content-Type': 'application/json'},
                        data=json.dumps({
                            "smart_collection": {
                                "body_html": body
                            }
                        })
                    )

                    print("Subcolor collection {} {} {} has been updated successfully".format(
                        subColorTitle, parentColorTitle, parentColorType))
                except Exception as e:
                    print(e)
