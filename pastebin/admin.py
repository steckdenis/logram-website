# -*- coding: utf-8 -*-
#
# admin.py
# This file is part of Logram Website
#
# Copyright (C) 2009-2010 - Takahashi Keisuke <keisuke@logram-project.org>
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
from pyv4.pastebin.models import *
from django.contrib import admin
from django.utils.translation import gettext as _

class PasteAdmin(admin.ModelAdmin):
    list_display = ('uniqid', 'author', 'created', 'format', 'ended', 'modified', 'author_m')
    list_filter = ['created', 'ended']
    search_fields = ['uniqid']

admin.site.register(Pastebin, PasteAdmin)