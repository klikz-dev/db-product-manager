from django.contrib import admin

from .models import Log, API, FTP


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


class APIAdmin(admin.ModelAdmin):
    actions = None

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        else:
            return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    fields = ['brand', 'type', 'url']

    list_display = ('brand', 'type', 'url', 'updated_at', 'status')
    list_filter = ['brand', 'type', 'status']
    search_fields = ['brand', 'type', 'status']


class FTPAdmin(admin.ModelAdmin):
    actions = None

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        else:
            return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    fields = ['brand', 'type', 'url', 'port', 'username', 'password']

    list_display = ('brand', 'type', 'url', 'port', 'updated_at', 'status')
    list_filter = ['brand', 'port', 'status']
    search_fields = ['brand', 'type', 'status']


class ScheduleAdmin(admin.ModelAdmin):
    actions = None

    def get_readonly_fields(self, request, obj=None):
        return self.fields or [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fields = ['description', 'type', 'process', 'schedule']

    list_display = ('description', 'type', 'process', 'schedule')
    list_filter = ['type']
    search_fields = ['description', 'type', 'process']


admin.site.register(Log, LogAdmin)
admin.site.register(API, APIAdmin)
admin.site.register(FTP, FTPAdmin)
