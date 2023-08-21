from django.core.management.base import BaseCommand

import os
import environ
import pymysql
import csv
import pandas

from library import debug
from shopify.models import Variant, Customer, Address
from mysql.models import ProductTag, Tag, ProductSubtype, Type

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

PROCESS = "Report"


class Command(BaseCommand):
    help = "Build Reports"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "roomvo" in options['functions']:
            processor = Processor()
            processor.roomvo()

        if "customers" in options['functions']:
            processor = Processor()
            processor.customers()


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.csr = self.con.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.csr.close()
        self.con.close()

    def roomvo(self):
        col_availability = []
        col_sku = []
        col_name = []
        col_width = []
        col_length = []
        col_height = []
        col_horizontal_repeat = []
        col_vertical_repeat = []
        col_image = []
        col_layout = []
        col_type = []
        col_link = []
        col_category = []
        col_style = []
        col_color = []
        col_subtype = []
        col_v1 = []
        col_v2 = []
        col_v3 = []
        col_v4 = []

        self.csr = self.con.cursor()
        self.csr.execute(f"""
            SELECT P.ProductID, P.SKU, P.Handle, P.Title, P.BodyHTML, P.ProductTypeId, M.Brand, PI.imageURL
            FROM ProductImage PI 
            JOIN Product P ON PI.ProductID = P.ProductID 
            JOIN ProductManufacturer PM ON P.SKU = PM.SKU 
            JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID 
            WHERE PI.ImageIndex = 20 AND P.Published = 1
        """)
        rows = self.csr.fetchall()

        wallpaperAdded = 0
        rugAdded = 0
        wallArtAdded = 0

        for row in rows:
            productId = row[0]
            sku = row[1]
            handle = row[2]
            title = row[3]
            bodyHTML = row[4]
            productTypeId = row[5]
            brand = row[6]
            imageURL = row[7]

            # JL Rug images doesn't look good
            if brand == "Jaipur Living":
                continue

            # Type
            if productTypeId == 2:
                type = "Wallpaper"
            elif productTypeId == 4:
                type = "Area Rug"
            elif productTypeId == 41:
                type = "Wall Art"
            else:
                continue

            # if (type == "Wallpaper" and wallpaperAdded > 9999) or (type == "Area Rug" and rugAdded > 9999) or (type == "Wall Art" and wallArtAdded > 9999):
            #     continue

            if "Rug Pad" in title:
                continue

            # Collection, Width, Length, and Layout
            width = ""
            length = ""
            height = ""
            depth = ""
            rollLength = ""
            hr = ""
            vr = ""
            layout = ""
            body = bodyHTML.replace(
                "<br/>", "<br>").replace("<br />", "<br>").split("<br>")
            for line in body:
                if "Width:" in line:
                    width = line.replace("Width:", "").strip()
                if "Length:" in line and "Roll Length:" not in line:
                    length = line.replace("Length:", "").strip()
                if "Height:" in line:
                    height = line.replace("Height:", "").strip()
                if "Depth:" in line:
                    depth = line.replace("Depth:", "").strip()
                if "Roll Length:" in line:
                    rollLength = line.replace("Roll Length:", "").strip()
                if "Horizontal Repeat:" in line:
                    hr = line.replace("Horizontal Repeat:", "").strip()
                if "Vertical Repeat:" in line:
                    vr = line.replace("Vertical Repeat:", "").strip()
                if "Repeat:" in line or "Horizontal Repeat:" in line or "Vertical Repeat:" in line:
                    layout = "Repeat"
                if "Match:" in line:
                    match = line.replace("Match:", "").strip()
                    layout = ", ".join((layout, match))

            x = width
            y = ""
            z = ""

            if type == "Area Rug" or type == "Wall Art":
                if depth:
                    z = depth
                    y = height or length
                else:
                    z = height
                    y = length

                if type == "Wall Art" and not z:
                    continue
            else:
                y = height or length

            if not y:
                y = rollLength

            # Variants
            v1 = ""
            v2 = ""
            v3 = ""
            v4 = ""
            variants = Variant.objects.filter(productId=productId)

            for variant in variants:
                if variant.isDefault == True:
                    v1 = variant.variantId
                elif "Trade - " in variant.name:
                    v2 = variant.variantId
                elif "Free Sample - " in variant.name:
                    v4 = variant.variantId
                elif "Sample - " in variant.name:
                    v3 = variant.variantId

            # Filters
            categories = []
            styles = []
            colors = []
            subtypes = []

            productTags = ProductTag.objects.filter(sku=sku)
            for productTag in productTags:
                try:
                    tag = Tag.objects.get(tagId=productTag.tagId)
                except Tag.DoesNotExist:
                    continue
                if tag.parentTagId == 0:
                    continue

                if tag.description == "Category":
                    categories.append(tag.name)

                if tag.description == "Style":
                    styles.append(tag.name)

                if tag.description == "Color":
                    colors.append(tag.name)

            productSubtypes = ProductSubtype.objects.filter(sku=sku)
            for productSubtype in productSubtypes:
                try:
                    subtype = Type.objects.get(
                        typeId=productSubtype.subtypeId)
                except Type.DoesNotExist:
                    continue
                if subtype.parentTypeId == 0:
                    continue

                subtypes.append(subtype.name)

            categories = ", ".join(categories)
            styles = ", ".join(styles)
            colors = ", ".join(colors)
            subtypes = ", ".join(subtypes)

            debug.debug(
                PROCESS, 0, f"Wallpaper: {wallpaperAdded}, Rug: {rugAdded}, Wall Art: {wallArtAdded} -- SKU: {sku}, Name: {title}")

            # Write Row
            if not x and not y:
                continue

            col_availability.append('Yes')
            col_sku.append(sku)
            col_name.append(title)
            col_width.append(x)
            col_length.append(y)
            col_height.append(z)
            col_horizontal_repeat.append(hr)
            col_vertical_repeat.append(vr)
            col_image.append(imageURL)
            col_layout.append(layout)
            col_type.append(type)
            col_link.append(
                'https://www.decoratorsbest.com/products/{}'.format(handle))
            col_category.append(categories)
            col_style.append(styles)
            col_color.append(colors)
            col_subtype.append(subtypes)
            col_v1.append(v1)
            col_v2.append(v2)
            col_v3.append(v3)
            col_v4.append(v4)

            # Counting
            if type == "Wallpaper":
                wallpaperAdded = wallpaperAdded + 1

            if type == "Area Rug":
                rugAdded = rugAdded + 1

            if type == "Wall Art":
                wallArtAdded = wallArtAdded + 1

        data1 = {
            'Availability': col_availability[0:19999],
            'SKU': col_sku[0:19999],
            'Name': col_name[0:19999],
            'Width': col_width[0:19999],
            'Length': col_length[0:19999],
            'Thickness': col_height[0:19999],
            'Horizontal Repeat': col_horizontal_repeat[0:19999],
            'Vertical Repeat': col_vertical_repeat[0:19999],
            'Image File Path': col_image[0:19999],
            'Tile / Plank Layout': col_layout[0:19999],
            'Product Subtype': col_type[0:19999],
            'Link': col_link[0:19999],
            'Category (Filter)': col_category[0:19999],
            'Style (Filter)': col_style[0:19999],
            'Color (Filter)': col_color[0:19999],
            'Subtype (Filter)': col_subtype[0:19999],
            'Add to Cart': col_v1[0:19999],
            'Add to Cart (Trade)': col_v2[0:19999],
            'Order Sample': col_v3[0:19999],
            'Order Sample (Trade)': col_v4[0:19999],
        }
        df1 = pandas.DataFrame(data1)
        df1.to_excel(f"{FILEDIR}/roomvo-1.xlsx", index=False)

        data2 = {
            'Availability': col_availability[20000:],
            'SKU': col_sku[20000:],
            'Name': col_name[20000:],
            'Width': col_width[20000:],
            'Length': col_length[20000:],
            'Thickness': col_height[20000:],
            'Horizontal Repeat': col_horizontal_repeat[20000:],
            'Vertical Repeat': col_vertical_repeat[20000:],
            'Image File Path': col_image[20000:],
            'Tile / Plank Layout': col_layout[20000:],
            'Product Subtype': col_type[20000:],
            'Link': col_link[20000:],
            'Category (Filter)': col_category[20000:],
            'Style (Filter)': col_style[20000:],
            'Color (Filter)': col_color[20000:],
            'Subtype (Filter)': col_subtype[20000:],
            'Add to Cart': col_v1[20000:],
            'Add to Cart (Trade)': col_v2[20000:],
            'Order Sample': col_v3[20000:],
            'Order Sample (Trade)': col_v4[20000:],
        }
        df2 = pandas.DataFrame(data2)
        df2.to_excel(f"{FILEDIR}/roomvo-2.xlsx", index=False)

    def customers(self):
        with open(FILEDIR + 'customers.csv', 'w', newline='') as customersFile:
            csvWriter = csv.DictWriter(customersFile, fieldnames=[
                'email',
                'fname',
                'lname',
                'phone',
                'address1',
                'address2',
                'company',
                'city',
                'state',
                'zip',
                'country',
                'total',
            ])

            csvWriter.writerow({
                'email': 'Email',
                'fname': 'First Name',
                'lname': 'Last Name',
                'phone': 'Phone Number',
                'address1': 'Address 1',
                'address2': 'Address 2',
                'company': 'Company',
                'city': 'City',
                'state': 'State',
                'zip': 'Zip Code',
                'country': 'Country',
                'total': 'Total Spent',
            })

            customers = Customer.objects.all()

            total = len(customers)
            for index, customer in enumerate(customers):
                try:
                    address = Address.objects.get(
                        addressId=customer.defaultAddressId)
                except Address.DoesNotExist:
                    continue

                csvWriter.writerow({
                    'email': customer.email,
                    'fname': customer.firstName,
                    'lname': customer.lastName,
                    'phone': customer.phone,
                    'address1': address.address1,
                    'address2': address.address2,
                    'company': address.company,
                    'city': address.city,
                    'state': address.state,
                    'zip': address.zip,
                    'country': address.country,
                    'total': customer.totalSpent,
                })

                debug.debug(PROCESS, 0, f"{index+1}/{total}: {customer.email}")
