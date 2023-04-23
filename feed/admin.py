from django.contrib import admin

from .models import Brewster, CoutureLamps, Covington, DanaGibson, ElaineSmith, JaipurLiving, JamieYoung, JFFabrics
from .models import Kasmir, Kravet, KravetDecor, MadcapCottage, Materialworks, Maxwell, MindTheGap, PhillipJeffries
from .models import Phillips, Pindler, Port68, PremierPrints, Scalamandre, Schumacher, Seabrook, StarkStudio, Stout, Surya
from .models import TresTintas, York, Zoffany


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
                   'uom', 'statusP', 'statusS', 'whiteShip', 'quickShip', 'collection']

    search_fields = ['mpn', 'sku', 'productId',
                     'pattern', 'color', 'collection']


@admin.register(Brewster)
class BrewsterAdmin(FeedAdmin):
    pass


@admin.register(CoutureLamps)
class CoutureLampsAdmin(FeedAdmin):
    pass


@admin.register(Covington)
class CovingtonAdmin(FeedAdmin):
    pass


@admin.register(DanaGibson)
class DanaGibsonAdmin(FeedAdmin):
    pass


@admin.register(ElaineSmith)
class ElaineSmithAdmin(FeedAdmin):
    pass


@admin.register(JaipurLiving)
class JaipurLivingAdmin(FeedAdmin):
    pass


@admin.register(JamieYoung)
class JamieYoungAdmin(FeedAdmin):
    pass


@admin.register(JFFabrics)
class JFFabricsAdmin(FeedAdmin):
    pass


@admin.register(Kasmir)
class KasmirAdmin(FeedAdmin):
    pass


@admin.register(Kravet)
class KravetAdmin(FeedAdmin):
    pass


@admin.register(KravetDecor)
class KravetDecorAdmin(FeedAdmin):
    pass


@admin.register(MadcapCottage)
class MadcapCottageAdmin(FeedAdmin):
    pass


@admin.register(Materialworks)
class MaterialworksAdmin(FeedAdmin):
    pass


@admin.register(Maxwell)
class MaxwellAdmin(FeedAdmin):
    pass


@admin.register(MindTheGap)
class MindTheGapAdmin(FeedAdmin):
    pass


@admin.register(PhillipJeffries)
class PhillipJeffriesAdmin(FeedAdmin):
    pass


@admin.register(Phillips)
class PhillipsAdmin(FeedAdmin):
    pass


@admin.register(Pindler)
class PindlerAdmin(FeedAdmin):
    pass


@admin.register(Port68)
class Port68Admin(FeedAdmin):
    pass


@admin.register(PremierPrints)
class PremierPrintsAdmin(FeedAdmin):
    pass


@admin.register(Scalamandre)
class ScalamandreAdmin(FeedAdmin):
    pass


@admin.register(Schumacher)
class SchumacherAdmin(FeedAdmin):
    pass


@admin.register(Seabrook)
class SeabrookAdmin(FeedAdmin):
    pass


@admin.register(StarkStudio)
class StarkStudioAdmin(FeedAdmin):
    pass


@admin.register(Stout)
class StoutAdmin(FeedAdmin):
    pass


@admin.register(Surya)
class SuryaAdmin(FeedAdmin):
    pass


@admin.register(TresTintas)
class TresTintasAdmin(FeedAdmin):
    pass


@admin.register(York)
class YorkAdmin(FeedAdmin):
    pass


@admin.register(Zoffany)
class ZoffanyAdmin(FeedAdmin):
    pass
