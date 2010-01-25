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

# Create your models here.
class Page(models.Model):
    title = models.CharField(_('Titre'), max_length=300)
    slug = models.CharField(_('Slug'), max_length=100)   # SlugField est unique, ce que nous ne voulons pas
    lang = models.CharField(_('Langue'), max_length=2)
    identifier = models.IntegerField(_('Identificateur'), blank=True, default=0)
    
    body = models.TextField(_('Contenu'))
    
    is_protected = models.BooleanField(_('Page protégée'))
    is_private = models.BooleanField(_('Page privée (accessible uniquement au staff)'))
    
    def __unicode__(self):
        return self.title + ' | ' + self.lang
    
    class Meta:
        verbose_name = _('Page')
        verbose_name_plural = _('Pages')
        
        permissions = (
            ('private_page', 'Set a page to private'),
            ('view_private_pages', 'View private pages'),
        )

class LogEntry(models.Model):
    page = models.ForeignKey(Page, verbose_name=_('Page'))
    
    comment = models.CharField(_('Commentaire'), max_length=300)
    body = models.TextField(_('Contenu à ce moment-là'))
    
    date = models.DateTimeField(_('Date de création'), auto_now_add=True)
    
    author_user = models.ForeignKey(Profile, verbose_name=_('Auteur (utilisateur)'), blank=True, null=True)
    author_ip = models.CharField(_('Auteur (adresse IP)'), max_length=15, blank=True, null=True)