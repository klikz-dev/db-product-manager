from django.contrib import admin

from .models import Feed


class FeedAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Primary Keys', {'fields': ['mpn', 'sku',
         'upc', 'pattern', 'color', 'title', 'productId']}),
        ('Categorization', {'fields': [
         'brand', 'type', 'manufacturer', 'collection']}),
        ('Main Information', {'fields': [
         'description', 'usage', 'disclaimer']}),
        ('Additional Information', {'fields': ['width', 'length', 'height', 'size', 'dimension',
         'repeatH', 'repeatV', 'repeat', 'material', 'finish', 'care', 'specs', 'features', 'weight', 'country']}),
        ('Measurement', {'fields': ['uom', 'minimum', 'increment']}),
        ('Tagging', {'fields': ['colors', 'tags']}),
        ('Pricing', {'fields': ['cost', 'msrp', 'map']}),
        ('Availability', {'fields': [
         'statusP', 'statusS', 'stockP', 'stockS']}),
        ('Assets', {'fields': ['thumbnail', 'roomsets']}),
    ]

    list_display = ('mpn', 'sku', 'upc', 'pattern', 'color', 'productId', 'brand', 'type',
                    'manufacturer', 'collection', 'cost', 'msrp', 'map', 'statusP', 'statusS', 'stockP', 'stockS')

    list_filter = ['brand', 'type', 'manufacturer',
                   'uom', 'statusP', 'statusS']

    search_fields = ['mpn', 'sku', 'productId', 'pattern', 'color']


admin.site.register(Feed, FeedAdmin)
