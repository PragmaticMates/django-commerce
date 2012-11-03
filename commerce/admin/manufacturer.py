from django.contrib import admin

from commerce.models.manufacturer import Manufacturer


class ManufacturerAdmin(admin.ModelAdmin):
    exclude = ('created', 'modified')

admin.site.register(Manufacturer, ManufacturerAdmin)
