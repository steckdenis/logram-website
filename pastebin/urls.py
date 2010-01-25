# -*- coding: utf-8 -*-
#
# urls.py
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
from django.conf.urls.defaults import *

urlpatterns = patterns('pyv4.pastebin.views',
    (r'^1\.html$', 'index'),
    (r'^2\.html$', 'save'),
    (r'^3-(?P<uniqid>\w+)\.html$', 'view_paste'),
    (r'^4-(?P<uniqid>\w+)\.html$', 'download'),
    (r'^5-(?P<uniqid>\w+)\.html$', 'modif'),
    (r'^7-(?P<uniqid>\w+)\.html$', 'alert'),
    (r'^9\.html$', 'my_pastes')
)

urlpatterns += patterns('pyv4.forum.views',
    (r'^8-(?P<alert_id>\d+)\.html$', 'rmalert')
)