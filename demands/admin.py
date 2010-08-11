# -*- coding: utf-8 -*-
#
# admin.py
# This file is part of Logram Website
#
# Copyright (C) 2010 - Denis Steckelmacher <steckdenis@logram-project.org>
#
# Logram Website is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Logram is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Logram; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA
#
from pyv4.demands.models import *
from django.contrib import admin
from django.utils.translation import gettext as _

admin.site.register(Type)
admin.site.register(Status)
admin.site.register(Priority)
admin.site.register(Demand)
admin.site.register(Relation)
admin.site.register(Attachment)
admin.site.register(Assignee)

class ComponentsInline(admin.StackedInline):
    model = Component
    extra = 1
    
class ProductVersionsInline(admin.StackedInline):
    model = ProductVersion
    extra = 1
    
class DefaultAssigneesInline(admin.StackedInline):
    model = DefaultAssignee
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVersionsInline, ComponentsInline, DefaultAssigneesInline]
    
admin.site.register(Product, ProductAdmin)

class PlatformVersionsInline(admin.StackedInline):
    model = PlatformVersion
    extra = 1
    
class PlatformAdmin(admin.ModelAdmin):
    inlines = [PlatformVersionsInline]

admin.site.register(Platform, PlatformAdmin)