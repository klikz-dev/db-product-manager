from django.contrib import admin

from .models import JamieYoung, Kravet, PhillipJeffries, Phillips, Scalamandre, Schumacher, StarkStudio, Surya, York


class FeedAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Primary Keys', {'fields': ['mpn', 'sku',
         'upc', 'pattern', 'color', 'title', 'productId']}),
        ('Categorization', {'fields': [
         'brand', 'type', 'manufacturer', 'collection']}),
        ('Main Information', {'fields': [
         'description', 'usage', 'disclaimer']}),
        ('Additional Information', {'fields': ['width', 'length', 'height', 'size', 'dimension', 'yards',
         'repeatH', 'repeatV', 'repeat', 'content', 'match', 'material', 'finish', 'care', 'specs', 'features', 'weight', 'country']}),
        ('Measurement', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['colors', 'tags']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': [
         'statusP', 'statusS', 'quickShip', 'whiteShip', 'bestSeller', 'outlet', 'stockP', 'stockS', 'stockNote']}),
        ('Assets', {'fields': ['thumbnail', 'roomsets']}),
    ]

    list_display = ('mpn', 'sku', 'pattern', 'color', 'productId', 'type',
                    'manufacturer', 'collection', 'cost', 'map', 'statusP', 'statusS')

    list_filter = ['brand', 'type', 'manufacturer',
                   'uom', 'statusP', 'statusS', 'whiteShip', 'quickShip']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


@admin.register(JamieYoung)
class JamieYoungAdmin(FeedAdmin):
    pass


@admin.register(Kravet)
class KravetAdmin(FeedAdmin):
    pass


@admin.register(PhillipJeffries)
class PhillipJeffriesAdmin(FeedAdmin):
    pass


@admin.register(Phillips)
class PhillipsAdmin(FeedAdmin):
    pass


@admin.register(Scalamandre)
class ScalamandreAdmin(FeedAdmin):
    pass


@admin.register(Schumacher)
class SchumacherAdmin(FeedAdmin):
    pass


@admin.register(StarkStudio)
class StarkStudioAdmin(FeedAdmin):
    pass


@admin.register(Surya)
class SuryaAdmin(FeedAdmin):
    pass


@admin.register(York)
class YorkAdmin(FeedAdmin):
    pass
