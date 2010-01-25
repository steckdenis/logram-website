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
from pyv4.news.models import News, Category
from django.contrib import admin
from django.utils.translation import gettext as _

class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date_published', 'date_modified', 'published', 'rejected', 'to_validate')
    list_filter = ['date_published', 'to_validate']
    search_fields = ['title']
    fieldsets = [
        (None, {'fields': ['author', 'category', 'date_published', 'topic']}),
        ('Contenu de la nouvelle', {'fields': ['title', 'intro', 'body']}),
        ('Publication', {'fields': ['to_validate', 'published', 'rejected', 'rejected_reason']}),
    ]

admin.site.register(News, NewsAdmin)
admin.site.register(Category)