from django.contrib import admin
from django import forms

from .models import Product, Variant, Order, Line_Item, Tracking
from mysql.models import Manufacturer, PendingNewProduct, ProductManufacturer, Type, PendingUpdatePrice, PendingUpdateProduct, PendingUpdatePublish


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper


class VariantAdmin(admin.ModelAdmin):
    actions = None

    def get_readonly_fields(self, request, obj=None):
        return self.fields or [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fields = ['product', 'name', 'cost', 'price', 'pricing',
              'minimumQuantity', 'restrictedQuantities', 'weight', 'isDefault', 'published']

    list_display = ('variantId', 'productId', 'product', 'name', 'cost',
                    'pricing', 'isDefault', 'published')
    list_filter = ['pricing', 'isDefault', 'published']
    search_fields = ['variantId', 'productId', 'name', ]


class VariantInline(admin.StackedInline):
    model = Variant
    extra = 0

    def __init__(self, *args, **kwargs):
        super(VariantInline, self).__init__(*args, **kwargs)
        self.can_delete = False


class ProductForm(forms.ModelForm):
    manufacturer = extra_field = forms.ChoiceField()
    type = extra_field = forms.ChoiceField()

    def manufacturers(self):
        pmArray = []
        manufacturers = Manufacturer.objects.all()
        for manufacturer in manufacturers:
            pmArray.append((manufacturer.name,
                            manufacturer.name))
        return pmArray

    def selectedManufacturer(self):
        if self.instance.sku:
            productManufacturer = ProductManufacturer.objects.get(
                sku=self.instance.sku)
            return productManufacturer.manufacturer.name
        else:
            return None

    def types(self):
        tArray = []
        types = Type.objects.all()
        for type in types:
            tArray.append((type.typeId,
                           type.name))
        return tArray

    class Meta:
        model = Product
        fields = ('productId', 'sku')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['productId'].disabled = True
        self.fields['manufacturer'].choices = self.manufacturers
        self.fields['manufacturer'].initial = self.selectedManufacturer
        self.fields['type'].choices = self.types
        self.fields['type'].initial = self.instance.productTypeId


class ProductAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    # form = ProductForm

    fieldsets = [
        (None, {'fields': [
            'productId', 'sku'
        ]}),
        ("Product Specification", {'fields': [
            'manufacturerPartNumber',
            'pattern',
            'color',
        ]}),
        ("Content", {'fields': [
            'title',
            'bodyHTML',
        ]}),
        # ("Category", {'fields': [
        #     'manufacturer',
        #     'type'
        # ]}),
        ("Status", {'fields': [
            'isOutlet',
            'published',
            'deleted',
        ]}),
    ]
    inlines = [VariantInline]

    ordering = ['sku']

    list_display = ('productId', 'sku', 'manufacturerPartNumber',
                    'pattern', 'color', 'published')

    search_fields = ['productId', 'manufacturerPartNumber',
                     'sku', 'pattern', 'color', 'name', 'title']

    list_filter = ['isOutlet', 'published', 'deleted']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.productId != "" and obj.productId != None:
            try:
                PendingUpdateProduct.objects.create(
                    productId=obj.productId
                )
            except:
                pass

            try:
                PendingUpdatePublish.objects.create(
                    productId=obj.productId
                )
            except:
                pass

            try:
                PendingUpdatePrice.objects.create(
                    productId=obj.productId
                )
            except:
                pass
        else:
            try:
                PendingNewProduct.objects.create(
                    sku=obj.sku
                )
            except:
                pass


class ItemInline(admin.StackedInline):
    model = Line_Item


class OrderAdmin(admin.ModelAdmin):
    actions = None

    def get_readonly_fields(self, request, obj=None):
        return self.fields or [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fieldsets = [
        (None, {'fields': [
            'shopifyOrderId',
            'orderNumber'
        ]}),
        ("Customer Info", {'fields': [
            'email',
            'phone',
            'customer',
        ]}),
        ("Billing Information", {'fields': [
            'billingFirstName',
            'billingLastName',
            'billingCompany',
            'billingAddress1',
            'billingAddress2',
            'billingCity',
            'billingState',
            'billingZip',
            'billingCountry',
            'billingPhone',
        ]}),
        ("Shipping Information", {'fields': [
            'shippingFirstName',
            'shippingLastName',
            'shippingCompany',
            'shippingAddress1',
            'shippingAddress2',
            'shippingCity',
            'shippingState',
            'shippingZip',
            'shippingCountry',
            'shippingPhone',
            'shippingMethod',
        ]}),
        ("Order Data", {'fields': [
            'orderNote',
            'totalItems',
            'totalDiscounts',
            'orderSubtotal',
            'orderTax',
            'orderShippingCost',
            'orderTotal',
            'weight',
            'orderDate',
        ]}),
        ("Additional Information", {'fields': [
            'initials',
            'status',
            'orderType',
            'manufacturerList',
            'referenceNumber',
            'customerEmailed',
            'customerCalled',
            'customerChatted',
            'specialShipping',
            'customerOrderStatus',
            'isFraud',
            'note',
            'oldPO',
        ]}),
    ]
    inlines = [ItemInline]

    list_display = ('orderNumber', 'email', 'shippingAddress',
                    'orderType', 'orderTotal', 'status', 'referenceNumber', 'orderDate', 'shippingMethod')
    list_filter = ['status', 'orderDate', 'orderType', 'shippingMethod']
    search_fields = ['orderNumber', 'shopifyOrderId',
                     'email', 'shippingFirstName']


class TrackingAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['orderNumber', 'brand', 'trackingNumber', 'trackingMethod']

    ordering = ['-createdAt']

    list_filter = ['brand', 'trackingMethod']

    list_display = ('orderNumber', 'brand', 'trackingNumber', 'trackingMethod')

    search_fields = ['orderNumber', 'brand',
                     'trackingNumber', 'trackingMethod']


admin.site.register(Variant, VariantAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Tracking, TrackingAdmin)
