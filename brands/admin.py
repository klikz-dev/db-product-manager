from django.contrib import admin

from .models import Covington, ElaineSmith, MadcapCottage, Materialworks, Maxwell, Brewster, JFFabrics, Kasmir, Kravet, Pindler, PhillipJeffries, PremierPrints, Scalamandre, Schumacher, Seabrook, Stout, TresTintas, York, Zoffany


class ElaineSmithAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'size', 'usage']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'boDate', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset1', 'roomset2',
         'roomset3', 'roomset4', 'roomset5', 'roomset6', 'roomset7']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'size', 'productId', 'status', 'boDate')

    list_filter = ['ptype', 'status', 'uom',
                   'manufacturer', 'collection', 'size']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class TresTintasAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'rollLength', 'material', 'match', 'usage']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


# class PklifestylesAdmin(admin.ModelAdmin):
#     fieldsets = [
#         (None, {'fields': ['mpn', 'sku']}),
#         ('Identities', {'fields': ['pattern', 'color']}),
#         ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
#         ('Description', {'fields': [
#          'description', 'content', 'width', 'sqft', 'rollLength', 'vr', 'hr', 'material', 'match', 'instruction', 'feature', 'usage']}),
#         ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
#         ('Tagging', {'fields': ['style', 'colors', 'category']}),
#         ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
#         ('Availability', {'fields': ['status', 'stock']}),
#         ('Image', {'fields': ['thumbnail', 'roomset']}),
#         ('Shipify Product', {'fields': ['productId']}),
#     ]

#     list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
#                     'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

#     list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

#     search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


# class MindthegapAdmin(admin.ModelAdmin):
#     fieldsets = [
#         (None, {'fields': ['mpn', 'sku']}),
#         ('Identities', {'fields': ['pattern', 'color']}),
#         ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
#         ('Description', {'fields': [
#          'description', 'size', 'rollLength', 'content', 'repeat', 'material', 'instruction', 'country', 'usage']}),
#         ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
#         ('Tagging', {'fields': ['style', 'colors', 'category']}),
#         ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
#         ('Availability', {'fields': ['status', 'stock']}),
#         ('Image', {'fields': ['thumbnail', 'roomset']}),
#         ('Shipify Product', {'fields': ['productId']}),
#     ]

#     list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
#                     'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

#     list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

#     search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class PremierPrintsAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'match', 'feature', 'usage']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class CovingtonAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'match', 'feature', 'usage']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class MaterialworksAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'size', 'rollLength', 'content', 'hr', 'vr', 'match', 'feature', 'usage']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'size', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom',
                   'manufacturer', 'collection', 'size']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class MadcapCottageAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'match', 'feature', 'usage']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')
    # list_display = ('productId', 'title')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class ZoffanyAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'match', 'feature', 'usage']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class MaxwellAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class BrewsterAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': [
         'ptype', 'manufacturer', 'collection', 'originalBrand']}),
        ('Description', {'fields': ['description', 'width', 'height', 'rollLength', 'content',
         'repeat', 'feature', 'bullet1', 'bullet2', 'bullet3', 'bullet4', 'bullet5']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map', 'only50Discount']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'map', 'msrp', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


# class FabricutAdmin(admin.ModelAdmin):
#     fieldsets = [
#         (None, {'fields': ['mpn', 'sku']}),
#         ('Identities', {'fields': ['pattern', 'color']}),
#         ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
#         ('Description', {'fields': [
#          'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'feature']}),
#         ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
#         ('Tagging', {'fields': ['style', 'colors', 'category']}),
#         ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
#         ('Availability', {'fields': ['status', 'stock']}),
#         ('Image', {'fields': ['thumbnail', 'roomset']}),
#         ('Shipify Product', {'fields': ['productId']}),
#     ]

#     list_display = ('mpn', 'sku', 'collection', 'pattern', 'color', 'uom',
#                     'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

#     list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

#     search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class JFFabricsAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'country', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map', 'weight']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class KasmirAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'feature', 'construction']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class KravetAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': [
         'status', 'statusText', 'stock', 'stockNote']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'size', 'productId', 'status', 'statusText', 'stock', 'sampleStock')

    list_filter = ['ptype', 'status', 'statusText', 'sample',
                   'uom', 'manufacturer', 'collection', 'size']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class PindlerAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class PhillipJeffriesAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'minimum', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


