import urllib
import json
import os
import requests
import boto3
import pymysql
from datetime import timedelta
from datetime import datetime

from library import debug

import environ
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))
aws_access_key = env('aws_access_key')
aws_secret_key = env('aws_secret_key')

api_version = env('shopify_api_version')

debug = debug.debug


class ProductData:
    def __init__(self, con, sku):
        self.sku = sku.upper()
        self.con = con
        self.csr = self.con.cursor()

        self.csr.execute("""SELECT P.ProductID, P.ManufacturerPartNumber, P.BodyHTML, P.Title, P.Description, P.Published, PV.Price, T.Name AS ProductType, P.Pattern, P.Color, P.Collection, M.Name AS Manufacturer, P.IsOutlet, P.CreatedAt, M.Brand AS Brand
                    FROM Product P LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID LEFT JOIN Type T ON P.ProductTypeID = T.TypeID LEFT JOIN ProductVariant PV ON P.SKU = PV.SKU
                    WHERE PV.IsDefault = 1 AND P.SKU = {}""".format(sq(sku)))
        product = self.csr.fetchone()
        self.productID = product[0]
        self.mpn = product[1].upper()
        self.body = product[2]

        self.title = product[3].title()
        self.description = product[4]
        self.published = product[5]
        self.price = product[6]
        self.ptype = product[7]
        self.pattern = product[8]
        self.color = product[9]
        self.collection = product[10]
        self.manufacturer = product[11]
        self.isOutlet = product[12]
        self.createdAt = product[13]
        self.brand = product[14]

    def ProductTag(self):
        price = self.price
        createdAt = self.createdAt
        isOutlet = self.isOutlet

        tags = []
        self.csr.execute(
            "SELECT T.Name, T.Description FROM Tag T JOIN ProductTag PT ON T.TagID = PT.TagID JOIN Product P ON PT.SKU = P.SKU WHERE P.SKU = {}".format(sq(self.sku)))
        for tag in self.csr.fetchall():
            tagName = tag[0]
            tagDesc = tag[1]
            tags.append("{}:{}".format(tagDesc, tagName))
            if tagName == 'Animals':
                tags.append("{}:{}".format('Subcategory', 'Animal'))
            elif tagDesc == 'Category':  # Check with bk on what all she wants in subcats
                excludeTags = ['abaca', 'arrowroot', 'bamboo', 'brick', 'cat', 'cheetah', 'coral', 'distressed', 'dog', 'elephant', 'hemp', 'horizontal stripe', 'horse', 'large florals', 'leopard', 'nautical',
                               'outdoor florals', 'rushcloth', 'sheer florals', 'sisal', 'skins', 'small florals', 'sports', 'stone', 'textile', 'ticking stripe', 'tye dye', 'toiles', 'trompe l\'oeil', 'tropical florals', 'zebra']

                if tagName.lower() not in excludeTags:
                    tags.append("{}:{}".format('Subcategory', tagName))

        if 0 <= price and price < 25:
            tags.append("Price:$0 - $25")
            tags.append("Price:$0 - $50")
        elif 25 <= price and price < 50:
            tags.append("Price:$25 - $50")
            tags.append("Price:$0 - $50")
        elif 50 <= price and price < 100:
            tags.append("Price:$50 - $100")
        elif 100 <= price and price < 200:
            tags.append("Price:$100 - $200")
        elif 200 <= price and price < 300:
            tags.append("Price:$200 - $300")
        elif 300 <= price and price < 400:
            tags.append("Price:$300 - $400")
        elif 400 <= price and price < 500:
            tags.append("Price:$400 - $500")
        elif 500 <= price:
            tags.append("Price:$500 & Up")

        # New Tag
        if createdAt > datetime.today() - timedelta(days=60):
            tags.append("Group:New")

        # Outlet Tag
        if isOutlet == 1:
            tags.append("Group:Outlet")

        # Add Product Type to Tags
        tags.append("Type:{}".format(self.ptype))

        # Manufacturer Tag
        tags.append("Brand:{}".format(self.brand))

        # Add Subtype To Tags
        self.csr.execute("SELECT T.Name, T.ParentTypeID, PT.ParentTypeID FROM ProductSubtype PS JOIN Type T ON PS.SubtypeID = T.TypeID LEFT JOIN Type PT ON T.ParentTypeID = PT.TypeID WHERE PS.SKU = {} AND T.Published = 1 AND PT.Published = 1 ORDER BY T.TypeID DESC".format(sq(self.sku)))
        subtypes = self.csr.fetchall()
        sts = []
        for subtype in subtypes:
            if subtype[1] == None or subtype[1] == 0 or subtype[0] in sts:
                continue
            path = subtype[0]
            parentTypeID = subtype[1]
            ppTypeID = subtype[2]
            while ppTypeID != 0:
                self.csr.execute(
                    "SELECT T.Name, T.ParentTypeID, PT.ParentTypeID FROM Type T LEFT JOIN Type PT ON T.ParentTypeID = PT.TypeID WHERE T.TypeID = {}".format(parentTypeID))
                sttmp = self.csr.fetchone()
                path = "{}>{}".format(sttmp[0], path)
                sts.append(sttmp[0])
                parentTypeID = sttmp[1]
                ppTypeID = sttmp[2]
            tags.append("Subtype:{}".format(path))

        # Subcategory code starts
        self.csr.execute(
            "SELECT Subcat, Val FROM ProductSubcategory where SKU = {} ".format(sq(self.sku)))
        subcategories = self.csr.fetchall()
        sts = []
        for subcat in subcategories:
            tag = 'Subcategory:'+subcat[0]
            if subcat[0] != subcat[1]:
                scatval = subcat[1]
                if scatval == 'Zebre':
                    scatval = 'Zebra'
                if scatval == 'Tigre':
                    scatval = 'Tiger'
                tag = tag + '>' + scatval

            if self.sku.find('SCALA') != -1 and subcat[0] == 'Animal':
                m = 'do nothing'
            elif subcat[0] == 'Asian':
                m = 'do nothing'
            elif self.sku.find('PJ') != -1 and (subcat[0] == 'Animal' or subcat[0] == 'Birds'):
                m = 'do nothing'
            else:
                tags.append(tag)
        # Subcategory code ends

        # Hipliee tag i.e. keep tags added by other vendors
        s = requests.Session()
        api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
            env('shopify_newproduct_key'), env('shopify_newproduct_password'))
        r = s.get(
            api_url+"/admin/api/{}/products/{}.json".format(api_version, self.productID))

        exProdMeta = json.loads(r.text)
        try:
            curtags = exProdMeta['product']['tags']
        except:
            curtags = ''

        _spt = curtags.split(',')
        for k in range(0, len(_spt)):
            if _spt[k].strip().find('p_color:') == 0 or _spt[k].strip().find('Designer:') == 0:
                tags.append(_spt[k].strip())
        # Hiplee ends

        origin = tags[:]
        for tag in origin:
            kv = tag.split(":")
            value = kv[1]
            if '>' in value:
                sts = value.split('>')
                for st in sts:
                    tags.append(st)
            else:
                tags.append(value)

        return tags

    def ProductMetafield(self):
        mpn = self.mpn
        title = self.title
        description = self.description
        collection = self.collection

        # Product Metafields
        pMeta = [
            {"key": "description_tag", "value": description,
                "namespace": "global", "value_type": "string"},
            {"key": "title_tag", "value": "{} | DecoratorsBest".format(
                title), "namespace": "global", "value_type": "string"},
            {"key": "ManufacturerPartNumber", "value": mpn,
                "namespace": "inventory", "value_type": "string"}
        ]
        if collection != None and collection != "":
            pMeta.append({"key": "collections", "value": collection,
                         "namespace": "product", "value_type": "string"})

        return pMeta

    def ProductVariants(self):
        variants = []
        self.csr.execute("SELECT IsDefault, Name, Price, Weight, Cost, Pricing, MinimumQuantity, RestrictedQuantities, GTIN, Published FROM ProductVariant WHERE SKU = {} ORDER BY Position ASC".format(sq(self.sku)))
        for v in self.csr.fetchall():
            isDefault = v[0]
            vName = v[1].title()
            price = float(v[2])
            weight = float(v[3])
            cost = float(v[4])
            pricing = v[5]
            minimum = v[6]
            increment = v[7]
            gtin = v[8]
            vPublished = v[9]
            mpn = self.mpn
            color = self.color
            pattern = self.pattern

            # Variant MetaFields
            vMeta = [
                {"key": "Cost", "value": cost,
                    "namespace": "inventory", "value_type": "string"},
                {"key": "ManufacturerPartNumber", "value": mpn,
                    "namespace": "inventory", "value_type": "string"},
                {"key": "UnitOfMeasurement", "value": pricing,
                    "namespace": "inventory", "value_type": "string"},
                {"key": "Published", "value": vPublished,
                    "namespace": "inventory", "value_type": "string"}
            ]
            if "Sample - " not in vName:
                if minimum != None and minimum != 1:
                    vMeta.append({"key": "MinimumQuantity", "value": minimum,
                                 "namespace": "inventory", "value_type": "string"})
                if increment != None and increment != "":
                    vMeta.append({"key": "RestrictedQuantities", "value": increment,
                                 "namespace": "inventory", "value_type": "string"})
            else:
                vMeta.append({"key": "RestrictedQuantities", "value": "1",
                             "namespace": "inventory", "value_type": "string"})

            variant = {
                "title": vName,
                "price": price,
                "sku": self.sku,
                "option1": vName,
                "option2": pattern,
                "option3": color,
                "weight": weight,
                "weight_unit": "lb",
                "metafields": vMeta,
            }
            if "Sample - " in vName:
                variant.update({"taxable": False})
            if gtin != None and gtin != "":
                variant.update({"barcode": gtin})

            variants.append(variant)

        return variants

    def ProductVariant(self, variantID):
        self.csr.execute("SELECT IsDefault, Name, Price, Weight, Cost, Pricing, MinimumQuantity, RestrictedQuantities, GTIN, Published FROM ProductVariant WHERE SKU = {} AND VariantID = {}".format(
            sq(self.sku), variantID))
        v = self.csr.fetchone()

        isDefault = v[0]
        vName = v[1].title()
        price = float(v[2])
        weight = float(v[3])
        cost = float(v[4])
        pricing = v[5]
        minimum = v[6]
        increment = v[7]
        gtin = v[8]
        vPublished = v[9]
        mpn = self.mpn
        color = self.color
        pattern = self.pattern

        # Variant MetaFields
        vMeta = [
            {"key": "Cost", "value": cost,
                "namespace": "inventory", "value_type": "string"},
            {"key": "ManufacturerPartNumber", "value": mpn,
                "namespace": "inventory", "value_type": "string"},
            {"key": "UnitOfMeasurement", "value": pricing,
                "namespace": "inventory", "value_type": "string"},
            {"key": "Published", "value": vPublished,
                "namespace": "inventory", "value_type": "string"}
        ]
        if "Sample - " not in vName:
            if minimum != None and minimum != 1:
                vMeta.append({"key": "MinimumQuantity", "value": minimum,
                             "namespace": "inventory", "value_type": "string"})
            if increment != None and increment != "":
                vMeta.append({"key": "RestrictedQuantities", "value": increment,
                             "namespace": "inventory", "value_type": "string"})
        else:
            vMeta.append({"key": "RestrictedQuantities", "value": "1",
                         "namespace": "inventory", "value_type": "string"})

        variant = {
            "title": vName,
            "price": price,
            "sku": self.sku,
            "option1": vName,
            "option2": pattern,
            "option3": color,
            "weight": weight,
            "weight_unit": "lb",
            "metafields": vMeta,
        }
        if "Sample - " in vName:
            variant.update({"taxable": False})
        if gtin != None and gtin != "":
            variant.update({"barcode": gtin})

        return variant


def sq(x):
    return "N'" + x.replace("'", "''") + "'"


def NewProductBySku(sku, con):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_newproduct_key'), env('shopify_newproduct_password'))
    s = requests.Session()
    csr = con.cursor()
    csr.execute("SELECT Title FROM Product WHERE SKU = {}".format(sq(sku)))
    title = (csr.fetchone())[0]
    rTitle = s.get(api_url + "/admin/api/{}/products.json?title={}".format(
        api_version, urllib.parse.quote_plus(title)))
    jTitle = json.loads(rTitle.text)

    for cp in jTitle['products']:
        if cp['variants'][0]['sku'] == sku:
            cProductID = cp['id']
            cHandle = cp['handle']
            csr.execute("UPDATE Product SET ProductID = {}, Handle = {} WHERE SKU = {}".format(
                cProductID, sq(cHandle), sq(sku)))
            con.commit()
            return cProductID

    pd = ProductData(con, sku)
    body = pd.body
    title = pd.title
    ptype = pd.ptype
    pattern = pd.pattern
    color = pd.color
    manu = pd.manufacturer
    published = pd.published

    # Product Variants
    titles = []
    variants = pd.ProductVariants()
    for variant in variants:
        titles.append(variant['title'])

    # Product Tag
    tags = pd.ProductTag()

    # Product Metafields
    pMeta = pd.ProductMetafield()

    p = {
        "body_html": body,
        "options": [
            {"name": "Title", "position": 1, "values": titles},
            {"name": "Pattern", "position": 2, "values": [pattern]},
            {"name": "Color", "position": 3, "values": [color]},
        ],
        "product_type": ptype,
        "tags": ",".join(tags),
        "title": title,
        "variants": variants,
        "vendor": manu,
        "metafields": pMeta
    }

    if published == 0:
        p.update({'published': False})

    r = s.post(
        api_url + "/admin/api/{}/products.json".format(api_version), json={"product": p})
    j = json.loads(r.text)

    jp = j["product"]
    handle = jp["handle"]
    productID = jp["id"]
    csr.execute("UPDATE Product SET ProductID = {}, Handle = {} WHERE SKU = {}".format(
        productID, sq(handle), sq(sku)))
    con.commit()

    for pv in jp["variants"]:
        variantID = pv["id"]
        vTitle = pv["option1"]
        csr.execute("UPDATE ProductVariant SET ProductID = {}, VariantID = {} WHERE SKU = {} AND Name = {}".format(
            productID, variantID, sq(sku), sq(vTitle)))
        con.commit()

    csr.close()
    s.close()

    return productID


