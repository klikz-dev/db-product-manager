from django.db import models


class Feed(models.Model):
    mpn = models.CharField(max_length=200, primary_key=True)
    sku = models.CharField(max_length=200, default=None, null=True, blank=True)
    upc = models.CharField(max_length=200, default=None, null=True, blank=True)
    pattern = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    color = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    title = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    productId = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    brand = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    type = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    manufacturer = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    collection = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    description = models.CharField(
        max_length=5000, default=None, null=True, blank=True)
    usage = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    disclaimer = models.CharField(
        max_length=2000, default=None, null=True, blank=True)

    width = models.FloatField(default=0, null=True, blank=True)  # inch
    length = models.FloatField(default=0, null=True, blank=True)  # inch
    height = models.FloatField(default=0, null=True, blank=True)  # inch
    size = models.CharField(
        max_length=200, default=None, null=True, blank=True)  # explains width x length
    dimension = models.CharField(
        max_length=200, default=None, null=True, blank=True)  # explains width x length x height

    repeatH = models.FloatField(default=0, null=True, blank=True)
    repeatV = models.FloatField(default=0, null=True, blank=True)
    repeat = models.CharField(
        max_length=200, default=None, null=True, blank=True)  # explains repeatH x repeatV

    material = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    finish = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    care = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    # array of {"key": "text"} object
    specs = models.JSONField(default=None, null=True, blank=True)
    features = models.JSONField(
        default=None, null=True, blank=True)  # array of texts
    weight = models.FloatField(default=0, null=True, blank=True)

    country = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    uom = models.CharField(max_length=200, default=None, null=True, blank=True)
    minimum = models.IntegerField(default=1)
    increment = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    tags = models.CharField(
        max_length=1000, default=None, null=True, blank=True)
    colors = models.CharField(
        max_length=1000, default=None, null=True, blank=True)

    cost = models.FloatField(default=0)
    msrp = models.FloatField(default=0)
    map = models.FloatField(default=0)

    statusP = models.BooleanField(default=False)
    statusS = models.BooleanField(default=False)
    stockP = models.IntegerField(default=0)
    stockS = models.IntegerField(default=0)

    thumbnail = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    roomsets = models.JSONField(
        default=None, null=True, blank=True)  # array of texts

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Feed"
        verbose_name_plural = "Feeds"

    def __str__(self):
        return self.mpn