# class RalphLaurenAdmin(admin.ModelAdmin):
#     fieldsets = [
#         (None, {'fields': ['mpn', 'sku']}),
#         ('Identities', {'fields': ['pattern', 'color']}),
#         ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
#         ('Description', {'fields': [
#          'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'feature']}),
#         ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
#         ('Tagging', {'fields': ['style', 'colors', 'category']}),
#         ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
#         ('Availability', {'fields': ['status', 'stock']}),
#         ('Image', {'fields': ['thumbnail', 'roomset']}),
#         ('Shipify Product', {'fields': ['productId']}),
#     ]

#     list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
#                     'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'sample', 'stock')

#     list_filter = ['ptype', 'manufacturer',
#                    'status', 'sample', 'uom', 'collection']

#     search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class ScalamandreAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'pieceSize', 'rollLength', 'content', 'hr', 'vr', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock', 'stockText']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'pieceSize', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom',
                   'manufacturer', 'collection', 'pieceSize']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class SchumacherAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'rollLength', 'height', 'content', 'hr', 'vr', 'feature', 'match']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'size', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom',
                   'manufacturer', 'minimum', 'collection', 'size']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class SeabrookAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'repeat', 'hr', 'vr', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class StoutAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': ['ptype', 'manufacturer', 'collection']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'content', 'hr', 'vr', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': ['status', 'stock', 'boqty', 'bodue']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock', 'bodue')

    list_filter = ['ptype', 'status', 'uom', 'manufacturer', 'collection']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


class YorkAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['mpn', 'sku']}),
        ('Identities', {'fields': ['pattern', 'color']}),
        ('Collection', {'fields': [
         'ptype', 'manufacturer', 'collection', 'brand_num', 'collection_num']}),
        ('Description', {'fields': [
         'description', 'width', 'height', 'rollLength', 'dimension', 'repeat', 'match', 'feature']}),
        ('Cut by', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['style', 'colors', 'category']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': [
         'status', 'statusText', 'stock', 'quickship']}),
        ('Image', {'fields': ['thumbnail', 'roomset']}),
        ('Shipify Product', {'fields': ['productId']}),
    ]

    list_display = ('mpn', 'sku', 'brand', 'collection_num', 'collection', 'pattern', 'color',
                    'cost', 'msrp', 'map', 'uom', 'productId', 'status', 'stock', 'quickship')

    list_filter = ['ptype', 'status', 'uom',
                   'manufacturer', 'collection', 'quickship']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


# Register Models
admin.site.register(ElaineSmith, ElaineSmithAdmin)
admin.site.register(TresTintas, TresTintasAdmin)
# admin.site.register(Pklifestyles, PklifestylesAdmin)
# admin.site.register(Mindthegap, MindthegapAdmin)
admin.site.register(PremierPrints, PremierPrintsAdmin)
admin.site.register(Covington, CovingtonAdmin)
admin.site.register(Materialworks, MaterialworksAdmin)
admin.site.register(MadcapCottage, MadcapCottageAdmin)
admin.site.register(Zoffany, ZoffanyAdmin)
admin.site.register(Maxwell, MaxwellAdmin)
admin.site.register(Brewster, BrewsterAdmin)
# admin.site.register(Fabricut, FabricutAdmin)
admin.site.register(JFFabrics, JFFabricsAdmin)
admin.site.register(Kasmir, KasmirAdmin)
admin.site.register(Kravet, KravetAdmin)
admin.site.register(Pindler, PindlerAdmin)
admin.site.register(PhillipJeffries, PhillipJeffriesAdmin)
# admin.site.register(RalphLauren, RalphLaurenAdmin)
admin.site.register(Scalamandre, ScalamandreAdmin)
admin.site.register(Schumacher, SchumacherAdmin)
admin.site.register(Seabrook, SeabrookAdmin)
admin.site.register(Stout, StoutAdmin)
admin.site.register(York, YorkAdmin)