def UploadImageToShopify(src):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_uploadimage_key'), env('shopify_uploadimage_password'))

    s = requests.Session()
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key,
                      aws_secret_access_key=aws_secret_key)
    bucket_name = 'dbproductimages'

    con = pymysql.connect(host=db_host, user=db_username,
                          passwd=db_password, db=db_name, connect_timeout=5)
    csr = con.cursor()

    fl = os.listdir(src)
    for f in fl:
        try:
            if "_" not in f:
                productID = f.lower().replace(".jpg", "")
                csr.execute(
                    "SELECT NULL FROM ProductImage WHERE ProductID = {} AND ImageIndex = 1".format(productID))
                s3.upload_file("{}/{}".format(src, f), bucket_name, "{}.jpg".format(
                    productID), ExtraArgs={'ContentType': 'image/jpeg', 'ACL': 'public-read'})
                os.remove('{}/{}'.format(src, f))
                imgLink = "https://s3.amazonaws.com/{}/{}.jpg".format(
                    bucket_name, productID)

                rImage = s.put(api_url + "/admin/api/{}/products/{}.json".format(api_version,
                               productID), json={"product": {"id": productID, "images": [{"src": imgLink}]}})
                jImage = json.loads(rImage.text)
                jpImage = jImage["product"]
                csr.execute("CALL AddToProductImage ({}, 1, {}, '{}')".format(
                    productID, jpImage['image']['id'], jpImage["image"]["src"]))
                con.commit()
            else:
                tmp = f.lower().replace(".jpg", "").split("_")
                productID = tmp[0]
                idx = tmp[1]

                csr.execute("SELECT ImageID FROM ProductImage WHERE ProductID = {} AND ImageIndex = {}".format(
                    productID, idx))
                temp = csr.fetchone()
                if temp != None:
                    imageId = temp[0]
                    rImage = s.delete(
                        api_url + "/admin/api/{}/products/{}/images/{}.json".format(api_version, productID, imageId))
                    jImage = json.loads(rImage.text)

                s3.upload_file("{}/{}".format(src, f), bucket_name, f,
                               ExtraArgs={'ContentType': 'image/jpeg', 'ACL': 'public-read'})
                os.remove('{}/{}'.format(src, f))
                imgLink = "https://s3.amazonaws.com/{}/{}".format(
                    bucket_name, f)

                rImage = s.post(api_url + "/admin/api/{}/products/{}/images.json".format(
                    api_version, productID), json={"image": {"position": idx, "src": imgLink}})
                jImage = json.loads(rImage.text)

                csr.execute("CALL AddToProductImage ({}, {}, {}, '{}')".format(
                    productID, idx, jImage['image']['id'], jImage["image"]["src"]))
                con.commit()
        except:
            continue

    csr.close()
    con.close()


