from django.db import models


class Brewster(models.Model):
    class Meta:
        verbose_name = "Brewster"
        verbose_name_plural = "Brewster"

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


class CoutureLamps(models.Model):
    class Meta:
        verbose_name = "Couture Lamps"
        verbose_name_plural = "Couture Lamps"

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
    width = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    height = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    depth = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    care = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    features = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    specs = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.FloatField(default=1)
    upc = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
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
    boDate = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomsets = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Covington(models.Model):
    class Meta:
        verbose_name = "Covington"
        verbose_name_plural = "Covington"

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

    gtin = models.CharField(
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


class DanaGibson(models.Model):
    class Meta:
        verbose_name = "Data Gibson"
        verbose_name_plural = "Data Gibson"

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
    width = models.FloatField(default=1)
    height = models.FloatField(default=1)
    depth = models.FloatField(default=1)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    finish = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    features = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.FloatField(default=1)
    upc = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
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
    boDate = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomsets = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class ElaineSmith(models.Model):
    class Meta:
        verbose_name = "Elaine Smith"
        verbose_name_plural = "Elaine Smith"

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
    size = models.CharField(
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
    boDate = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.FloatField(default=1)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset1 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset2 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset3 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset4 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset5 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset6 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomset7 = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class JamieYoung(models.Model):
    class Meta:
        verbose_name = "Jamie Young"
        verbose_name_plural = "Jamie Young"

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
    width = models.FloatField(default=1)
    height = models.FloatField(default=1)
    depth = models.FloatField(default=1)
    features = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    disclaimer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    care = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    specs = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.FloatField(default=1)
    upc = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
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
    boDate = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomsets = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class JaipurLiving(models.Model):
    class Meta:
        verbose_name = "Jaipur Living"
        verbose_name_plural = "Jaipur Living"

    mpn = models.CharField(max_length=200)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    name = models.CharField(
        max_length=200, default=None, null=True, blank=True)
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
    width = models.FloatField(default=0)
    length = models.FloatField(default=0)
    height = models.FloatField(default=0)
    features = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    care = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.FloatField(default=1)
    upc = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
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
    boDate = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomsets = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class JFFabrics(models.Model):
    class Meta:
        verbose_name = "JF Fabrics"
        verbose_name_plural = "JF Fabrics"

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
    class Meta:
        verbose_name = "Kasmir"
        verbose_name_plural = "Kasmir"

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
    class Meta:
        verbose_name = "Kravet"
        verbose_name_plural = "Kravet"

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


class KravetDecor(models.Model):
    class Meta:
        verbose_name = "Kravet Decor"
        verbose_name_plural = "Kravet Decor"

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
    width = models.FloatField(default=1)
    height = models.FloatField(default=1)
    depth = models.FloatField(default=1)
    features = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    care = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.FloatField(default=1)
    upc = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
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
    boDate = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomsets = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class MadcapCottage(models.Model):
    class Meta:
        verbose_name = "Madcap Cottage"
        verbose_name_plural = "Madcap Cottage"

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


class Materialworks(models.Model):
    class Meta:
        verbose_name = "MaterialWorks"
        verbose_name_plural = "MaterialWorks"

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


class Maxwell(models.Model):
    class Meta:
        verbose_name = "Maxwell"
        verbose_name_plural = "Maxwell"

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
    repeat = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    content = models.CharField(max_length=1000)

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


class PhillipJeffries(models.Model):
    class Meta:
        verbose_name = "Phillip Jeffries"
        verbose_name_plural = "Phillip Jeffries"

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


class Pindler(models.Model):
    class Meta:
        verbose_name = "Pindler"
        verbose_name_plural = "Pindler"

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


class PremierPrints(models.Model):
    class Meta:
        verbose_name = "Premier Prints"
        verbose_name_plural = "Premier Prints"

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


class Scalamandre(models.Model):
    class Meta:
        verbose_name = "Scalamandre"
        verbose_name_plural = "Scalamandre"

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
    class Meta:
        verbose_name = "Schumacher"
        verbose_name_plural = "Schumacher"

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
    class Meta:
        verbose_name = "Seabrook"
        verbose_name_plural = "Seabrook"

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


class StarkStudio(models.Model):
    class Meta:
        verbose_name = "Stark Studio"
        verbose_name_plural = "Stark Studio"

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
    width = models.FloatField(default=1)
    length = models.FloatField(default=1)
    dimension = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    weight = models.FloatField(default=1)
    upc = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
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
    boDate = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomsets = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mpn


class Stout(models.Model):
    class Meta:
        verbose_name = "Stout"
        verbose_name_plural = "Stout"

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


class TresTintas(models.Model):
    class Meta:
        verbose_name = "Tres Tintas"
        verbose_name_plural = "Tres Tintas"

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
    width = models.FloatField(default=0)
    rollLength = models.FloatField(default=0)
    material = models.CharField(
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


class York(models.Model):
    class Meta:
        verbose_name = "York"
        verbose_name_plural = "York"

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


class Zoffany(models.Model):
    class Meta:
        verbose_name = "Zoffany"
        verbose_name_plural = "Zoffany"

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
