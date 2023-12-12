from django.core.management.base import BaseCommand

import os
import environ
import pymysql
import datetime
import re
import boto3
import xml.etree.ElementTree as ET
import xml.dom.minidom as MD

from library import debug, inventory


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"
GS_FEED_DIR = f"{FILEDIR}/feed/DecoratorsBestGS.xml"
FB_FEED_DIR = f"{FILEDIR}/feed/DecoratorsBestFB.xml"

PROCESS = "Feed"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "google" in options['functions']:
            with Processor() as processor:
                processor.gsFeed()

        if "facebook" in options['functions']:
            with Processor() as processor:
                processor.fbFeed()

        if "main" in options['functions']:
            with Processor() as processor:
                processor.gsFeed()
                processor.fbFeed()


class Processor:
    def __init__(self):
        self.env = environ.Env()
        self.bucket = 'decoratorsbestimages'

    def __enter__(self):
        self.con = pymysql.connect(host=self.env('MYSQL_HOST'), user=self.env('MYSQL_USER'), passwd=self.env(
            'MYSQL_PASSWORD'), db=self.env('MYSQL_DATABASE'), connect_timeout=5)
        self.s3 = boto3.client('s3', aws_access_key_id=self.env(
            'aws_access_key'), aws_secret_access_key=self.env('aws_secret_key'))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fmt(self, s):
        s = str(s).replace("N/A", "").replace("n/a", "").replace('', '').replace('¥',
                                                                                  '').replace('…', '').replace('„', '').replace('', '').strip()
        if s != None and s != "":
            allowedCharaters = [" ", ",", ".", "'", "\"", "*",
                                "(", ")", "$", "&", ">", "-", "=", "+", "/", "!", "%", "^", "@", ":", ";", "{", "}", "[", "]", "?"]

            cleaned = [character for character in s if character.isalnum()
                       or character in allowedCharaters]

            return "".join(cleaned)
        else:
            return ""

    def gsFeed(self):
        debug.debug(PROCESS, 0, f"Started running GS {PROCESS} processor.")

        if os.path.isfile(GS_FEED_DIR):
            os.remove(GS_FEED_DIR)

        csr = self.con.cursor()
        csr.execute("""
            SELECT 
                P.SKU,
                P.Title AS PName,
                P.Handle,
                PI.ImageURL,
                M.Name as Manufacturer,
                PV.Price * PV.MinimumQuantity AS Price,
                T.Name AS Type,
                (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=2 AND PT.SKU = P.SKU LIMIT 1) AS DesignStyle,
                (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=3 AND PT.SKU = P.SKU LIMIT 1) AS Color,
                PV.Weight,
                PV.GTIN,
                P.ManufacturerPartNumber,
                P.BodyHTML,
                PV.Cost,
                PV.Price as SPrice,
                P.ProductID,
                P.Pattern,
                PV.MinimumQuantity
            FROM Product P
                LEFT JOIN ProductImage PI ON P.ProductID = PI.ProductID
                LEFT JOIN ProductVariant PV ON P.ProductID = PV.ProductID
                LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU
                LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
                LEFT JOIN Type T ON P.ProductTypeID = T.TypeID
            WHERE PI.ImageIndex = 1
                AND M.Published = 1
                AND P.Published = 1
                AND P.ManufacturerPartNumber <> ''
                AND P.Name NOT LIKE '%Borders'
                AND P.Name NOT LIKE '%Disney'
                AND PV.IsDefault=1
                AND PV.Published=1
                AND PV.Cost != 0
                AND T.NAME NOT IN ("Furniture", "Trim")
                AND M.BRAND NOT IN ("Madcap Cottage", "Jaipur Living", "Phillips", "NOIR")
            """)

        products = csr.fetchall()
        csr.close()

        total, skiped = self.generateXML(products, GS_FEED_DIR)
        if skiped < total * 0.3:
            self.uploadToGS()
        else:
            debug.debug(
                PROCESS, 2, f"Ignore uploading the GS feed because too many items {skiped}/{total} have been skiped")

    def fbFeed(self):
        debug.debug(PROCESS, 0, f"Started running FB {PROCESS} processor.")

        if os.path.isfile(FB_FEED_DIR):
            os.remove(FB_FEED_DIR)

        csr = self.con.cursor()
        csr.execute("""
            SELECT 
                P.SKU,
                P.Title AS PName,
                P.Handle,
                PI.ImageURL,
                M.Name as Manufacturer,
                PV.Price * PV.MinimumQuantity AS Price,
                T.Name AS Type,
                (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=2 AND PT.SKU = P.SKU LIMIT 1) AS DesignStyle,
                (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=3 AND PT.SKU = P.SKU LIMIT 1) AS Color,
                PV.Weight,
                PV.GTIN,
                P.ManufacturerPartNumber,
                P.BodyHTML,
                PV.Cost,
                PV.Price as SPrice,
                P.ProductID,
                P.Pattern,
                PV.MinimumQuantity
            FROM Product P
                LEFT JOIN ProductImage PI ON P.ProductID = PI.ProductID
                LEFT JOIN ProductVariant PV ON P.ProductID = PV.ProductID
                LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU
                LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
                LEFT JOIN Type T ON P.ProductTypeID = T.TypeID
            WHERE PI.ImageIndex = 1
                AND M.Published = 1
                AND P.Published = 1
                AND P.ManufacturerPartNumber <> ''
                AND P.Name NOT LIKE '%Borders'
                AND P.Name NOT LIKE '%Disney'
                AND PV.IsDefault=1
                AND PV.Published=1
                AND PV.Cost != 0
                AND T.Name IN ("Wallpaper", "Pillow")
                AND M.BRAND NOT IN ("Madcap Cottage", "Jaipur Living", "Phillips", "NOIR")
            """)

        products = csr.fetchall()
        csr.close()

        total, skiped = self.generateXML(products, FB_FEED_DIR)
        if skiped < total * 0.3:
            self.uploadToFB()
        else:
            debug.debug(
                PROCESS, 2, f"Ignore uploading the FB feed because too many items {skiped}/{total} have been skiped")

    def generateXML(self, products, feed_dir):
        total = len(products)
        skiped = 0

        root = ET.Element("rss")
        root.set("xmlns:g", "http://base.google.com/ns/1.0")

        channel = ET.SubElement(root, "channel")

        title = ET.SubElement(channel, "title")
        title.text = "DecoratorsBest"

        link = ET.SubElement(channel, "link")
        link.text = "https://www.decoratorsbest.com/"

        description = ET.SubElement(channel, "description")
        description.text = "DecoratorsBest"

        for index, row in enumerate(products):
            sku = self.fmt(str(row[0]))
            pName = self.fmt(str(row[1]).title())
            handle = str(row[2])
            imageURL = str(row[3])
            brand = self.fmt(str(row[4]))
            price = round(float(row[5]), 2)
            ptype = self.fmt(str(row[6]))
            style = self.fmt(str(row[7]))
            color = self.fmt(str(row[8]))
            weight = round(float(row[9]), 2)
            gtin = ''
            mpn = self.fmt(str(row[11]))
            bodyHTML = str(row[12])
            cost = round(float(row[13]), 2)
            sprice = round(float(row[14]), 2)
            productID = str(row[15])
            pattern = self.fmt(str(row[16]))
            minQty = int(row[17])

            # Exceptions
            stock = inventory.inventory(sku)
            if stock["quantity"] < minQty:
                debug.debug(
                    PROCESS, 0, f"{index}/{total}: IGNORED SKU {sku}. Out of stock")
                skiped += 1
                continue

            if (brand == "A-Street Prints Wallpaper" or brand == "Brewster Home Fashions Wallpaper") and "Peel & Stick" in pName:
                debug.debug(
                    PROCESS, 0, f"{index}/{total}: IGNORED SKU {sku}. Brewster Peel & Stick")
                skiped += 1
                continue

            if bool(re.search(r'\bget\b', f"{pName}, {bodyHTML}", re.IGNORECASE)):
                debug.debug(
                    PROCESS, 0, f"{index}/{total}: IGNORED SKU {sku}. 'Get' word in the description")
                skiped += 1
                continue
            ################

            # Refine Information
            title = f"{pName} - {sku}"

            desc = self.fmt(re.sub(r'<br\s?/?>|\n', ' ', bodyHTML))
            if not desc:
                desc = title

            brand = brand.replace("Covington", "DB By DecoratorsBest").replace("Premier Prints", "DB By DecoratorsBest").replace(
                "Materialworks", "DB By DecoratorsBest").replace("Tempaper", "DB By DecoratorsBest Wallpaper")

            if price > 300:
                priceRange = "300+"
            elif price > 250:
                priceRange = "250-300"
            elif price > 200:
                priceRange = "200-250"
            elif price > 150:
                priceRange = "150-200"
            elif price > 100:
                priceRange = "100-150"
            elif price > 50:
                priceRange = "50-100"
            elif price > 25:
                priceRange = "25-50"
            elif price > 10:
                priceRange = "10-25"
            else:
                continue

            margin = int((sprice - cost) / cost * 100)

            if ptype == "Fabric":
                category = "Arts & Entertainment > Hobbies & Creative Arts > Arts & Crafts > Art & Crafting Materials > Textiles > Fabric"
                productType = "Home & Garden > Bed and Living Room > Home Fabric"
            elif ptype == "Wallpaper":
                category = "Home & Garden > Decor > Wallpaper"
                productType = "Home & Garden > Bed and Living Room > Home Wallpaper"
            elif ptype == "Pillow":
                category = "Home & Garden > Decor > Throw Pillows"
                productType = "Home & Garden > Bed and Living Room > Home Pillow"
            elif ptype == "Trim":
                category = "Arts & Entertainment > Hobbies & Creative Arts > Arts & Crafts > Art & Crafting Materials > Embellishments & Trims"
                productType = "Home & Garden > Bed and Living Room > Home Trim"
            elif ptype == "Furniture":
                category = "Furniture"
                productType = "Home & Garden > Bed and Living Room > Home Furniture"
            else:
                category = "Home & Garden > Decor"
                productType = "Home & Garden > Decor"
            category = self.fmt(category)
            productType = self.fmt(productType)

            material = ""
            lines = bodyHTML.replace(
                "<br />", "<br/>").replace("<br/>", "<br>").split("<br>")
            for line in lines:
                if "Material:" in line:
                    material = self.fmt(
                        line.replace("Material:", "").strip())

            if style == "":
                style = pattern
            ##################

            item = ET.SubElement(channel, "item")

            ET.SubElement(item, "g:id").text = f"{sku}"
            ET.SubElement(item, "g:item_group_id").text = f"{productID}"
            ET.SubElement(item, "g:title").text = f"{title}"
            ET.SubElement(item, "g:description").text = f"{desc}"
            ET.SubElement(
                item, "g:google_product_category").text = f"{category}"
            ET.SubElement(
                item, "g:link").text = f"https://www.decoratorsbest.com/products/{handle}"
            ET.SubElement(item, "g:image_link").text = f"{imageURL}"
            ET.SubElement(item, "g:availability").text = "in stock"
            ET.SubElement(
                item, "g:quantity_to_sell_on_facebook").text = f"{stock['quantity']}"
            ET.SubElement(item, "g:gtin").text = f"{gtin}"
            ET.SubElement(item, "g:price").text = f"{price}"
            ET.SubElement(item, "g:brand").text = f"{brand}"
            ET.SubElement(item, "g:mpn").text = f"{mpn}"
            ET.SubElement(item, "g:product_type").text = f"{productType}"
            ET.SubElement(item, "g:condition").text = "new"
            ET.SubElement(item, "g:color").text = f"{color}"
            ET.SubElement(item, "g:pattern").text = f"{style}"
            ET.SubElement(item, "g:shipping_weight").text = f"{weight}"
            ET.SubElement(item, "g:material").text = f"{material}"
            ET.SubElement(item, "g:custom_label_0").text = f"{ptype}"
            ET.SubElement(item, "g:custom_label_1").text = f"{brand}"
            ET.SubElement(item, "g:custom_label_2").text = f"{priceRange}"
            ET.SubElement(item, "g:custom_label_3").text = f"{margin}"

            debug.debug(
                PROCESS, 0, f"{index}/{total}: Success for SKU {sku}. Skiped {skiped} SKUs")

        tree_str = ET.tostring(root, encoding='utf-8')
        tree_dom = MD.parseString(tree_str)
        pretty_tree = tree_dom.toprettyxml(indent="\t")

        with open(feed_dir, 'w', encoding="UTF-8") as file:
            file.write(pretty_tree)

        return (total, skiped)

    def uploadToGS(self):
        now = datetime.datetime.now()

        self.s3.upload_file(GS_FEED_DIR, self.bucket, "DecoratorsBestGS.xml", ExtraArgs={
                            'ACL': 'public-read'})
        debug.debug(
            PROCESS, 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS.xml')

        self.s3.upload_file(
            GS_FEED_DIR, self.bucket, "DecoratorsBestGS-V2.xml", ExtraArgs={'ACL': 'public-read'})
        debug.debug(
            PROCESS, 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS-V2.xml')

        self.s3.upload_file(
            GS_FEED_DIR, self.bucket, f"DecoratorsBestGS-{now.year}-{now.month}-{now.day}.xml", ExtraArgs={'ACL': 'public-read'})
        debug.debug(
            PROCESS, 0, f"Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS-{now.year}-{now.month}-{now.day}.xml")

    def uploadToFB(self):
        self.s3.upload_file(FB_FEED_DIR, self.bucket, "DecoratorsBestFB.xml", ExtraArgs={
                            'ACL': 'public-read'})
        debug.debug(
            PROCESS, 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestFB.xml')
