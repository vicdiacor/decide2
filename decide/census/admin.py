from django.contrib import admin

from .models import Census, ParentGroup, Request


class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id', 'adscripcion')
    list_filter = ('voting_id', 'adscripcion')

    search_fields = ('voter_id', )

class ParentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'isPublic')
    list_filter = ('name', 'isPublic')

class RequestAdmin(admin.ModelAdmin):
    list_display = ('voter_id', 'group_id')
    list_filter = ('voter_id', 'group_id')

    search_fields = ('voter_id', 'group_id')

admin.site.register(Census, CensusAdmin)
admin.site.register(ParentGroup, ParentGroupAdmin)
admin.site.register(Request, RequestAdmin)
