from django.contrib import admin
from django.db.models import get_models, get_app
from django import forms

from schedule.models import SchoolQuicklink, School, SchoolAlias

for model in get_models(get_app('schedule')):
    if model == SchoolQuicklink or model == SchoolAlias:
        continue
    admin.site.register(model)

class SchoolQuicklinkAdminForm(forms.ModelForm):
    domain = forms.ModelChoiceField(queryset=School.objects.order_by('name'))

    class Meta:
        model = SchoolQuicklink

class SchoolQuickLinkAdmin(admin.ModelAdmin):
    form = SchoolQuicklinkAdminForm

class SchoolAliasAdminForm(forms.ModelForm):
    domain = forms.ModelChoiceField(queryset=School.objects.order_by('name'))

    class Meta:
        model = SchoolAlias

class SchoolAliasAdmin(admin.ModelAdmin):
    form = SchoolAliasAdminForm

admin.site.register(SchoolAlias, SchoolAliasAdmin)
