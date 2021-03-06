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

urlpatterns = patterns('pyv4.users.views',
    (r'^1-(?P<user_id>\d+)\.html$', 'view'),
    (r'^2-(?P<page>\d+)\.html$', 'list'),
    (r'^3\.html$', 'staff'),
    (r'^4-(?P<page>\d+)\.html$', 'online'),
    (r'^5\.html$', 'opts_index'),
    (r'^5-1\.html$', 'opts_profile'),
    (r'^5-2\.html$', 'opts_pseudo'),
    (r'^5-3\.html$', 'opts_mdp'),
    (r'^5-4\.html$', 'opts_design'),
)