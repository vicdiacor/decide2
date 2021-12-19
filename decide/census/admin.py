from django.contrib import admin

from .models import Census, ParentGroup


class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id', 'adscripcion')
    list_filter = ('voting_id', 'adscripcion')

    search_fields = ('voter_id', )

class ParentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'isPublic')
    list_filter = ('name', 'isPublic')


admin.site.register(Census, CensusAdmin)
admin.site.register(ParentGroup, ParentGroupAdmin)
