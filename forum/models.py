# -*- coding: utf-8 -*-
#
# models.py
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
from django.db import models
from django.utils.translation import gettext_lazy as _

from pyv4.general.models import Profile
from pyv4.pastebin.models import Pastebin
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.CharField(_('Description'), max_length=400)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Categorie')
        verbose_name_plural = _('Categories')

class Forum(models.Model):
    category = models.ForeignKey(Category, verbose_name=_('Catégorie'))
    
    name = models.CharField(_('Nom en français'), max_length=200)
    description = models.CharField(_('Description en français'), max_length=400)
    
    num_topics = models.IntegerField(_('Nombre de sujets'))
    num_posts = models.IntegerField(_('Nombre de posts'))
    
    last_topic = models.ForeignKey('Topic', verbose_name=_('Dernier sujet dans lequel on posté'), related_name='f', blank=True, null=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Forum')
        verbose_name_plural = _('Forum')

class Poll(models.Model):
    question = models.CharField(_('Question'), max_length=200)
    pub_date = models.DateTimeField(_('Date de publication'), auto_now=True)
    topic = models.ForeignKey('Topic', verbose_name=_('Sujet'), related_name='polls')
    
    def __unicode__(self):
        return self.question
        
    class Meta:
        verbose_name = _('Sondage')
        verbose_name_plural = _('Sondages')
        
        permissions = (
            ('poll_on_all_topics', 'Add a poll on all topics'),
        )
    
class Choice(models.Model):
    poll = models.ForeignKey(Poll, verbose_name=_('Sondage'))
    choice = models.CharField(_('Choix'), max_length=200)
    votes = models.IntegerField(_('Votes'))
    
    def __unicode__(self):
        return self.choice
        
    class Meta:
        verbose_name = _('Choix')
        verbose_name_plural = _('Choix')
        
class Topic(models.Model):
    forum = models.ForeignKey(Forum, verbose_name=_('Forum'), blank=True, null=True)
    author = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    lang = models.CharField(_('Code ISO de la langue'), max_length=2)
    
    title = models.CharField(_('Titre'), max_length=150)
    subtitle = models.CharField(_('Sous-titre'), max_length=200)
    
    last_post = models.ForeignKey('Post', verbose_name=_('Dernier message'), related_name='t', blank=True, null=True)
    last_post_page = models.IntegerField(_('Page du dernier post dans le sujet'))
    num_posts = models.IntegerField(_('Nombre de messages'))
    
    stick = models.BooleanField(_('Post-it'))
    closed = models.BooleanField(_('Fermé'))
    resolved = models.BooleanField(_('Résolu'))
    
    poll = models.ForeignKey(Poll, verbose_name=_('Sondage lié'), blank=True, null=True, related_name='tp')
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        verbose_name = _('Sujet')
        verbose_name_plural = _('Sujets')

class Post(models.Model):
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet'))
    author = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    
    has_helped = models.BooleanField(_('A aidé l\'auteur du sujet'))
    date_created = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_modified = models.DateTimeField(_('Date de dernière mise à jour'), auto_now=True)
    
    contents = models.TextField(_('Contenu'))
    
    def __unicode__(self):
        # On ne s'en sert pas, normalement
        return 'post'
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        
        permissions = (
            ('edit_all_posts', 'Edit all posts'),
        )

class History(models.Model):
    post = models.ForeignKey(Post, verbose_name=_('Post'))
    author = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    
    date = models.DateTimeField(_('Date de création'), auto_now_add=True)
    comment = models.CharField(_('Commentaire'), max_length=200)
    
    def __unicode__(self):
        return self.comment
    
    class Meta:
        verbose_name = _('Historique de message')
        verbose_name_plural = _('Historiques de message')

class UserTopic(models.Model):
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet'))
    user = models.ForeignKey(Profile, verbose_name=_('Utilisateur'))
    
    last_read_post_page = models.IntegerField(_('Page du dernier post lu'))
    last_read_post = models.ForeignKey(Post, verbose_name=_('Dernier message lu'))

class Bookmark(models.Model):
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet'))
    user = models.ForeignKey(User, verbose_name=_('Utilisateur'))

class Alert(models.Model):
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet'), blank=True, null=True)
    paste = models.ForeignKey(Pastebin, verbose_name=_('Paste'), related_name='paste', blank=True, null=True)
    author = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    
    comment = models.CharField(_('Commentaire'), max_length=400)
    
    def __unicode__(self):
        return self.comment
    
    class Meta:
        verbose_name = _('Alerte')
        verbose_name_plural = _('Alertes')
        
        permissions = (
            ('view_alerts', 'View alerts'),
        )