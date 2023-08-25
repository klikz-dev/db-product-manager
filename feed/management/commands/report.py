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
        wallpaper_col_availability = []
        wallpaper_col_sku = []
        wallpaper_col_name = []
        wallpaper_col_width = []
        wallpaper_col_length = []
        wallpaper_col_height = []
        wallpaper_col_horizontal_repeat = []
        wallpaper_col_vertical_repeat = []
        wallpaper_col_image = []
        wallpaper_col_layout = []
        wallpaper_col_type = []
        wallpaper_col_link = []
        wallpaper_col_category = []
        wallpaper_col_style = []
        wallpaper_col_color = []
        wallpaper_col_subtype = []
        wallpaper_col_v1 = []
        wallpaper_col_v2 = []
        wallpaper_col_v3 = []
        wallpaper_col_v4 = []

        rug_col_availability = []
        rug_col_sku = []
        rug_col_name = []
        rug_col_width = []
        rug_col_length = []
        rug_col_height = []
        rug_col_horizontal_repeat = []
        rug_col_vertical_repeat = []
        rug_col_image = []
        rug_col_layout = []
        rug_col_type = []
        rug_col_link = []
        rug_col_category = []
        rug_col_style = []
        rug_col_color = []
        rug_col_subtype = []
        rug_col_v1 = []
        rug_col_v2 = []
        rug_col_v3 = []
        rug_col_v4 = []

        wallart_col_availability = []
        wallart_col_sku = []
        wallart_col_name = []
        wallart_col_width = []
        wallart_col_length = []
        wallart_col_height = []
        wallart_col_horizontal_repeat = []
        wallart_col_vertical_repeat = []
        wallart_col_image = []
        wallart_col_layout = []
        wallart_col_type = []
        wallart_col_link = []
        wallart_col_category = []
        wallart_col_style = []
        wallart_col_color = []
        wallart_col_subtype = []
        wallart_col_v1 = []
        wallart_col_v2 = []
        wallart_col_v3 = []
        wallart_col_v4 = []

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

        self.csr.execute(f"""
            SELECT P.ProductID, P.SKU, P.Handle, P.Title, P.BodyHTML, P.ProductTypeId, M.Brand, PI.imageURL, T.Name
            FROM ProductImage PI
            LEFT JOIN Product P ON PI.ProductID = P.ProductID 
            LEFT JOIN Type T ON P.ProductTypeId = T.TypeId
            LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU 
            LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID 
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
            type = row[8]

            # JL Rug images doesn't look good
            # if brand == "Jaipur Living":
            #     continue

            # Type
            types = [
                "Wallpaper",
                "Rug",
                "Wall Art",
                "Wall Mirrors",
                "Wall Hangings",
                "Wall Accent",
                "Mirrors"
            ]

            if type not in types:
                continue

            if type == "Rug":
                type = "Area Rug"
            elif "Mirror" in type or "Wall " in type:
                type = "Wall Art"

            if "Rug Pad" in title:
                continue

            # Collection, Width, Length, and Layout
            width = ""
            length = ""
            height = ""
            depth = ""
            rollLength = ""
            size = ""
            dim = ""
            hr = ""
            vr = ""
            repeat = ""
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
                if "Size:" in line:
                    size = line.replace("Size:", "").strip()
                if "Dimension:" in line:
                    dim = line.replace("Dimension:", "").replace(
                        "Roll", "").strip()
                if "Horizontal Repeat:" in line:
                    hr = line.replace("Horizontal Repeat:", "").strip()
                    layout = "Repeat"
                if "Vertical Repeat:" in line:
                    vr = line.replace("Vertical Repeat:", "").strip()
                    layout = "Repeat"
                if "Repeat:" in line and "Horizontal" not in line and "Vertical" not in line:
                    repeat = line.replace("Repeat:", "").strip()
                    layout = "Repeat"
                if "Match:" in line:
                    match = line.replace("Match:", "").strip()
                    layout = ", ".join((layout, match))

            x = width.replace("Each Pre-Cut Roll",
                              "").replace("Inches.", "in").strip()
            y = length or height
            z = ""

            if type == "Area Rug" or type == "Wall Art":
                if depth:
                    y = length or height
                    z = depth
                else:
                    y = length
                    z = height

                if z and not y:
                    y = z
                    z = ""

            if not y and rollLength:
                y = round(float(rollLength.replace(
                    "yards", "").replace("yds", "").strip()) * 36, 2)
                y = f"{y} in"

            if "ft" in y:
                y = round(float(y.replace("ft", "").strip()) * 12, 2)
                y = f"{y} in"

            if not x and "x" in size:
                x = size.split("x")[0].replace(
                    "sold as a single", "").replace("wide", "").strip()

            if not x and dim:
                if "/" in dim:
                    dim = dim.split("/")[0]
                if "x" in dim:
                    x = dim.split("x")[0].strip()
                    y = dim.split("x")[1].strip()
                    if "yards" in y or "yds" in y:
                        y = round(float(y.replace("yards", "").replace(
                            "yds", "").strip()) * 36, 2)
                        y = f"{y} in"

            # Repeat
            if "/" in repeat and "in" in repeat:
                vr = repeat.split("/")[0].replace("in.", "in").strip()
                if "x" in vr:
                    vr = round(float(repeat.split("x")[0].replace(
                        "cm", "").replace("W", "").replace("m", "").strip()) / 2.54, 2)
                    vr = f"{vr} in"
                hr = x

            x = x.replace('"', ' in').replace("W", "").replace(
                "H", "").replace(",", "")
            y = y.replace('"', ' in').replace("W", "").replace(
                "H", "").replace(",", "")
            hr = hr.replace('"', ' in')
            vr = vr.replace('"', ' in')

            if x == "0 in":
                x = ""
            if y == "0 in":
                y = ""
            if vr == "0 in":
                vr = ""
            if hr == "0 in":
                hr = ""

            if not x or not y:
                continue

            # Variants
            v1 = ""
            v2 = ""
            v3 = ""
            v4 = ""

            self.csr.execute(f"""
                SELECT PV.Name, PV.VariantId, PV.IsDefault
                FROM ProductVariant PV
                WHERE PV.ProductId='{productId}'
            """)
            rows = self.csr.fetchall()

            for row in rows:
                if row[2] == 1:
                    v1 = row[1]
                elif "Trade - " in row[0]:
                    v2 = row[1]
                elif "Free Sample - " in row[0]:
                    v4 = row[1]
                elif "Sample - " in row[0]:
                    v3 = row[1]

            v1 = productId
            v2 = productId
            v3 = productId
            v4 = productId

            # Filters
            categories = []
            styles = []
            colors = []
            subtypes = []

            self.csr.execute(f"""
                SELECT T.Name, T.Description, T.ParentTagId
                FROM ProductTag PT
                LEFT JOIN Tag T ON PT.TagId = T.TagId
                WHERE PT.SKU='{sku}'
            """)
            rows = self.csr.fetchall()

            for row in rows:
                if row[2] == 0:
                    continue

                if row[1] == "Category":
                    categories.append(row[0])

                if row[1] == "Style":
                    styles.append(row[0])

                if row[1] == "Color":
                    colors.append(row[0])

            self.csr.execute(f"""
                SELECT T.Name, T.ParentTypeId
                FROM ProductSubtype PT
                LEFT JOIN Type T ON PT.SubTypeId = T.TypeId
                WHERE PT.SKU='{sku}'
            """)
            rows = self.csr.fetchall()

            for row in rows:
                if row[1] != 0:
                    subtypes.append(row[0])

            categories = ", ".join(categories)
            styles = ", ".join(styles)
            colors = ", ".join(colors)
            subtypes = ", ".join(subtypes)

            debug.debug(
                PROCESS, 0, f"Wallpaper: {wallpaperAdded}, Area Rug: {rugAdded}, Wall Art: {wallArtAdded} -- SKU: {sku}, Name: {title}")

            # Counting
            if type == "Wallpaper":
                wallpaperAdded = wallpaperAdded + 1
                wallpaper_col_availability.append('Yes')
                wallpaper_col_sku.append(sku)
                wallpaper_col_name.append(title)
                wallpaper_col_width.append(x)
                wallpaper_col_length.append(y)
                wallpaper_col_height.append(z)
                wallpaper_col_horizontal_repeat.append(hr)
                wallpaper_col_vertical_repeat.append(vr)
                wallpaper_col_image.append(imageURL)
                wallpaper_col_layout.append(layout)
                wallpaper_col_type.append(type)
                wallpaper_col_link.append(
                    'https://www.decoratorsbest.com/products/{}'.format(handle))
                wallpaper_col_category.append(categories)
                wallpaper_col_style.append(styles)
                wallpaper_col_color.append(colors)
                wallpaper_col_subtype.append(subtypes)
                wallpaper_col_v1.append(v1)
                wallpaper_col_v2.append(v2)
                wallpaper_col_v3.append(v3)
                wallpaper_col_v4.append(v4)

            if type == "Area Rug":
                rugAdded = rugAdded + 1
                rug_col_availability.append('Yes')
                rug_col_sku.append(sku)
                rug_col_name.append(title)
                rug_col_width.append(x)
                rug_col_length.append(y)
                rug_col_height.append(z)
                rug_col_horizontal_repeat.append(hr)
                rug_col_vertical_repeat.append(vr)
                rug_col_image.append(imageURL)
                rug_col_layout.append(layout)
                rug_col_type.append(type)
                rug_col_link.append(
                    'https://www.decoratorsbest.com/products/{}'.format(handle))
                rug_col_category.append(categories)
                rug_col_style.append(styles)
                rug_col_color.append(colors)
                rug_col_subtype.append(subtypes)
                rug_col_v1.append(v1)
                rug_col_v2.append(v2)
                rug_col_v3.append(v3)
                rug_col_v4.append(v4)

            if type == "Wall Art":
                wallArtAdded = wallArtAdded + 1
                wallart_col_availability.append('Yes')
                wallart_col_sku.append(sku)
                wallart_col_name.append(title)
                wallart_col_width.append(x)
                wallart_col_length.append(y)
                wallart_col_height.append(z)
                wallart_col_horizontal_repeat.append(hr)
                wallart_col_vertical_repeat.append(vr)
                wallart_col_image.append(imageURL)
                wallart_col_layout.append(layout)
                wallart_col_type.append(type)
                wallart_col_link.append(
                    'https://www.decoratorsbest.com/products/{}'.format(handle))
                wallart_col_category.append(categories)
                wallart_col_style.append(styles)
                wallart_col_color.append(colors)
                wallart_col_subtype.append(subtypes)
                wallart_col_v1.append(v1)
                wallart_col_v2.append(v2)
                wallart_col_v3.append(v3)
                wallart_col_v4.append(v4)

        col_availability = wallpaper_col_availability + \
            rug_col_availability + wallart_col_availability
        col_sku = wallpaper_col_sku + rug_col_sku + wallart_col_sku
        col_name = wallpaper_col_name + rug_col_name + wallart_col_name
        col_width = wallpaper_col_width + rug_col_width + wallart_col_width
        col_length = wallpaper_col_length + rug_col_length + wallart_col_length
        col_height = wallpaper_col_height + rug_col_height + wallart_col_height
        col_horizontal_repeat = wallpaper_col_horizontal_repeat + \
            rug_col_horizontal_repeat + wallart_col_horizontal_repeat
        col_vertical_repeat = wallpaper_col_vertical_repeat + \
            rug_col_vertical_repeat + wallart_col_vertical_repeat
        col_image = wallpaper_col_image + rug_col_image + wallart_col_image
        col_layout = wallpaper_col_layout + rug_col_layout + wallart_col_layout
        col_type = wallpaper_col_type + rug_col_type + wallart_col_type
        col_link = wallpaper_col_link + rug_col_link + wallart_col_link
        col_category = wallpaper_col_category + rug_col_category + wallart_col_category
        col_style = wallpaper_col_style + rug_col_style + wallart_col_style
        col_color = wallpaper_col_color + rug_col_color + wallart_col_color
        col_subtype = wallpaper_col_subtype + rug_col_subtype + wallart_col_subtype
        col_v1 = wallpaper_col_v1 + rug_col_v1 + wallart_col_v1
        col_v2 = wallpaper_col_v2 + rug_col_v2 + wallart_col_v2
        col_v3 = wallpaper_col_v3 + rug_col_v3 + wallart_col_v3
        col_v4 = wallpaper_col_v4 + rug_col_v4 + wallart_col_v4

        data1 = {
            'Availability': col_availability[0:27999],
            'SKU': col_sku[0:27999],
            'Name': col_name[0:27999],
            'Width': col_width[0:27999],
            'Length': col_length[0:27999],
            'Thickness': col_height[0:27999],
            'Horizontal Repeat': col_horizontal_repeat[0:27999],
            'Vertical Repeat': col_vertical_repeat[0:27999],
            'Image File Path': col_image[0:27999],
            'Tile / Plank Layout': col_layout[0:27999],
            'Product Subtype': col_type[0:27999],
            'Link': col_link[0:27999],
            'Category (Filter)': col_category[0:27999],
            'Style (Filter)': col_style[0:27999],
            'Color (Filter)': col_color[0:27999],
            'Subtype (Filter)': col_subtype[0:27999],
            'Add to Cart': col_v1[0:27999],
            'Add to Cart (Trade)': col_v2[0:27999],
            'Order Sample': col_v3[0:27999],
            'Order Sample (Trade)': col_v4[0:27999],
        }
        df1 = pandas.DataFrame(data1)
        df1.to_excel(f"{FILEDIR}/roomvo-1.xlsx", index=False)

        data2 = {
            'Availability': col_availability[28000:],
            'SKU': col_sku[28000:],
            'Name': col_name[28000:],
            'Width': col_width[28000:],
            'Length': col_length[28000:],
            'Thickness': col_height[28000:],
            'Horizontal Repeat': col_horizontal_repeat[28000:],
            'Vertical Repeat': col_vertical_repeat[28000:],
            'Image File Path': col_image[28000:],
            'Tile / Plank Layout': col_layout[28000:],
            'Product Subtype': col_type[28000:],
            'Link': col_link[28000:],
            'Category (Filter)': col_category[28000:],
            'Style (Filter)': col_style[28000:],
            'Color (Filter)': col_color[28000:],
            'Subtype (Filter)': col_subtype[28000:],
            'Add to Cart': col_v1[28000:],
            'Add to Cart (Trade)': col_v2[28000:],
            'Order Sample': col_v3[28000:],
            'Order Sample (Trade)': col_v4[28000:],
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