def UpdateProductToShopify(productID, key, password, con):
    # api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(env('shopify_updateproduct_key, env('shopify_updateproduct_password)
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        key, password)
    s = requests.Session()
    csr = con.cursor()
    csr.execute(
        "SELECT SKU, Published FROM Product WHERE ProductID = {}".format(productID))
    # if 1==1:
    try:
        upd = csr.fetchone()
        pub = upd[1]
        sku = upd[0]

        pd = ProductData(con, sku)

        titles = []
        csr.execute(
            "SELECT VariantID FROM ProductVariant WHERE SKU = {}".format(sq(sku)))
        for v in csr.fetchall():
            variantID = v[0]
            rvm = s.get(api_url + "/admin/api/{}/products/{}/variants/{}/metafields.json".format(
                api_version, productID, variantID))
            jvm = json.loads(rvm.text)
            if 'metafields' in jvm:
                for vm in jvm['metafields']:
                    s.delete(
                        api_url + "/admin/api/{}/metafields/{}.json".format(api_version, vm['id']))
            variant = pd.ProductVariant(variantID)
            titles.append(variant['title'])
            variant.update({"id": variantID})
            s.put(api_url + "/admin/api/{}/variants/{}.json".format(api_version,
                  variantID), json={"variant": variant})

        ###################################################################################################
        # If NOT need to update the product metafield, comment the section and the below 2 sections
        # rpm = s.get(api_url + "/admin/api/{}/products/{}/metafields.json".format(api_version, productID))
        # jpm = json.loads(rpm.text)
        # for pm in jpm['metafields']:
        #     s.delete(api_url + "/admin/api/{}/metafields/{}.json".format(api_version, pm['id']))
        ###################################################################################################

        body = pd.body
        title = pd.title
        ptype = pd.ptype
        pattern = pd.pattern
        color = pd.color
        manu = pd.manufacturer
        published = pd.published
        tags = pd.ProductTag()
        ##########################################
        # pMeta = pd.ProductMetafield()
        ##########################################

        p = {
            "body_html": body,
            "options": [
                {"name": "Title", "position": 1, "values": titles},
                {"name": "Pattern", "position": 2, "values": [pattern]},
                {"name": "Color", "position": 3, "values": [color]},
            ],
            "product_type": ptype,
            "tags": ",".join(tags),
            "title": title,
            "vendor": manu,
            ##################################
            # "metafields" : pMeta
            ##################################
        }

        if published == 0:
            p.update({'published': False})

        r = s.put(api_url + "/admin/api/{}/products/{}.json".format(api_version,
                  productID), json={"product": p})
        # print r.text
        csr.execute(
            "DELETE FROM PendingUpdateProduct WHERE ProductID = {}".format(productID))
        con.commit()

    except Exception as e:
        print(e)

    csr.close()
    s.close()


