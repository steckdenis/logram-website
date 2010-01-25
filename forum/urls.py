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

urlpatterns = patterns('pyv4.forum.views',
    #routes "forum-...", ou "forum-" n'est pas mis
    (r'^1-(?P<forum_id>\d+)-(?P<page>\d+)-[a-z0-9_-]+\.html$', 'viewforum'),
    (r'^2-(?P<topic_id>\d+)-(?P<page>\d+)-[a-z0-9_-]+\.html$', 'viewtopic'),
    (r'^3-(?P<topic_id>\d+)\.html$', 'post'),
    (r'^4-(?P<post_id>\d+)\.html$', 'edit'),
    (r'^5-(?P<post_id>\d+)\.html$', 'toggle_helped'),
    (r'^6-(?P<forum_id>\d+)\.html$', 'newtopic'),
    (r'^7-(?P<forum_id>\d+)-(?P<page>\d+)\.html$', 'unread'),
    (r'^8-(?P<forum_id>\d+)-(?P<page>\d+)\.html$', 'mytopics'),
    (r'^9-(?P<forum_id>\d+)-(?P<page>\d+)\.html$', 'visited'),
    (r'^10-(?P<forum_id>\d+)-(?P<page>\d+)\.html$', 'posted'),
    (r'^11-(?P<topic_id>\d+)\.html$', 'toggle_solve'),
    (r'^12-(?P<topic_id>\d+)\.html$', 'alert'),
    (r'^13-(?P<topic_id>\d+)\.html$', 'moderate'),
    (r'^14-(?P<alert_id>\d+)\.html$', 'rmalert'),
    (r'^15-(?P<topic_id>\d+)\.html$', 'addpoll'),
    (r'^16-(?P<poll_id>\d+)\.html$', 'vote'),
    (r'^17-(?P<topic_id>\d+)\.html$', 'toggle_watch'),
)