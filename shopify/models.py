from django.db import models


class Customer(models.Model):
    customerId = models.CharField(max_length=200, primary_key=True)
    email = models.CharField(max_length=200)
    firstName = models.CharField(max_length=200)
    lastName = models.TextField(max_length=2000)
    phone = models.CharField(max_length=200)
    defaultAddressId = models.CharField(max_length=200)
    orderCount = models.IntegerField(default=0)
    totalSpent = models.FloatField(default=0)
    state = models.CharField(max_length=200)
    note = models.TextField(max_length=1000)
    tags = models.CharField(max_length=200)
    acceptsMarketing = models.BooleanField(default=False)

    createdAt = models.DateTimeField()
    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "Customer"


class Address(models.Model):
    addressId = models.CharField(max_length=200, primary_key=True)
    customer = models.ForeignKey(
        Customer, db_column="customerId", related_name='addresses', on_delete=models.CASCADE)
    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    zip = models.CharField(max_length=200)
    country = models.CharField(max_length=200)

    createdAt = models.DateTimeField()
    updatedAt = models.DateTimeField()

    def address(self):
        return "{}, {}, {} {}, {}, {}".format(self.address1, self.city, self.state, self.zip, self.country, self.phone)

    class Meta:
        managed = True
        db_table = "Address"


class ProductImage(models.Model):
    productId = models.CharField(max_length=200)
    imageIndex = models.IntegerField(default=1)
    imageId = models.CharField(max_length=200, primary_key=True)
    imageURL = models.CharField(max_length=200)

    updatedAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "ProductImage"


class Product(models.Model):
    sku = models.CharField(max_length=200, primary_key=True)
    productId = models.CharField(
        max_length=200, blank=True, default=None, null=True)

    manufacturerPartNumber = models.CharField(
        max_length=200, default=None, null=True)
    pattern = models.CharField(max_length=200, default=None, null=True)
    color = models.CharField(max_length=200, default=None, null=True)

    title = models.CharField(max_length=200, default=None, null=True)
    bodyHTML = models.TextField(max_length=2000, default=None, null=True)

    name = models.CharField(max_length=200, default=None, null=True)
    description = models.CharField(max_length=1000, default=None, null=True)
    handle = models.CharField(max_length=200, default=None, null=True)

    productTypeId = models.IntegerField(default=1, null=True, blank=True)

    isOutlet = models.BooleanField(default=False)
    published = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        managed = True
        db_table = "Product"


class Variant(models.Model):
    variantId = models.CharField(max_length=200, primary_key=True)

    productId = models.CharField(max_length=200, default=False, null=False)
    product = models.ForeignKey(
        Product, db_column='sku', related_name='variants', on_delete=models.CASCADE)

    name = models.CharField(max_length=200, default=None, null=True)

    cost = models.FloatField(default=0)
    price = models.FloatField(default=0)

    pricing = models.CharField(max_length=200, default=None, null=True)
    minimumQuantity = models.CharField(max_length=200, default=None, null=True)
    restrictedQuantities = models.CharField(
        max_length=200, default="", blank=True, null=True)
    weight = models.FloatField(default=1)
    GTIN = models.CharField(max_length=200, default=None, null=True)

    isDefault = models.BooleanField(default=True)
    published = models.BooleanField(default=True)

    backOrderDate = models.CharField(
        max_length=200, default='0000-00-00', blank=True, null=True)
    boDateStatus = models.SmallIntegerField(default=0)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        managed = True
        db_table = "ProductVariant"


