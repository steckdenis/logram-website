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
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from pyv4.general.models import Profile
from pyv4.forum.models import Topic

# Create your models here.

class Category(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    desc = models.TextField(_('Description'))
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Categorie')
        verbose_name_plural = _('Categories')

class News(models.Model):
    author = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    category = models.ForeignKey(Category, verbose_name=_('Catégorie'))
    
    title = models.CharField(_('Titre'), max_length=200)
    intro = models.TextField(_('Introduction (affichée sur la page d\'accueil)'))
    body = models.TextField(_('Corps'))
    
    published = models.BooleanField(_('Publiée'))
    to_validate = models.BooleanField(_('En attente de validation'))
    is_private = models.BooleanField(_('News privée'))
    rejected = models.BooleanField(_('Refusée'))
    rejected_reason = models.CharField(_('Si refus, raison de celui-ci'), max_length=200, blank=True, null=True)
    
    date_created = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_published = models.DateTimeField(_('Date de publication'), blank=True, null=True)
    date_modified = models.DateTimeField(_('Date de dernière mise à jour'), auto_now=True)
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet de commentaire'), blank=True, null=True)
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        verbose_name = _('Nouvelle')
        verbose_name_plural = _('Nouvelles')
        
        permissions = (
            ('view_unpublished', 'View unpublished'),
        )