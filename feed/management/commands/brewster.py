from django.core.management.base import BaseCommand
from feed.models import Brewster

import os
import environ
import pymysql
import xlrd
import time
import paramiko
import csv
import codecs

from library import datasheet, database, debug, common, const


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Brewster"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            processor.downloadDatasheets()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "validate" in options['functions']:
            processor = Processor()
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = Brewster.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.image()

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="", dst=f"{FILEDIR}/brewster-inventory.csv", fileSrc=False)
                    processor.inventory()

                print("Finished process. Waiting for next run. {}:{}".format(
                    BRAND, options['functions']))
                time.sleep(86400)


class Processor:
    def __init__(self):
        self.env = environ.Env()

        self.con = pymysql.connect(host=self.env('MYSQL_HOST'), user=self.env('MYSQL_USER'), passwd=self.env(
            'MYSQL_PASSWORD'), db=self.env('MYSQL_DATABASE'), connect_timeout=5)
        self.datasheetManager = datasheet.DatasheetManager(brand=BRAND)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Brewster)

        try:
            transport = paramiko.Transport(
                (const.sftp[f"{BRAND} Images"]["host"], const.sftp[f"{BRAND} Images"]["port"]))
            transport.connect(
                username=const.sftp[f"{BRAND} Images"]["user"], password=const.sftp[f"{BRAND} Images"]["pass"])
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            debug.debug(BRAND, 1,
                        f"Connection to {BRAND} SFTP Server Failed. Error: {str(e)}")
            sftp = None

        self.imageServer = sftp

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()
        self.imageServer.close()

    def downloadDatasheets(self):
        debug.debug(
            BRAND, 0, "Downloading collection-based product datasheets from Brewster SFTP")

        self.imageServer.chdir(path='/WallpaperBooks')

        collections = self.imageServer.listdir()

        for collection in collections:
            if "All Wallpaper Images" in collection:
                continue

            filename = ''
            collectionDir = self.imageServer.listdir(collection)
            for file in collectionDir:
                if "xlsx" in file:
                    filename = file

            if filename == 'TheCottageData.xlsx':
                continue

            if filename != '':
                try:
                    self.imageServer.get(f"{collection}/{filename}",
                                         f"{FILEDIR}/brewster/{collection}.xlsx")
                    debug.debug(
                        BRAND, 0, f"Downloaded {filename} from Brewster SFTP")
                except Exception as e:
                    debug.debug(
                        BRAND, 1, f"Downloading {filename} from Brewster SFTP has been filed. Error: {str(e)}")
                    continue
            else:
                debug.debug(
                    BRAND, 1, f"No datasheets found in {collection} directory")

        debug.debug(
            BRAND, 0, "Downloading collection-based product datasheets from Brewster SFTP")
        return True

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Price & Discontinued
        discontinuedMPNs = []
        prices = {}

        wb = xlrd.open_workbook(f"{FILEDIR}/brewster-price.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            mpn = common.formatText(sh.cell_value(i, 0))

            if sh.cell_value(i, 14) == "Y":
                discontinuedMPNs.append(mpn)

            cost = common.formatFloat(sh.cell_value(i, 13))
            map = common.formatFloat(sh.cell_value(i, 12))
            msrp = common.formatFloat(sh.cell_value(i, 11))

            prices[mpn] = {
                'cost': cost,
                'map': map,
                'msrp': msrp
            }

        wb = xlrd.open_workbook(f"{FILEDIR}/brewster-od.xls")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            mpn = common.formatText(sh.cell_value(i, 2))

            if mpn not in discontinuedMPNs:
                discontinuedMPNs.append(mpn)

        # Best Sellers
        bestsellingMPNs = []

        wb = xlrd.open_workbook(f"{FILEDIR}/brewster-bestsellers.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            mpn = common.formatText(sh.cell_value(i, 0))
            bestsellingMPNs.append(mpn)

        # Get Product Feed
        products = []

        for datasheet in os.listdir(f"{FILEDIR}/brewster"):
            if "$" in datasheet or "~" in datasheet:
                continue

            headers, data = self.datasheetManager.readDatasheet(
                datasheetType="XLSX",
                datasheetPath=f"{FILEDIR}/brewster/{datasheet}",
            )

            manufacturerId = -1
            mpnId = -1
            nameId = -1
            usageId = -1
            descriptionId = -1
            msrpId = -1
            mapId = -1
            widthId = -1
            heightId = -1
            coverageId = -1
            repeatId = -1
            matchId = -1
            pasteId = -1
            materialId = -1
            washId = -1
            removeId = -1
            colorId = -1
            colorsId = -1
            styleId = -1
            patternId = -1
            themeId = -1
            bullet1Id = -1
            bullet2Id = -1
            bullet3Id = -1
            bullet4Id = -1
            bullet5Id = -1

            for colId, header in enumerate(headers):
                if header == "Brand":
                    manufacturerId = colId
                elif header == "Pattern" and colId < 10:
                    mpnId = colId
                elif header == "Name":
                    nameId = colId
                elif header == "Product Type":
                    usageId = colId
                elif header == "Description":
                    descriptionId = colId
                elif header == "MSRP" or "Original Unit Retail" in header:
                    msrpId = colId
                elif header == "MAP":
                    mapId = colId
                elif "Width" in header:
                    widthId = colId
                elif "Length" in header:
                    heightId = colId
                elif header == "Coverage":
                    coverageId = colId
                elif "Repeat" in header:
                    repeatId = colId
                elif header == "Match":
                    matchId = colId
                elif header == "Paste":
                    pasteId = colId
                elif header == "Material":
                    materialId = colId
                elif header == "Washability":
                    washId = colId
                elif header == "Removability":
                    removeId = colId
                elif header == "Colorway":
                    colorId = colId
                elif header == "Color Family":
                    colorsId = colId
                elif header == "Style":
                    styleId = colId
                elif header == "Pattern" and colId > 10:
                    patternId = colId
                elif header == "Theme":
                    themeId = colId
                elif header == "Bullet Point 1":
                    bullet1Id = colId
                elif header == "Bullet Point 2":
                    bullet2Id = colId
                elif header == "Bullet Point 3":
                    bullet3Id = colId
                elif header == "Bullet Point 4":
                    bullet4Id = colId
                elif header == "Bullet Point 5":
                    bullet5Id = colId

            for row in data:
                try:
                    # Primary Attributes
                    mpn = common.formatInt(row[mpnId])
                    if mpn == 0:
                        mpn = common.formatText(row[mpnId])

                    if row[manufacturerId] == "A-Street Prints":
                        sku = f"Street {mpn}"
                    else:
                        sku = f"Brewster {mpn}"

                    pattern = common.formatText(row[patternId])

                    if pattern == "":
                        pattern = mpn

                    if colorId > -1:
                        color = common.formatText(row[colorId])
                    elif colorsId > -1:
                        color = common.formatText(row[colorsId])
                    else:
                        debug.debug(BRAND, 1, f"Color Error for MPN: {mpn}")
                        continue

                    if color == "":
                        color = "Multicolor"

                    if nameId > 0:
                        name = common.formatText(row[nameId])
                    else:
                        name = ""

                    # Categorization
                    brand = BRAND
                    type = "Wallpaper"

                    if row[manufacturerId] == "A-Street Prints":
                        manufacturer = "A-Street Prints Wallpaper"
                    else:
                        manufacturer = "Brewster Home Fashions Wallpaper"

                    collection = datasheet.replace('.xlsx', '')
                    if row[manufacturerId] != "Brewster" and row[manufacturerId] != "A-Street Prints" and row[manufacturerId] not in collection:
                        collection = f"{row[manufacturerId]} {collection}"

                    custom = {
                        'originalBrand': row[manufacturerId]
                    }

                    # Main Information
                    description = common.formatText(row[descriptionId])
                    usage = common.formatText(row[usageId])
                    width = common.formatFloat(row[widthId])
                    height = common.formatFloat(row[heightId])
                    repeat = common.formatText(row[repeatId])

                    # Additional Information
                    yards = round(height / 3, 2)

                    if bullet1Id > 0:
                        bullet1 = common.formatText(row[bullet1Id])
                    else:
                        bullet1 = f"Coverage: {common.formatText(row[coverageId])}"

                    if bullet2Id > 0:
                        bullet2 = common.formatText(row[bullet2Id])
                    else:
                        bullet2 = f"Match: {common.formatText(row[matchId])}"

                    if bullet3Id > 0:
                        bullet3 = common.formatText(row[bullet3Id])
                    else:
                        bullet3 = f"Paste: {common.formatText(row[pasteId])} <br>Material: {common.formatText(row[materialId])}"

                    if bullet4Id > 0:
                        bullet4 = common.formatText(row[bullet4Id])
                    else:
                        bullet4 = f"Washability: {common.formatText(row[washId])}"

                    if bullet5Id > 0:
                        bullet5 = common.formatText(row[bullet5Id])
                    else:
                        bullet5 = f"Removability: {common.formatText(row[removeId])}"

                    features = [bullet1, bullet2, bullet3, bullet4, bullet5]

                    # Pricing
                    if msrpId > 0:
                        msrp = common.formatFloat(row[msrpId])
                        cost = common.formatFloat(msrp / 2)
                    else:
                        debug.debug(BRAND, 1, f"Cost Error for MPN: {mpn}")

                    if mapId > 0:
                        map = common.formatFloat(row[msrpId])
                    else:
                        map = 0

                    if mpn in prices:
                        cost = prices[mpn]['cost']
                        map = prices[mpn]['map']
                        msrp = prices[mpn]['msrp']

                    # Measurement
                    uom = "Per Roll"

                    # Tagging
                    style = row[styleId]
                    category = row[themeId]
                    tags = f"{pattern}, {style}, {category}, {description}"

                    colors = color

                    # Status
                    if collection == 'Scalamandre' or mpn in discontinuedMPNs or row[manufacturerId] == "Eijffinger" or row[manufacturerId] == "Eiffinger":
                        statusP = False
                    else:
                        statusP = True

                    statusS = True

                    if mpn in bestsellingMPNs:
                        bestSeller = True
                    else:
                        bestSeller = False

                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    continue

                product = {
                    'mpn': mpn,
                    'sku': sku,
                    'pattern': pattern,
                    'color': color,
                    'name': name,

                    'brand': brand,
                    'type': type,
                    'manufacturer': manufacturer,
                    'collection': collection,

                    'description': description,
                    'usage': usage,
                    'width': width,
                    'height': height,
                    'repeat': repeat,
                    'custom': custom,

                    'yards': yards,
                    'features': features,

                    'cost': cost,
                    'map': map,
                    'msrp': msrp,
                    'uom': uom,

                    'tags': tags,
                    'colors': colors,

                    'statusP': statusP,
                    'statusS': statusS,
                    'bestSeller': bestSeller,

                }
                products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        unknownPath = []

        hasImage = []

        con = self.con
        csr = con.cursor()
        csr.execute(
            f"SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = '{BRAND}'")
        for row in csr.fetchall():
            hasImage.append(str(row[0]))
        csr.close()

        products = Brewster.objects.all()
        for product in products:
            if not product.productId or product.productId in hasImage:
                continue

            collection = product.collection
            mpn = product.mpn
            productId = product.productId

            try:
                originalBrand = product.custom['originalBrand']
                if originalBrand != "Advantage" and collection != "Eijffinger Web Only":
                    collection = collection.replace(originalBrand, "").strip()

                try:
                    self.imageServer.chdir(
                        path='/WallpaperBooks/{}/Images/300dpi'.format(collection))
                except:
                    try:
                        self.imageServer.chdir(
                            path='/WallpaperBooks/{}/Images/72dpi'.format(collection))
                    except:
                        self.imageServer.chdir(
                            path='/WallpaperBooks/{}/Images'.format(collection))

                files = self.imageServer.listdir()

                if "{}.jpg".format(mpn) in files:
                    self.imageServer.get(
                        f"{mpn}.jpg", f"{FILEDIR}/../../../images/product/{productId}.jpg")
                    debug.debug(
                        BRAND, 0, f"downloaded product image {productId}.jpg")

                    # Only if thumbnail exists
                    if f"{mpn}_Room.jpg" in files:
                        self.imageServer.get(
                            f"{mpn}_Room.jpg", f"{FILEDIR}/../../../images/roomset/{productId}_2.jpg")
                        debug.debug(
                            BRAND, 0, f"downloaded roomset image {productId}_2.jpg")

                    if f"{mpn}_Room_2.jpg" in files:
                        self.imageServer.get(
                            f"{mpn}_Room_2.jpg", f"{FILEDIR}/../../../images/roomset/{productId}_3.jpg")
                        debug.debug(
                            BRAND, 0, f"downloaded roomset image {productId}_3.jpg")

                    if f"{mpn}_Room_3.jpg" in files:
                        self.imageServer.get(
                            f"{mpn}_Room_3.jpg", f"{FILEDIR}/../../../images/roomset/{productId}_4.jpg")
                        debug.debug(
                            BRAND, 0, f"downloaded roomset image {productId}_4.jpg")

                    if f"{mpn}_Room_4.jpg" in files:
                        self.imageServer.get(
                            f"{mpn}_Room_4.jpg", f"{FILEDIR}/../../../images/roomset/{productId}_5.jpg")
                        debug.debug(
                            BRAND, 0, f"downloaded roomset image {productId}_5.jpg")
            except:
                if collection not in unknownPath:
                    unknownPath.append(collection)
                continue

        print(unknownPath)

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/brewster-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            mpn = row[0]
            try:
                product = Brewster.objects.get(mpn=mpn)
            except Brewster.DoesNotExist:
                continue

            sku = product.sku
            stockP = common.formatInt(row[3])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)

    def hires(self):
        con = self.con
        csr = con.cursor()
        csr.execute(
            f"SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 20 AND M.Brand = '{BRAND}'")

        hasImage = []
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        csr.close()

        self.imageServer.chdir(path='/WallpaperBooks')
        collections = self.imageServer.listdir()

        for collection in collections:
            try:
                self.imageServer.chdir(
                    path=f"/WallpaperBooks/{collection}/Images/300dpi")
                files = self.imageServer.listdir()

                for file in files:
                    mpn = file.split(".")[0]

                    try:
                        product = Brewster.objects.get(mpn=mpn)
                    except Brewster.DoesNotExist:
                        continue

                    productId = product.productId
                    if productId in hasImage:
                        continue

                    self.imageServer.get(
                        file, f"{FILEDIR}/../../../images/hires/{productId}_20.jpg")
                    debug.debug(
                        BRAND, 0, f"downloaded hires image {productId}_20.jpg")
            except Exception as e:
                print(e)
                continue