def UpdatePriceToShopify(productID, con):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updateprice_key'), env('shopify_updateprice_password'))

    s = requests.Session()
    csr = con.cursor()
    csr.execute(
        "SELECT VariantID, Price FROM ProductVariant WHERE ProductID = {} AND Name NOT LIKE '%Sample - %'".format(productID))
    for row in csr.fetchall():
        variantID = row[0]
        price = float(row[1])

        r = s.put(api_url + "/admin/api/{}/variants/{}.json".format(api_version,
                  variantID), json={"variant": {'id': variantID, 'price': price}})

        csr.execute(
            "DELETE FROM PendingUpdatePrice WHERE ProductID = {}".format(productID))
        con.commit()

    csr.close()
    s.close()


def UpdatePublishToShopify(productID, con):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updatepublish_key'), env('shopify_updatepublish_password'))

    s = requests.Session()
    csr = con.cursor()
    csr.execute("SELECT P.Published, (SELECT PI.ImageIndex FROM ProductImage PI WHERE PI.ImageIndex = 1 and PI.ProductID=P.ProductID) img, P.ProductID FROM Product P WHERE P.ProductID = {}".format(productID))
    for row in csr.fetchall():
        if row[0] == 1:
            # Publish only if image is present
            if row[1] is not None and row[1] == 1:
                published = True
            else:
                # Don not publish
                published = False
                csr.execute(
                    "UPDATE Product SET Published = 0 WHERE ProductID = {}".format(productID))
                debug(
                    "shopify", 1, "Unpublished because image not present : pid -> {}".format(productID))
        else:
            published = False

        r = s.put(api_url + "/admin/api/{}/products/{}.json".format(api_version,
                  productID), json={"product": {'id': productID, 'published': published, 'status': 'active'}})

        csr.execute(
            "DELETE FROM PendingUpdatePublish WHERE ProductID = {}".format(productID))
        con.commit()

    csr.close()
    s.close()


