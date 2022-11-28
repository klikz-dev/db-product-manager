from django.core.management.base import BaseCommand

import os
import time
import pymysql

from library import debug, common

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

debug = debug.debug
backup = common.backup


colorDict = {
    'black': 'Black',
    'caviar': 'Black',
    'coal': 'Black',
    'ebony': 'Black',
    'jet': 'Black',
    'noir': 'Black',
    'onyx': 'Black',
    'pepper': 'Black',
    'adriatic': 'Blue',
    'atlantis': 'Blue',
    'blue': 'Blue',
    'capri': 'Blue',
    'cerulean': 'Blue',
    'cobalt': 'Blue',
    'denim': 'Blue',
    'lake': 'Blue',
    'lapis': 'Blue',
    'marine': 'Blue',
    'midnight': 'Blue',
    'nautical': 'Blue',
    'navy': 'Blue',
    'ocean': 'Blue',
    'periwinkle': 'Blue',
    'prussian': 'Blue',
    'royal': 'Blue',
    'sapphire': 'Blue',
    'aqua': 'Blue/Green',
    'azure': 'Blue/Green',
    'caribbean': 'Blue/Green',
    'mineral': 'Blue/Green',
    'peacock': 'Blue/Green',
    'pool': 'Blue/Green',
    'sea': 'Blue/Green',
    'spa': 'Blue/Green',
    'surf': 'Blue/Green',
    'turquoise': 'Blue/Green',
    'brandy': 'Brown',
    'brown': 'Brown',
    'chestnut': 'Brown',
    'chocolate': 'Brown',
    'cocoa': 'Brown',
    'cognac': 'Brown',
    'date': 'Brown',
    'espresso': 'Brown',
    'havana': 'Brown',
    'hazelnut': 'Brown',
    'java': 'Brown',
    'mahogany': 'Brown',
    'mink': 'Brown',
    'mushroom': 'Brown',
    'sable': 'Brown',
    'sandcastle': 'Brown',
    'truffle': 'Brown',
    'umber': 'Brown',
    'walnut': 'Brown',
    'almond': 'Beige',
    'beige': 'Beige',
    'bisque': 'Beige',
    'cream': 'Beige',
    'ivory': 'Beige',
    'linen': 'Beige',
    'natural': 'Beige',
    'parchment': 'Beige',
    'taupe': 'Beige',
    'vanilla': 'Beige',
    'wheat': 'Beige',
    'alpine': 'Green',
    'apple': 'Green',
    'avocado': 'Green',
    'basil': 'Green',
    'celadon': 'Green',
    'celery': 'Green',
    'emerald': 'Green',
    'fern': 'Green',
    'forest': 'Green',
    'grass': 'Green',
    'hunter': 'Green',
    'ivy': 'Green',
    'jade': 'Green',
    'kiwi': 'Green',
    'lime': 'Green',
    'mint': 'Green',
    'moss': 'Green',
    'pistachio': 'Green',
    'sage': 'Green',
    'turquois': 'Turquoise',
    'willow': 'Green',
    'graphite': 'Grey',
    'grey': 'Grey',
    'pebble': 'Grey',
    'pewter': 'Grey',
    'platinum': 'Grey',
    'powder': 'Grey',
    'quartz': 'Grey',
    'silver': 'Grey',
    'slate': 'Grey',
    'smoke': 'Grey',
    'steel': 'Grey',
    'stone': 'Grey',
    'vapor': 'Grey',
    'multi': 'Multi',
    'amber': 'Orange',
    'apricot': 'Orange',
    'bronze': 'Orange',
    'cinnamon': 'Orange',
    'clementine': 'Orange',
    'copper': 'Orange',
    'coral': 'Orange',
    'flame': 'Orange',
    'ginger': 'Orange',
    'mango': 'Orange',
    'melon': 'Orange',
    'orange': 'Orange',
    'papaya': 'Orange',
    'paprika': 'Orange',
    'peach': 'Orange',
    'salmon': 'Orange',
    'tangerine': 'Orange',
    'terracotta': 'Orange',
    'azalea': 'Pink',
    'begonia': 'Pink',
    'berry': 'Pink',
    'blossom': 'Pink',
    'blush': 'Pink',
    'hibiscus': 'Pink',
    'jasmine': 'Pink',
    'mimosa': 'Pink',
    'petal': 'Pink',
    'pink': 'Pink',
    'raspberry': 'Pink',
    'rose': 'Pink',
    'shell': 'Pink',
    'amethyst': 'Purple',
    'aubergine': 'Purple',
    'eggplant': 'Purple',
    'lavender': 'Purple',
    'mulberry': 'Purple',
    'orchid': 'Purple',
    'plum': 'Purple',
    'purple': 'Purple',
    'brick': 'Red',
    'burgundy': 'Red',
    'cayenne': 'Red',
    'chili': 'Red',
    'cinnabar': 'Red',
    'crimson': 'Red',
    'currant': 'Red',
    'lacquer': 'Red',
    'persimmon': 'Red',
    'pomegranate': 'Red',
    'poppy': 'Red',
    'red': 'Red',
    'ruby': 'Red',
    'scarlet': 'Red',
    'strawberry': 'Red',
    'adobe': 'Tan',
    'bamboo': 'Tan',
    'barley': 'Tan',
    'camel': 'Tan',
    'cashew': 'Tan',
    'desert': 'Tan',
    'khaki': 'Tan',
    'pecan': 'Tan',
    'raffia': 'Tan',
    'saddle': 'Tan',
    'sesame': 'Tan',
    'sisal': 'Tan',
    'tan': 'Tan',
    'toffee': 'Tan',
    'brass': 'Tan',
    'alabaster': 'White',
    'quartz': 'White',
    'snow': 'White',
    'white': 'White',
    'butter': 'Yellow',
    'canary': 'Yellow',
    'citrine': 'Yellow',
    'citrus': 'Yellow',
    'daffodil': 'Yellow',
    'gold': 'Yellow',
    'honey': 'Yellow',
    'lemon': 'Yellow',
    'mustard': 'Yellow',
    'sand': 'Yellow',
    'straw': 'Yellow',
    'sun': 'Yellow',
    'topaz': 'Yellow',
    'yellow': 'Yellow'
}

sizeDict = {
    '12" dia': '12" Diameter Sphere',
    '12" x 12"': '12" Diameter Sphere',
    '14" x 14"': '14" Square',
    '15.7" x 15.7"': '16" Square',
    '16" x 16"': '16" Square',
    '17.7" x 17.7"': '18" Square',
    '18" x 18"': '18" Square',
    '19" x 19"': '19" Square',
    '19.7" x 19.7"': '20" Square',
    '20" x 20"': '20" Square',
    '22" x 22"': '22" Square',
    '24" x 24"': '24" Square',

    'up to 1"': 'Up to 1"',
    '1" to 2"': '1" to 2"',
    '2" to 3"': '2" to 3"',
    '3" to 4"': '3" to 4"',
    '4" to 5"': '4" to 5"',
    '5" and more': '5" and More',
}


class Command(BaseCommand):
    help = 'Update Pending Tags'

    def handle(self, *args, **options):
        while True:
            self.editColor()
            self.editCategory()
            self.editStyle()
            self.editSubtype()
            self.editSize()

            debug("Shopify", 0, "Finished Process. Waiting for next run.")
            time.sleep(3600)

    def editColor(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM EditColor WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        con.commit()

        csr.execute("SELECT SKU, Color FROM EditColor WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            color = row[1].lower()
            for key in colorDict.keys():
                if key in color:
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq(colorDict[key])))
                    con.commit()

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditColor)
                                                            AND SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 3)""")
        con.commit()

        csr.execute("DELETE FROM EditColor")
        con.commit()

        csr.close()
        con.close()

    def editCategory(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM EditCategory WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        con.commit()

        categories = []
        csr.execute(
            "SELECT DISTINCT T.Name AS Tag FROM Tag T WHERE T.ParentTagID = 2")
        for row in csr.fetchall():
            categories.append(row[0].lower())

        csr.execute("SELECT SKU, Category FROM EditCategory WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            category = row[1].lower()
            for c in categories:
                if c in category:
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq(c)))
                    con.commit()

                    print("Added product tag: {} for product: {}".format(c, sku))

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditCategory)
                                                            AND SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 2)""")
        con.commit()

        csr.execute("DELETE FROM EditCategory")
        con.commit()

        csr.close()
        con.close()

    def editStyle(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("DELETE FROM EditStyle WHERE SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 1) OR SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        con.commit()

        styles = []
        csr.execute(
            "SELECT DISTINCT T.Name AS Tag FROM Tag T WHERE T.ParentTagID = 1")
        for row in csr.fetchall():
            styles.append(row[0].lower())

        csr.execute("SELECT SKU, Style FROM EditStyle WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            style = row[1].lower()
            for s in styles:
                if s in style:
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq(s)))
                    con.commit()

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditStyle)
                                                            AND SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 1)""")
        con.commit()

        csr.execute("DELETE FROM EditStyle")
        con.commit()

        csr.close()
        con.close()

    def editSubtype(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM EditSubtype WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        con.commit()

        subtypes = {}
        csr.execute(
            "SELECT DISTINCT T.Name AS Type, T.TypeID FROM Type T WHERE T.ParentTypeID != 0")
        for row in csr.fetchall():
            ptype = row[0].lower()
            if ptype[-2:] == 'es':
                if ptype == "accessories":
                    ptype = "accessory"
                elif ptype == "wall sconces":
                    ptype = "wall sconce"
                elif ptype == "rosettes":
                    ptype = "rosette"
                elif ptype == "bookcases":
                    ptype = "bookcase"
                elif ptype == "consoles":
                    ptype = "console"
                elif ptype == "coffee tables":
                    ptype = "coffee table"
                elif ptype == "tables":
                    ptype = "table"
                elif ptype == "vases":
                    ptype = "vase"
                else:
                    ptype = ptype[0:-2]
            elif ptype[-1:] == 's':
                ptype = ptype[0:-1]
            subtypes.update({ptype: row[1]})

        csr.execute("SELECT SKU, Subtype FROM EditSubtype WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            subtype = row[1].lower()
            for key, value in subtypes.items():
                if key in subtype:
                    csr.execute("CALL AddToProductSubtype ({}, {})".format(
                        common.sq(sku), value))
                    con.commit()

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditSubtype)
                                                            AND SKU IN (SELECT SKU FROM ProductSubtype PT JOIN Type T ON PT.SubtypeID = T.TypeID WHERE T.ParentTypeID != 0)""")
        con.commit()

        csr.execute("DELETE FROM EditSubtype")
        con.commit()

        csr.close()
        con.close()

    def editSize(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "DELETE FROM EditSize WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        con.commit()

        csr.execute("SELECT SKU, Size FROM EditSize WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            size = row[1].lower()
            isLumbar = True
            for key in sizeDict.keys():
                if key in size:
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq(sizeDict[key])))
                    con.commit()
                    isLumbar = False
            if isLumbar:
                csr.execute("CALL AddToProductTag ({}, {})".format(
                    common.sq(sku), common.sq('Lumbar')))
                con.commit()

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditSize)
                                                            AND SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 7)""")
        con.commit()

        csr.execute("DELETE FROM EditSize")
        con.commit()

        csr.close()
        con.close()
