# -*- coding: utf-8 -*-
#
# urls.py
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
from django.conf.urls.defaults import *

urlpatterns = patterns('pyv4.wiki.views',
    #routes "wiki-...", ou "wiki-" n'est pas mis
    (r'^1\.html$', 'randompage'),
    (r'^2-(?P<page>\d+)\.html$', 'changes'),
    (r'^3-(?P<page_id>\d+)-(?P<identifier>\d+)-(?P<slug>[a-z0-9_-]+)\.html$', 'edit'),
    (r'^4-(?P<page_id>\d+)\.html$', 'history'),
    (r'^5-(?P<page_id>\d+)\.html$', 'toggle_protect'),
    (r'^6-(?P<page_id>\d+)\.html$', 'toggle_private'),
    (r'^7-(?P<change_id>\d+)\.html$', 'pagedate'),
    (r'^8-(?P<change_id>\d+)\.html$', 'cancelchange'),
    
    # Page sans numéros, à la fin, cer elles récupèrent tout ce qui "reste"
    (r'^(?P<slug>[a-z0-9_-]+)\.html$', 'viewpage'),
    (r'^(?P<slug>[a-z0-9_-]+)\.(?P<lang>[a-z]{2})\.html$', 'viewpagelang'),
)