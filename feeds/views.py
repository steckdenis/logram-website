# -*- coding: utf-8 -*-
#
# views.py
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

from django.contrib.syndication.views import Feed
from django.utils.cache import cache
from django.utils.translation import gettext as _

from pyv4.news.models import News
from pyv4.demands.models import Demand
from pyv4.forum.models import Topic
from pyv4.wiki.models import Page
from pyv4.packages.models import Package
from pyv4.general.functions import *
from pyv4.forum.views import return_page


class LatestNews(Feed):
    title = _("Logram-Project: News")
    link = "/"
    description = _("Dix dernières nouvelles")
    
    def items(self):
        # Si le cache du rss existe, on l'utilise
        NList = cache.get('feeds_news', False)
        if not NList:
            NList = News.objects.select_related('category', 'author') \
                    .order_by('-date_published') \
                    .filter(published=True,is_private=0)[:10]
            # Ecris le cache du RSS news de 30min
            cache.set('feeds_news', NList, 30*60)
        return NList
    
    
    def item_link(self, News):
        return '/news-2-%d-1-%s.html' % (int(News.id), slugify(News.title))
    
    
class LatestJournal(Feed):
    title = _("Logram-Project: Journal")
    link = "/"
    description = _("Dix derniers journaux")
    
    def items(self):
        # Si le cache du rss existe, on l'utilise
        JList = cache.get('feeds_journal', False)
        if not JList:
            JList = News.objects.select_related('category', 'author') \
                    .order_by('-date_published') \
                    .filter(published=True,is_private=1)[:10]
            # Ecris le cache du RSS jounral de 30min
            cache.set('feeds_journal', JList, 30*60)
        return JList
    
    
    def item_link(self, News):
        return '/news-2-%d-1-%s.html' % (int(News.id), slugify(News.title))
    

class LatestAsk(Feed):
    title = _("Logram-Project: Demandes")
    link = "/"
    description = _("Dix dernières demandes")
    
    def items(self):
        # Si le cache du rss existe, on l'utilise
        DList = cache.get('feeds_ask', False)
        if not DList:
            DList = Demand.objects.select_related('author', 'd_type').order_by('-created_at')[:10]
            
            # Ecris le cache du RSS des demandes de 30min
            cache.set('feeds_ask', DList, 30*60)
        return DList
    
    
    def item_link(self, Demand):
        return '/demand-5-%d-1.html' % int(Demand.id)
    
    
    
class LatestMessage(Feed):
    title = _("Logram-Project: Messages")
    link = "/"
    description = _("Dix derniers messages")
    
    def items(self):
        # Si le cache du rss existe, on l'utilise
        MList = cache.get('feeds_msg', False)
        if not MList:
            MList = Topic.objects.select_related('last_post', 'last_post__author') \
                    .extra(select={'date_created': 'forum_post.date_created', 'contents': 'forum_post.contents'}) \
                    .order_by('-last_post__date_created')[:10]
            
            # Ecris le cache du RSS Message du forum de 30min
            cache.set('feeds_msg', MList, 30*60)
        return MList
    
    
    def item_link(self, Topic):
        return '/' + return_page(Topic, None)

def index(request):
    return tpl('feeds/index.html',"", request)


class LatestWiki(Feed):
    title = _("Logram-Project: Wiki")
    link = "/"
    description = _("Dix dernières pages de wiki")
    
    def items(self):
        # Si le cache du rss existe, on l'utilise
        WList = cache.get('feeds_wiki', False)
        if not WList:
            WList = Page.objects.filter(is_private=False).order_by('-id')[:10]
            
            # Ecris le cache du RSS Wiki de 30min
            cache.set('feeds_msg', WList, 30*60)
        return WList
    
    
    def item_link(self, Page):
        return '/wiki-%s.%s.html' % (Page.slug, Page.lang)

		
class LatestPackages(Feed):
    title = _("Logram-Project: Packages")
    link = "/"
    description = _("Dix derniers paquets disponibles")
    
    def items(self):
        # Si le cache du rss existe, on l'utilise
        PList = cache.get('feeds_packages', False)
        if not PList:
            PList = Package.objects.select_related('arch').order_by('-date')[:10]
            
            # Ecris le cache du RSS Packages de 30min
            cache.set('feeds_packages', PList, 30*60)
        return PList
    
    
    def item_link(self, Package):
        return '/packages-4-%d.html' % (Package.id)
