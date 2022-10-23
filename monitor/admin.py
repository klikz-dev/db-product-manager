from django.contrib import admin
from rangefilter.filters import DateRangeFilter
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Log, Profit


class LogAdmin(admin.ModelAdmin):
    actions = None

    def get_readonly_fields(self, request, obj=None):
        return self.fields or [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fields = ['source', 'date', 'level', 'message']

    list_display = ('source', 'date', 'level', 'message')
    list_filter = ['source', 'date', 'level']
    search_fields = ['source', 'date', 'message', 'level']


class ProfitResource(resources.ModelResource):
    class Meta:
        model = Profit
        fields = ('po', 'type', 'cost', 'price', 'date')


class ProfitAdmin(ImportExportModelAdmin):
    actions = None

    def get_readonly_fields(self, request, obj=None):
        return self.fields or [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    resource_classes = [ProfitResource]

    list_display = ('po', 'type', 'cost', 'price', 'date')
    list_filter = (
        ('date', DateRangeFilter),
        'type'
    )
    search_fields = ['po']


admin.site.register(Log, LogAdmin)
admin.site.register(Profit, ProfitAdmin)
