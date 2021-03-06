# -*- coding: utf-8 -*-
#
# admin.py
# This file is part of Logram Website
#
# Copyright (C) 2009 - Denis Steckelmacher <steckdenis@logram-project.org>
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
from pyv4.general.models import Profile, Style, GlobalMessage
from django.contrib import admin
from django.utils.translation import gettext as _

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username',)
    fields = ['uname', 'main_group_name', 'main_group', 'website', 'quote', 'avatar', 'pperso', 'sign', 'point']

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Style)
admin.site.register(GlobalMessage)