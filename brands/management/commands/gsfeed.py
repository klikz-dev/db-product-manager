from django.core.management.base import BaseCommand

import boto3
import time
import pymysql
import html
import os
import datetime
import requests
import json

from library import debug

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))
aws_access_key = env('aws_access_key')
aws_secret_key = env('aws_secret_key')


debug = debug.debug

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FEEDDIR = FILEDIR + '/files/feed/DecoratorsBestGS.xml'


class Command(BaseCommand):
    help = 'Generate Google Shopping Feed'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "main" in options['functions']:
            while True:
                self.feed()
                self.upload()
                time.sleep(36400)

    def formatter(self, s):
        if s != None and s != "":
            allowedCharaters = [" ", ",", ".", "'", "\"", "*",
                                "(", ")", "$", "&", "-", "=", "+", "/", "!", "%", "^", "@", ":", ";", "{", "}", "[", "]", "?"]

            cleaned = [character for character in s if character.isalnum()
                       or character in allowedCharaters]

            return html.escape("".join(cleaned))
        else:
            return ""

    def feed(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        if os.path.isfile(FEEDDIR):
            os.remove(FEEDDIR)
        f = open(FEEDDIR, "w+")

        csr.execute("""SELECT P.SKU, P.Title AS PName, P.Handle, PI.ImageURL, M.Name as Manufacturer, PV.Price * PV.MinimumQuantity AS Price, T.Name AS Type, 
                      (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=2 AND PT.SKU = P.SKU LIMIT 1) AS DesignStyle,
                      (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=3 AND PT.SKU = P.SKU LIMIT 1) AS Color,
                      PV.Weight,
                      PV.GTIN,
                      P.ManufacturerPartNumber,
                      P.BodyHTML,
                      PV.Cost,
                      PV.Price as SPrice,
                      P.ProductID,
                      P.Pattern
                      FROM Product P
                      LEFT JOIN ProductImage PI ON P.ProductID = PI.ProductID
                      LEFT JOIN ProductVariant PV ON P.ProductID = PV.ProductID
                      LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU
                      LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
                      LEFT JOIN Type T ON P.ProductTypeID = T.TypeID
                      WHERE PI.ImageIndex = 1
                      AND M.Brand NOT IN ("Fabricut", "Schumacher", "Scalamandre", "P/K Lifestyles", "Clarence House", "Jamie Young", "Noir", "Studio Zen", "Cyan", "Couture Lamps", "Global Views", "Olympus Minerals", "Kravet Decor", "Robert Allen", "Nature's Decoration", "Duralee")
                      AND M.Name NOT IN ("Aviva Stanoff Wallpaper", "Missoni Wallpaper", "Patina Vie Wallpaper")
                      AND PV.Cost != 0
                      AND P.Published = 1
                      AND P.ManufacturerPartNumber <> ''
                      AND PV.IsDefault=1
                      AND PV.Published=1
                      AND M.Published=1
                      AND P.Name NOT LIKE '%Borders'
                      AND P.SKU NOT IN (
                        SELECT P.SKU FROM Product P JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID 
                        WHERE (P.Name LIKE '%Disney%' AND M.Brand = 'York')
                      )""")

        f.write('<?xml version="1.0"?>')
        f.write('<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">')
        f.write('<channel>')
        f.write('<title>DecoratorsBest</title>')
        f.write('<link>https://www.decoratorsbest.com</link>')
        f.write('<description>DecoratorsBest</description>')

        count = 0
        for row in csr.fetchall():
            sku = row[0]

            # Check Stock
            # try:
            #     username = 'decoratorsbest'
            #     password = '5iXrwa8X!ZjRT'
            #     url = "https://legacy.decoratorsbestom.com/inventory.php?user={}&password={}&sku={}".format(
            #         username, password, sku)

            #     payload = {}
            #     headers = {}

            #     response = requests.request(
            #         "GET", url, headers=headers, data=payload)
            #     stockInfo = json.loads(response.text)
            #     print(stockInfo['Quantity'])

            #     if int(stockInfo['Quantity']) < 1:
            #         continue
            # except Exception as e:
            #     print(e)
            #     continue
            ############

            title = self.formatter("{} - {}".format(row[1].title(), sku))
            desc = self.formatter(row[12].replace(
                "<br/>", " ").replace("<br>", " "))
            if desc == "":
                desc = title
            handle = row[2]
            imageURL = row[3]

            brand = self.formatter(row[4])
            brand = brand.replace("Covington", "DB By DecoratorsBest").replace(
                "Premier Prints", "DB By DecoratorsBest").replace("Materialworks", "DB By DecoratorsBest")

            price = row[5]
            sprice = row[14]
            cost = row[13]
            productID = row[15]

            # Ignore Brewster Peel & Stick
            if brand == "A-Street Prints Wallpaper" or brand == "Brewster Home Fashions Wallpaper":
                if "Peel & Stick" in title:
                    continue
            ##############################

            # Skip word "get"
            getInText = False
            for word in title.split():
                if "get" == word.lower():
                    getInText = True
            for word in desc.split():
                if "get" == word.lower():
                    getInText = True
            
            if getInText:
                debug("GS", 1, "Ignore SKU: {}. Get in the text".format(sku))
                continue
            #################

            debug("GS", 0, "Writing -- ProductID: {}, SKU: {}, Brand: {}, Cost: {}".format(
                productID, sku, brand, price))

            priceForRange = price
            if priceForRange > 300:
                priceRange = "300+"
            elif priceForRange > 250:
                priceRange = "250-300"
            elif priceForRange > 200:
                priceRange = "200-250"
            elif priceForRange > 150:
                priceRange = "150-200"
            elif priceForRange > 100:
                priceRange = "100-150"
            elif priceForRange > 50:
                priceRange = "50-100"
            elif priceForRange > 25:
                priceRange = "25-50"
            elif priceForRange > 10:
                priceRange = "10-25"
            else:
                priceRange = "0-10"

            margin = (sprice - cost) / cost

            ptype = row[6]
            style = self.formatter(row[7])
            color = self.formatter(row[8])
            weight = row[9]
            gtin = row[10]
            mpn = row[11]
            if ptype == "Fabric":
                category = "Arts & Entertainment > Hobbies & Creative Arts > Arts & Crafts > Art & Crafting Materials > Textiles > Fabric"
                productType = "Home & Garden > Bed and Living Room > Home Fabric"
            elif ptype == "Wallpaper":
                category = "Home & Garden > Decor > Wallpaper"
                productType = "Home & Garden > Bed and Living Room > Home Wallpaper"
            elif ptype == "Pillow":
                category = "Home & Garden > Decor > Pillow"
                productType = "Home & Garden > Bed and Living Room > Home Pillow"
            elif ptype == "Trim":
                category = "Home & Garden > Decor > Trim"
                productType = "Home & Garden > Bed and Living Room > Home Trim"
            elif ptype == "Furniture":
                category = "Home & Garden > Decor > Furniture"
                productType = "Home & Garden > Bed and Living Room > Home Furniture"
            else:
                category = "Home & Garden > Decor"
                productType = ""
            count = count + 1

            category = self.formatter(category)
            productType = self.formatter(productType)

            # Material
            material = ""
            bodyHTML = str(row[12]).replace("<br />", "<br/>").replace("<br/>", "<br>")
            lines = bodyHTML.split("<br>")
            for line in lines:
                if "Material:" in line:
                    material = line.replace("Material:", "").strip()

            # Pattern
            if style == "":
                style = row[16]

            f.write('<item>')
            f.write('<g:id>{}</g:id>'.format(sku))
            f.write('<g:item_group_id>{}</g:item_group_id>'.format(productID))
            f.write('<g:title>{}</g:title>'.format(title))
            f.write('<g:description>{}</g:description>'.format(desc))
            if category != '':
                f.write(
                    '<g:google_product_category>{}</g:google_product_category>'.format(category))
            f.write(
                '<g:link>https://www.decoratorsbest.com/products/{}</g:link>'.format(handle))
            f.write('<g:image_link>{}</g:image_link>'.format(imageURL))
            f.write('<g:availability>in stock</g:availability>')

            test_list = ['FI72111', 'DL2968', 'TR4237MC', 'RRD1027N',
                         'TR4236MC', 'TR4235MC', 'TR4232MC', 'TR4234MC', 'RRD1027N']
            if gtin != None and gtin != '' and gtin != 0:
                if any(ext in sku for ext in test_list):
                    print("Invalid gtin SKU's")
                else:
                    f.write('<g:gtin>{}</g:gtin>'.format(gtin))
            f.write('<g:price>{} USD</g:price>'.format(price))
            f.write('<g:brand>{}</g:brand>'.format(brand))
            f.write('<g:mpn>{}</g:mpn>'.format(mpn))
            if productType != '':
                f.write('<g:product_type>{}</g:product_type>'.format(productType))
            f.write('<g:condition>new</g:condition>')
            f.write('<g:color>{}</g:color>'.format(color))
            f.write('<g:pattern>{}</g:pattern>'.format(style))
            f.write('<g:shipping_weight>{} lb</g:shipping_weight>'.format(weight))
            if material != '':
                f.write('<g:material>{}</g:material>'.format(material))
            f.write('<g:custom_label_0>{}</g:custom_label_0>'.format(ptype))
            f.write('<g:custom_label_1>{}</g:custom_label_1>'.format(brand))
            f.write('<g:custom_label_2>{}</g:custom_label_2>'.format(priceRange))
            f.write(
                '<g:custom_label_3>{}</g:custom_label_3>'.format("{}%".format(int(margin*100))))
            f.write('</item>\n')

        f.write('</channel>')
        f.write('</rss>')
        f.close()

        csr.close()
        con.close()

    def upload(self):
        now = datetime.datetime.now()
        fname = 'DecoratorsBestGS-' + \
            str(now.year)+'-'+str(now.month)+'-'+str(now.day)+'.xml'

        s3 = boto3.client('s3', aws_access_key_id=aws_access_key,
                          aws_secret_access_key=aws_secret_key)
        bucket_name = 'decoratorsbestimages'

        s3.upload_file(FEEDDIR,
                       bucket_name, "DecoratorsBestGS.xml", ExtraArgs={'ACL': 'public-read'})
        debug("GS", 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS.xml')

        s3.upload_file(FEEDDIR,
                       bucket_name, "DecoratorsBestGS-V2.xml", ExtraArgs={'ACL': 'public-read'})
        debug("GS", 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestGS-V2.xml')

        s3.upload_file(FEEDDIR,
                       bucket_name, fname, ExtraArgs={'ACL': 'public-read'})
        debug("GS", 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/' + fname)
