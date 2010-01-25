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

urlpatterns = patterns('pyv4.demands.views',
    #routes "demands-...", ou "demands-" n'est pas mis
    (r'^1\.html', 'index'),
    (r'^2-(?P<action>\d+)-(?P<type_or_demand_id>\d+)\.html$', 'post'),
    (r'^3-(?P<type_id>\d+)-(?P<status_id>\d+)-(?P<order_by>[a-z]+)-(?P<page>\d+)\.html', 'mlist'),
    (r'^5-(?P<demand_id>\d+)-(?P<page>\d+)\.html$', 'view'),
    (r'^6-(?P<action>\d+)-(?P<demand_id>\d+)\.html$', 'note'),
    (r'^7-(?P<demand_id>\d+)\.html$', 'take'),
    (r'^8-(?P<child_type>\d+)-(?P<demand_id>\d+)\.html$', 'add_child'),
    (r'^9-(?P<child_type>\d+)-(?P<demand_id>\d+)-(?P<child_id>\d+)\.html$', 'remove_child'),
)