from misc.models import Config, YotpoEmail, YotpoSMS
from django.contrib import admin


class YotpoEmailAdmin(admin.ModelAdmin):
    fields = ["email", ]

    list_display = ("email", )

    search_fields = ["email", ]


class YotpoSMSAdmin(admin.ModelAdmin):
    fields = ["email", ]

    list_display = ("email", )

    search_fields = ["email", ]


class ConfigAdmin(admin.ModelAdmin):
    fields = ["yotpo_email_marker", 'yotpo_sms_marker', 'last_processed_order', 'last_processed_sample']

    list_display = ("yotpo_email_marker", 'yotpo_sms_marker', 'last_processed_order', 'last_processed_sample')

    search_fields = ["yotpo_email_marker", 'yotpo_sms_marker', 'last_processed_order', 'last_processed_sample']


admin.site.register(YotpoEmail, YotpoEmailAdmin)
admin.site.register(YotpoSMS, YotpoSMSAdmin)
admin.site.register(Config, ConfigAdmin)
