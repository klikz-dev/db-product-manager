from django.db import models


class Pklifestyles(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    content = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    sqft = models.FloatField(default=0)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    vr = models.FloatField(default=0)
    hr = models.FloatField(default=0)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    instruction = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Mindthegap(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    size = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    repeat = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    instruction = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class PremierPrints(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.FloatField(default=0)
    height = models.FloatField(default=0)
    rollLength = models.FloatField(default=0)
    content = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    hr = models.FloatField(default=0)
    vr = models.FloatField(default=0)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Covington(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.FloatField(default=0)
    height = models.FloatField(default=0)
    rollLength = models.FloatField(default=0)
    content = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    hr = models.FloatField(default=0)
    vr = models.FloatField(default=0)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Materialworks(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    size = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.FloatField(default=0)
    content = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    hr = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class MadcapCottage(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.FloatField(default=0)
    content = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    hr = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def title(self):
        return "{} {} {} {}".format(self.brand, self.pattern, self.color, self.ptype)

    def __str__(self):
        return self.mpn


class Zoffany(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.FloatField(default=0)
    height = models.FloatField(default=0)
    rollLength = models.FloatField(default=0)
    content = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    hr = models.FloatField(default=0)
    vr = models.FloatField(default=0)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Maxwell(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.FloatField(default=0)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Brewster(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    depth = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    repeat = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    bullet1 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    bullet2 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    bullet3 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    bullet4 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    bullet5 = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    # additional
    originalBrand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    only50Discount = models.BooleanField(default=True)

    def __str__(self):
        return self.mpn


class Fabricut(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    design = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    statusText = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    stock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class JFFabrics(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.FloatField(default=0)
    height = models.FloatField(default=0)
    rollLength = models.FloatField(default=0)
    content = models.CharField(max_length=1000)
    hr = models.FloatField(default=0)
    vr = models.FloatField(default=0)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Kasmir(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    construction = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Kravet(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    sample = models.BooleanField(default=True)
    statusText = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    stock = models.IntegerField(default=0)
    stockNote = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    sampleStock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Pindler(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class PhillipJeffries(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class RalphLauren(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    stockNote = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    sample = models.BooleanField(default=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Scalamandre(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    pieceSize = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    stockText = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Schumacher(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Seabrook(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    length = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.FloatField(default=0, null=True, blank=True)
    content = models.CharField(max_length=1000)
    repeat = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.TextField(
        max_length=1000, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Stout(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    stock = models.IntegerField(default=0)
    boqty = models.FloatField(default=0)
    bodue = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    url = models.CharField(max_length=200, default=None, null=True, blank=True)

    def __str__(self):
        return self.mpn


class York(models.Model):
    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    brand_num = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ptype = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection_num = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    rollLength = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    repeat = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    hr = models.CharField(max_length=200, default=None, null=True, blank=True)
    vr = models.CharField(max_length=200, default=None, null=True, blank=True)
    dimension = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    feature = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    match = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    style = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    category = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    status = models.BooleanField(default=True)
    statusText = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    stock = models.IntegerField(default=0)
    quickship = models.BooleanField(default=False)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn
