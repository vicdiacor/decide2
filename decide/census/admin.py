from django.contrib import admin
from django.contrib.auth.models import User
from .models import Census, ParentGroup, Request, RequestStatus



class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id', 'adscripcion')
    list_filter = ('voting_id', 'adscripcion')

    search_fields = ('voter_id', )

class ParentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'isPublic')
    list_filter = ('name', 'isPublic')

def accept(modeladmin, request, queryset):
    for v in queryset.all():
        voter = User.objects.get(pk=v.voter_id)
        group = ParentGroup.objects.get(pk=v.group_id)
        #Guardar el group en el voter y guardarlo
        v.status = RequestStatus.ACCEPTED        
        v.save()

def reject(modeladmin, request, queryset):
    for v in queryset.all():
        v.status = RequestStatus.REJECTED        
        v.save()

class RequestAdmin(admin.ModelAdmin):
    list_display = ('voter_id', 'group_id')
    list_filter = ('voter_id', 'group_id')

    search_fields = ('voter_id', 'group_id')

           
                    

admin.site.register(Census, CensusAdmin)
admin.site.register(ParentGroup, ParentGroupAdmin)
admin.site.register(Request, RequestAdmin)


