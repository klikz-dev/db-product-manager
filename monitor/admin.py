from django.contrib import admin

from .models import Log


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


admin.site.register(Log, LogAdmin)