class Order(models.Model):
    shopifyOrderId = models.CharField(max_length=200, primary_key=True)
    orderNumber = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    phone = models.CharField(max_length=200, default=None, null=True)
    customer = models.ForeignKey(
        Customer, db_column="customerId", related_name='orders', on_delete=models.CASCADE)

    billingLastName = models.CharField(
        max_length=200, default=None, null=True)
    billingFirstName = models.CharField(
        max_length=200, default=None, null=True)
    billingCompany = models.CharField(max_length=200, default=None, null=True)
    billingAddress1 = models.CharField(
        max_length=200, default=None, null=True)
    billingAddress2 = models.CharField(
        max_length=200, default=None, null=True)
    billingCity = models.CharField(max_length=200, default=None, null=True)
    billingState = models.CharField(max_length=200, default=None, null=True)
    billingZip = models.CharField(max_length=200, default=None, null=True)
    billingCountry = models.CharField(max_length=200, default=None, null=True)
    billingPhone = models.CharField(max_length=200, default=None, null=True)

    shippingLastName = models.CharField(
        max_length=200, default=None, null=True)
    shippingFirstName = models.CharField(
        max_length=200, default=None, null=True)
    shippingCompany = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    shippingAddress1 = models.CharField(
        max_length=200, default=None, null=True)
    shippingAddress2 = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    shippingCity = models.CharField(max_length=200, default=None, null=True)
    shippingState = models.CharField(max_length=200, default=None, null=True)
    shippingZip = models.CharField(max_length=200, default=None, null=True)
    shippingCountry = models.CharField(max_length=200, default=None, null=True)
    shippingPhone = models.CharField(max_length=200, default=None, null=True)

    shippingMethod = models.CharField(max_length=200, default=None, null=True)
    orderNote = models.CharField(
        max_length=2000, default=None, null=True, blank=True)
    totalItems = models.FloatField(default=0)
    totalDiscounts = models.FloatField(default=0)
    orderSubtotal = models.FloatField(default=0)
    orderTax = models.FloatField(default=0)
    orderShippingCost = models.FloatField(default=0)
    orderTotal = models.FloatField(default=0)

    weight = models.FloatField(default=0)
    orderDate = models.DateTimeField()
    initials = models.CharField(max_length=200, default=None, null=True)
    status = models.CharField(max_length=200, default="New", null=True)
    orderType = models.CharField(max_length=200, default="Order", null=True)
    manufacturerList = models.CharField(
        max_length=2000, default=None, null=True)
    referenceNumber = models.CharField(
        max_length=2000, default=None, null=True, blank=True)

    customerEmailed = models.SmallIntegerField(default=0)
    customerCalled = models.SmallIntegerField(default=0)
    customerChatted = models.SmallIntegerField(default=0)

    specialShipping = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    customerOrderStatus = models.CharField(
        max_length=200, default=None, null=True)

    note = models.CharField(
        max_length=5000, default=None, null=True, blank=True)
    oldPO = models.CharField(max_length=200, default=None, null=True)

    isFraud = models.SmallIntegerField(default=False)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def shippingAddress(self):
        return "{} {}, {}, {}, {}, {} {}, {}".format(
            self.shippingFirstName,
            self.shippingLastName,
            self.shippingAddress1,
            self.shippingAddress2,
            self.shippingCity,
            self.shippingState,
            self.shippingZip,
            self.shippingCountry
        )

    def __str__(self):
        return "PO {}".format(self.orderNumber)

    class Meta:
        managed = True
        db_table = "Orders"


class Line_Item(models.Model):
    order = models.ForeignKey(
        Order, db_column="shopifyOrderId", related_name='line_items', on_delete=models.CASCADE)

    variant = models.ForeignKey(
        Variant, db_column="variantId", related_name='line_items', on_delete=models.CASCADE)

    quantity = models.IntegerField(default=1)

    orderedProductTitle = models.CharField(
        max_length=200, default=None, null=True)
    orderedProductVariantTitle = models.CharField(
        max_length=200, default=None, null=True)
    orderedProductVariantName = models.CharField(
        max_length=200, default=None, null=True)
    orderedProductSKU = models.CharField(
        max_length=200, default=None, null=True)
    orderedProductManufacturer = models.CharField(
        max_length=200, default=None, null=True)
    orderedProductUnitPrice = models.FloatField(default=0)
    orderedProductLineDiscount = models.FloatField(default=0)
    orderedProductUnitWeight = models.FloatField(default=0)
    taxable = models.BooleanField(default=True)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} {}".format(self.quantity, self.orderedProductTitle)

    class Meta:
        managed = True
        db_table = "Orders_ShoppingCart"


class Tracking(models.Model):
    orderNumber = models.CharField(max_length=200, primary_key=True)
    brand = models.CharField(max_length=200)
    trackingNumber = models.CharField(max_length=200)
    trackingMethod = models.CharField(max_length=200)

    createdAt = models.DateTimeField()

    class Meta:
        managed = True
        db_table = "OrderTracking"
