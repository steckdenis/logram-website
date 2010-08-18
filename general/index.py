# -*- coding: utf-8 -*-
#
# index.py
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
from djapian import space, Indexer, CompositeIndexer

from pyv4.forum.models import Post
from pyv4.wiki.models import Page
from pyv4.news.models import News
from pyv4.demands.models import Demand

class PostIndexer(Indexer):
    fields = ['contents']
    tags = [
        ('author', 'author'),
        ('date_created', 'date_created')
    ]

class NewsIndexer(Indexer):
    fields = ['title', 'intro', 'body']
    tags = [
        ('title', 'title'),
        ('author', 'author'),
        ('date_published', 'date_published')
    ]

class WikiIndexer(Indexer):
    fields = ['body']
    tags = [
        ('title', 'title'),
        ('lang', 'lang')
    ]
    
class DemandIndexer(Indexer):
    fields = ['title', 'content']
    tags = [
        ('title', 'title'),
        ('content', 'content')
    ]

space.add_index(Post, PostIndexer, attach_as='indexer')
space.add_index(Page, WikiIndexer, attach_as='indexer')
space.add_index(News, NewsIndexer, attach_as='indexer')
space.add_index(Demand, DemandIndexer, attach_as='indexer')

complete_indexer = CompositeIndexer(Post.indexer, Page.indexer, News.indexer, Demand.indexer)