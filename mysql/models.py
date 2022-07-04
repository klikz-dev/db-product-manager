from django.db import models


class Admin(models.Model):
    Email = models.CharField(max_length=200, primary_key=True)
    Password = models.CharField(max_length=200)

    class Meta:
        managed = True
        db_table = "Admin"


class CustomEmail(models.Model):
    Email = models.CharField(max_length=200, primary_key=True)
    cid = models.CharField(max_length=200)
    status = models.IntegerField(default=0)
    orderid = models.CharField(max_length=200)
    md = models.TextField(max_length=2000)
    flow = models.CharField(max_length=200)

    created = models.DateTimeField()
    updated = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "CustomEmails"


class EditCategory(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    category = models.CharField(max_length=2000)
    isManual = models.CharField(max_length=200)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "EditCategory"


class EditColor(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    color = models.CharField(max_length=2000)
    isManual = models.CharField(max_length=200)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "EditColor"


class EditStyle(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    style = models.CharField(max_length=2000)
    isManual = models.CharField(max_length=200)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "EditStyle"


class EditSubtype(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    subType = models.CharField(max_length=2000)
    isManual = models.CharField(max_length=200)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "EditSubtype"


class Manufacturer(models.Model):
    manufacturerId = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200)

    class Meta:
        managed = True
        db_table = "Manufacturer"

    def __str__(self):
        return self.name


class ProductManufacturer(models.Model):
    sku = models.CharField(
        max_length=200, primary_key=True)

    # Get Manufactuer
    manufacturer = models.ForeignKey(
        Manufacturer, db_column='manufacturerId', on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = "ProductManufacturer"


class PendingNewProduct(models.Model):
    sku = models.CharField(
        max_length=200, primary_key=True)

    class Meta:
        managed = True
        db_table = "PendingNewProduct"


class PendingUpdateProduct(models.Model):
    productId = models.CharField(
        max_length=200, primary_key=True)

    class Meta:
        managed = True
        db_table = "PendingUpdateProduct"


class PendingUpdatePublish(models.Model):
    productId = models.CharField(
        max_length=200, primary_key=True)

    class Meta:
        managed = True
        db_table = "PendingUpdatePublish"


class PendingUpdatePrice(models.Model):
    productId = models.CharField(
        max_length=200, primary_key=True)

    class Meta:
        managed = True
        db_table = "PendingUpdatePrice"


class PendingUpdateTag(models.Model):
    productId = models.CharField(
        max_length=200, primary_key=True)

    class Meta:
        managed = True
        db_table = "PendingUpdateTagBodyHTML"


class PORecord(models.Model):
    KravetEDI = models.CharField(
        max_length=200, primary_key=True)
    YorkEDI = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    FabricutEDI = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    RalphLaurenEDI = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    ClarenceHouseEDI = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    SampleReminder = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    SampleReminder2 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    BrewsterEDI = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    SchumacherEDI = models.CharField(
        max_length=200, default=None, null=True, blank=True)

    class Meta:
        managed = True
        db_table = "PORecord"


class ProductInventory(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    quantity = models.CharField(max_length=200)
    type = models.IntegerField(default=1)
    note = models.TextField(max_length=1000)
    brand = models.CharField(max_length=200)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "ProductInventory"


class ProductSubcategory(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    subcat = models.CharField(max_length=200)
    val = models.IntegerField(default=1)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "ProductSubcategory"


class ProductSubtype(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    subtypeId = models.CharField(max_length=200)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "ProductSubtype"


class ProductTag(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    tagId = models.CharField(max_length=200)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "ProductTag"


class Tag(models.Model):
    tagId = models.IntegerField(default=1, primary_key=True)
    name = models.CharField(max_length=200)
    parentTagId = models.IntegerField(default=0)
    description = models.CharField(max_length=200)
    published = models.BooleanField(default=True)
    deleted = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "Tag"


class Type(models.Model):
    typeId = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200)
    parentTypeId = models.IntegerField(default=0)
    published = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "Type"
