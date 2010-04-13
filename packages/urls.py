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

urlpatterns = patterns('pyv4.packages.views',
    #routes "packages-...", où "packages-" n'est pas mis
    # (r'^2-(?P<page>\d+)\.html$', 'changes'),
    (r'^1\.html$', 'home'),
    (r'^2-(?P<distro_id>\d+)\.html$', 'sections'),
    (r'^3-(?P<distro_id>\d+)-(?P<section_id>\d+)\.html$', 'listsection'),
    
    (r'^4-(?P<package_id>\d+)\.html$', 'showpackage'),
    (r'^6-(?P<package_id>\d+)\.html$', 'viewmirrors'),
    (r'^7-(?P<package_id>\d+)\.html$', 'viewfiles'),
    (r'^8-(?P<package_id>\d+)\.html$', 'changelog'),
    (r'^9-(?P<source_id>\d+)\.html$', 'viewsource'),
    
    (r'^5\.html$', 'search'),
)