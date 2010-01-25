# -*- coding: utf-8 -*-
#
# urls.py
# This file is part of Logram Website
#
# Copyright (C) 2009 - Keisuke
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

from pyv4.feeds.views import LatestNews, LatestJournal, LatestAsk, LatestMessage, LatestWiki, LatestPackages

feeds = {
    'latestnews': LatestNews,
    'latestjournal': LatestJournal,
    'latestask': LatestAsk,
    'latestmsg': LatestMessage,
    'latestwiki': LatestWiki,
	'latestpackages': LatestPackages
}


urlpatterns = patterns('',
    (r'^$', 'pyv4.feeds.views.index'),
    (r'^(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),

)