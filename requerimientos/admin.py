from django.contrib import admin

from requerimientos.models import RequirementDetail, Requirement, \
    RequirementApproval


# Register your models here.
class RequirementDetailRowAdmin(admin.TabularInline):
    model = RequirementDetail


class RequirementDetailsAdmin(admin.ModelAdmin):
    inlines = [RequirementDetailRowAdmin]


admin.site.register(Requirement, RequirementDetailsAdmin)
admin.site.register(RequirementApproval)
