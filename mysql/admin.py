from django.contrib import admin

from .models import EditSize, Manufacturer, Admin, CustomEmail, EditCategory, EditColor, EditStyle, EditSubtype, PORecord
from .models import ProductManufacturer, PendingNewProduct, PendingUpdateProduct, PendingUpdatePublish, PendingUpdatePrice
from .models import PendingUpdateTag, ProductInventory, ProductSubcategory, ProductSubtype, ProductTag, Tag, Type


class AdminAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['Email', 'Password']

    ordering = ['-Email']

    list_display = ('Email', 'Password')

    search_fields = ['Email']


class CustomEmailAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['Email', 'cid', 'orderid', 'status', 'md', 'flow']

    ordering = ['-Email']

    list_filter = ['status']

    list_display = ('Email', 'cid', 'orderid', 'status', 'flow')

    search_fields = ['Email', 'cid', 'orderid', 'md', 'flow']


class EditCategoryAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'category', 'isManual']

    ordering = ['-updatedAt']

    list_filter = ['isManual']

    list_display = ('sku', 'category', 'isManual')

    search_fields = ['sku', 'category']


class EditColorAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'color', 'isManual']

    ordering = ['-updatedAt']

    list_filter = ['isManual']

    list_display = ('sku', 'color', 'isManual')

    search_fields = ['sku', 'color']


class EditStyleAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'style', 'isManual']

    ordering = ['-updatedAt']

    list_filter = ['isManual']

    list_display = ('sku', 'style', 'isManual')

    search_fields = ['sku', 'style']


class EditSubtypeAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'subType', 'isManual']

    ordering = ['-updatedAt']

    list_filter = ['isManual']

    list_display = ('sku', 'subType', 'isManual')

    search_fields = ['sku', 'subType']


class EditSizeAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'size', 'isManual']

    ordering = ['-updatedAt']

    list_filter = ['isManual', 'size']

    list_display = ('sku', 'size', 'isManual')

    search_fields = ['sku', 'size']


class ManufacturerAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    # def has_add_permission(self, request):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    fields = ['manufacturerId', 'name', 'brand']

    ordering = ['manufacturerId']

    list_display = ('manufacturerId', 'name', 'brand')

    list_filter = ['brand']

    search_fields = ['name', 'brand']


class ProductManufacturerAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'manufacturer']

    list_display = ('sku', 'manufacturer')

    list_filter = ['manufacturer']

    search_fields = ['sku']


class PendingNewProductAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku']

    list_display = ('sku',)

    search_fields = ['sku']


class PendingUpdateProductAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['productId']

    list_display = ('productId',)

    search_fields = ['productId']


class PendingUpdatePublishAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['productId']

    list_display = ('productId',)

    search_fields = ['productId']


class PendingUpdatePriceAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['productId']

    list_display = ('productId',)

    search_fields = ['productId']


class PendingUpdateTagAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['productId']

    list_display = ('productId',)

    search_fields = ['productId']


class PORecordAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    fields = ['KravetEDI', 'YorkEDI', 'FabricutEDI', 'RalphLaurenEDI',
              'ClarenceHouseEDI', 'SampleReminder', 'SampleReminder2', 'BrewsterEDI', 'SchumacherEDI', 'ScalamandreEDI',
              'CovingtonOrder',
              'CovingtonSample',
              'ElaineSmithOrder',
              'ElaineSmithSample',
              'JFFabricsOrder',
              'JFFabricsSample',
              'KasmirOrder',
              'KasmirSample',
              'MadcapCottageOrder',
              'MadcapCottageSample',
              'MaterialworksOrder',
              'MaterialworksSample',
              'MaxwellOrder',
              'MaxwellSample',
              'MindTheGapOrder',
              'MindTheGapSample',
              'PhillipJeffriesOrder',
              'PhillipJeffriesSample',
              'PindlerOrder',
              'PindlerSample',
              'PremierPrintsOrder',
              'PremierPrintsSample',
              'RalphLaurenOrder',
              'RalphLaurenSample',
              'SeabrookOrder',
              'SeabrookSample',
              'StoutOrder',
              'StoutSample',
              'TresTintasOrder',
              'TresTintasSample',
              'ZoffanyOrder',
              'ZoffanySample',
              ]

    list_display = ('KravetEDI', 'YorkEDI', 'FabricutEDI', 'RalphLaurenEDI',
                    'ClarenceHouseEDI', 'SampleReminder', 'SampleReminder2', 'BrewsterEDI', 'SchumacherEDI', 'ScalamandreEDI',
                    'CovingtonOrder',
                    'CovingtonSample',
                    'ElaineSmithOrder',
                    'ElaineSmithSample',
                    'JFFabricsOrder',
                    'JFFabricsSample',
                    'KasmirOrder',
                    'KasmirSample',
                    'MadcapCottageOrder',
                    'MadcapCottageSample',
                    'MaterialworksOrder',
                    'MaterialworksSample',
                    'MaxwellOrder',
                    'MaxwellSample',
                    'MindTheGapOrder',
                    'MindTheGapSample',
                    'PhillipJeffriesOrder',
                    'PhillipJeffriesSample',
                    'PindlerOrder',
                    'PindlerSample',
                    'PremierPrintsOrder',
                    'PremierPrintsSample',
                    'RalphLaurenOrder',
                    'RalphLaurenSample',
                    'SeabrookOrder',
                    'SeabrookSample',
                    'StoutOrder',
                    'StoutSample',
                    'TresTintasOrder',
                    'TresTintasSample',
                    'ZoffanyOrder',
                    'ZoffanySample',
                    )

    search_fields = ['KravetEDI', 'YorkEDI', 'FabricutEDI', 'RalphLaurenEDI',
                     'ClarenceHouseEDI', 'SampleReminder', 'SampleReminder2', 'BrewsterEDI', 'SchumacherEDI', 'ScalamandreEDI',
                     'CovingtonOrder',
                     'CovingtonSample',
                     'ElaineSmithOrder',
                     'ElaineSmithSample',
                     'JFFabricsOrder',
                     'JFFabricsSample',
                     'KasmirOrder',
                     'KasmirSample',
                     'MadcapCottageOrder',
                     'MadcapCottageSample',
                     'MaterialworksOrder',
                     'MaterialworksSample',
                     'MaxwellOrder',
                     'MaxwellSample',
                     'MindTheGapOrder',
                     'MindTheGapSample',
                     'PhillipJeffriesOrder',
                     'PhillipJeffriesSample',
                     'PindlerOrder',
                     'PindlerSample',
                     'PremierPrintsOrder',
                     'PremierPrintsSample',
                     'RalphLaurenOrder',
                     'RalphLaurenSample',
                     'SeabrookOrder',
                     'SeabrookSample',
                     'StoutOrder',
                     'StoutSample',
                     'TresTintasOrder',
                     'TresTintasSample',
                     'ZoffanyOrder',
                     'ZoffanySample',
                     ]


class ProductInventoryAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'quantity', 'type', 'note', 'brand']

    ordering = ['-updatedAt']

    list_display = ('sku', 'quantity', 'type', 'note', 'brand')

    list_filter = ['type', 'brand']

    search_fields = ['sku', 'note']


class ProductSubcategoryAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'subcat', 'val']

    ordering = ['-updatedAt']

    list_display = ('sku', 'subcat', 'val')

    search_fields = ['sku', 'subcat', 'val']


class ProductSubtypeAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'subtypeId']

    ordering = ['-updatedAt']

    list_display = ('sku', 'subtypeId')

    search_fields = ['sku', 'subtypeId']


class ProductTagAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    fields = ['sku', 'tagId']

    ordering = ['-updatedAt']

    list_display = ('sku', 'tagId')

    search_fields = ['sku', 'tagId']


class TagAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    # def has_add_permission(self, request):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    fields = ['tagId', 'name', 'parentTagId',
              'description', 'published', 'deleted']

    ordering = ['tagId']

    list_filter = ['parentTagId', 'published']

    list_display = ('tagId', 'name', 'parentTagId',
                    'description', 'published', 'deleted')

    search_fields = ['tagId', 'name', 'parentTagId', 'description']


class TypeAdmin(admin.ModelAdmin):
    actions = None

    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def has_add_permission(self, request):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    fields = ['typeId', 'name', 'parentTypeId', 'published']

    ordering = ['typeId']

    list_filter = ['parentTypeId']

    list_display = ('typeId', 'name', 'parentTypeId', 'published')

    search_fields = ['typeId', 'name', 'parentTypeId', 'published']


admin.site.register(Admin, AdminAdmin)
admin.site.register(CustomEmail, CustomEmailAdmin)
admin.site.register(EditCategory, EditCategoryAdmin)
admin.site.register(EditColor, EditColorAdmin)
admin.site.register(EditStyle, EditStyleAdmin)
admin.site.register(EditSubtype, EditSubtypeAdmin)
admin.site.register(EditSize, EditSizeAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(ProductManufacturer, ProductManufacturerAdmin)
admin.site.register(PendingNewProduct, PendingNewProductAdmin)
admin.site.register(PendingUpdateProduct, PendingUpdateProductAdmin)
admin.site.register(PendingUpdatePublish, PendingUpdatePublishAdmin)
admin.site.register(PendingUpdatePrice, PendingUpdatePriceAdmin)
admin.site.register(PendingUpdateTag, PendingUpdateTagAdmin)
admin.site.register(PORecord, PORecordAdmin)
admin.site.register(ProductInventory, ProductInventoryAdmin)
admin.site.register(ProductSubcategory, ProductSubcategoryAdmin)
admin.site.register(ProductSubtype, ProductSubtypeAdmin)
admin.site.register(ProductTag, ProductTagAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Type, TypeAdmin)
