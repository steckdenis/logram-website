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

urlpatterns = patterns('pyv4.upload.views',
    #routes "news-...", ou "news-" n'est pas mis
    (r'^1-(?P<dir_id>\d+)\.html$', 'viewdir'),
    (r'^2-(?P<dir_id>\d+).html$', 'upload'),
    (r'^3-(?P<file_id>\d+)\.html$', 'delete'),
    (r'^4-(?P<hash>[0-9a-f]+)-(?P<parent_type>\d+)-(?P<quota>\d+)-(?P<uniqid>\d+)\.html$', 'newdir'),
)