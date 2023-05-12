from django.core.management.base import BaseCommand

import os
import environ
import pymysql
import datetime
import html
import re
import boto3

from library import debug, inventory


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"
FEEDDIR = f"{FILEDIR}/feed/DecoratorsBestGS.xml"

PROCESS = "GS Feed"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "main" in options['functions']:
            total, skiped = processor.feed()
            if skiped < total * 0.2:
                processor.upload()
            else:
                debug.debug(
                    PROCESS, 2, f"Ignore uploading the feed because too many items {skiped}/{total} have been skiped")


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.s3 = boto3.client('s3', aws_access_key_id=env(
            'aws_access_key'), aws_secret_access_key=env('aws_secret_key'))
        self.bucket = 'decoratorsbestimages'

    def __del__(self):
        self.con.close()

    def fmt(self, s):
        if s != None and s != "":
            allowedCharaters = [" ", ",", ".", "'", "\"", "*",
                                "(", ")", "$", "&", ">", "-", "=", "+", "/", "!", "%", "^", "@", ":", ";", "{", "}", "[", "]", "?"]

            cleaned = [character for character in s if character.isalnum()
                       or character in allowedCharaters]

            return html.escape("".join(cleaned))
        else:
            return ""

    def feed(self):
        debug.debug(PROCESS, 0, f"Started running {PROCESS} processor.")

        if os.path.isfile(FEEDDIR):
            os.remove(FEEDDIR)

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
                AND M.Published=1
                AND M.Brand NOT IN ("Scalamandre")
                AND M.Name NOT IN ("Aviva Stanoff Wallpaper", "Missoni Wallpaper", "Patina Vie Wallpaper", "Kravet Pillow")
                AND P.Published = 1
                AND P.ManufacturerPartNumber <> ''
                AND P.Name NOT LIKE '%Borders'
                AND P.Name NOT LIKE '%Disney'
                AND PV.IsDefault=1
                AND PV.Published=1
                AND PV.Cost != 0
            """)

        products = csr.fetchall()
        csr.close()

        total = len(products)
        skiped = 0

        with open(FEEDDIR, 'w') as f:
            f.write('<?xml version="1.0"?>')
            f.write('<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">')
            f.write('<channel>')
            f.write('<title>DecoratorsBest</title>')
            f.write('<link>https://www.decoratorsbest.com</link>')
            f.write('<description>DecoratorsBest</description>')

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
                gtin = self.fmt(str(row[10]))
                mpn = self.fmt(str(row[11]))
                bodyHTML = str(row[12])
                cost = round(float(row[13]), 2)
                sprice = round(float(row[14]), 2)
                productID = str(row[15])
                pattern = self.fmt(str(row[16]))
                minQty = int(row[17])

                stock = inventory.inventory(sku)

                # Exceptions
                if stock["quantity"] < int(minQty):
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

                desc = self.fmt(bodyHTML.replace(
                    "<br />", "").replace("<br/>", " ").replace("<br>", " "))
                if desc == "":
                    desc = title

                brand = brand.replace("Covington", "DB By DecoratorsBest").replace(
                    "Premier Prints", "DB By DecoratorsBest").replace("Materialworks", "DB By DecoratorsBest")

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
                    priceRange = "0-10"

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

                f.write("<item>")
                f.write(f"<g:id>{sku}</g:id>")
                f.write(f"<g:item_group_id>{productID}</g:item_group_id>")
                f.write(f"<g:title>{title}</g:title>")
                f.write(f"<g:description>{desc}</g:description>")
                f.write(
                    f"<g:google_product_category>{category}</g:google_product_category>")
                f.write(
                    f"<g:link>https://www.decoratorsbest.com/products/{handle}</g:link>")
                f.write(f"<g:image_link>{imageURL}</g:image_link>")
                f.write(f"<g:availability>in stock</g:availability>")
                f.write(f"<g:gtin>{gtin}</g:gtin>")
                f.write(f"<g:price>{price} USD</g:price>")
                f.write(f"<g:brand>{brand}</g:brand>")
                f.write(f"<g:mpn>{mpn}</g:mpn>")
                f.write(f"<g:product_type>{productType}</g:product_type>")
                f.write(f"<g:condition>new</g:condition>")
                f.write(f"<g:color>{color}</g:color>")
                f.write(f"<g:pattern>{style}</g:pattern>")
                f.write(f"<g:shipping_weight>{weight} lb</g:shipping_weight>")
                f.write(f"<g:material>{material}</g:material>")
                f.write(f"<g:custom_label_0>{ptype}</g:custom_label_0>")
                f.write(f"<g:custom_label_1>{brand}</g:custom_label_1>")
                f.write(f"<g:custom_label_2>{priceRange}</g:custom_label_2>")
                f.write(f"<g:custom_label_3>{margin}%</g:custom_label_3>")

                debug.debug(
                    PROCESS, 0, f"{index}/{total}: Success for SKU {sku}. Skiped {skiped} SKUs")

            f.write('</channel>')
            f.write('</rss>')
            f.close()

        return (total, skiped)

    def upload(self):
        now = datetime.datetime.now()

        self.s3.upload_file(FEEDDIR, self.bucket, "DecoratorsBestGS.xml", ExtraArgs={
                            'ACL': 'public-read'})
        debug.debug(
            PROCESS, 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS.xml')

        self.s3.upload_file(
            FEEDDIR, self.bucket, "DecoratorsBestGS-V2.xml", ExtraArgs={'ACL': 'public-read'})
        debug.debug(
            PROCESS, 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS-V2.xml')

        self.s3.upload_file(
            FEEDDIR, self.bucket, f"DecoratorsBestGS-{now.year}-{now.month}-{now.day}.xml", ExtraArgs={'ACL': 'public-read'})
        debug.debug(
            PROCESS, 0, f"Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS-{now.year}-{now.month}-{now.day}.xml")