def UpdateTagBodyToShopify(productID, con):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updatetagbody_key'), env('shopify_updatetagbody_password'))

    s = requests.Session()
    csr = con.cursor()
    csr.execute("SELECT SKU FROM Product WHERE ProductID = {}".format(productID))
    sku = (csr.fetchone())[0]
    pd = ProductData(con, sku)
    body = pd.body
    tags = pd.ProductTag()
    tag = ",".join(tags)

    r = s.put(api_url + "/admin/api/{}/products/{}.json".format(api_version, productID),
              json={"product": {"id": productID, "body_html": body, "tags": tag}})

    csr.execute(
        "DELETE FROM PendingUpdateTagBodyHTML WHERE ProductID = {}".format(productID))
    con.commit()

    csr.close()
    s.close()


def AddProductToCollection(productID, collectionID):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_addproducttocollection_key'), env('shopify_addproducttocollection_password'))
    s = requests.Session()
    r = s.post(api_url + "/admin/api/{}/collects.json".format(api_version, productID),
               json={"collect": {"product_id": productID, "collection_id": collectionID}})


def UpdateProductByProductID(productID, param):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updateproductbyid_key'), env('shopify_updateproductbyid_password'))

    s = requests.Session()
    r = s.put(api_url + "/admin/api/{}/products/{}.json".format(api_version,
              productID), json={"product": param})

    s.close()


def UpdateVariantByVariantID(variantID, param):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updateproductbyid_key'), ('shopify_updateproductbyid_password'))

    s = requests.Session()
    r = s.put(api_url + "/admin/api/{}/variants/{}.json".format(api_version,
              variantID), json={"variant": param})

    s.close()


def DeleteVariantByVariantID(variantID):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updateproductbyid_key'), env('shopify_updateproductbyid_password'))

    s = requests.Session()
    r = s.delete(
        api_url + "/admin/api/{}/variants/{}.json".format(api_version, variantID))

    s.close()


def DeleteProductByProductID(productID):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updateproductbyid_key'), env('shopify_updateproductbyid_password'))

    s = requests.Session()
    r = s.delete(
        api_url + "/admin/api/{}/products/{}.json".format(api_version, productID))

    s.close()


def GetProductByProductID(productID):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updateproductbyid_key'), env('shopify_updateproductbyid_password'))

    s = requests.Session()
    r = s.get(
        api_url + "/admin/api/{}/products/{}.json".format(api_version, productID))

    s.close()

    return r


def getProductsByVendor(vendor):
    api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
        env('shopify_updateproductbyid_key'), env('shopify_updateproductbyid_password'))

    s = requests.Session()
    r = s.get(
        api_url + "admin/api/{}/products.json?fields=id,vendor&vendor={}".format(api_version, vendor))

    s.close()
    return r
