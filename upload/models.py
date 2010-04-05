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

from pyv4.general.functions import *

d_types = [
    (D_TYPE_FORUM, _('Fichiers en rapport avec le forum')),
    (D_TYPE_WIKI, _('Fichiers utilisés sur les pages de documentations')),
    (D_TYPE_DEMANDS, _('Fichiers utilisés avec les demandes')),
]

# Create your models here.
class Directory(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    quota = models.IntegerField(_('Quota (octets)'), default=0)
    used = models.IntegerField(_('Octets utilisés'), default=0)
    
    user = models.ForeignKey(User, verbose_name=_('Propriétaire'))
    parent = models.ForeignKey('self', verbose_name=_('Dossier parent'), blank=True, null=True)

    sha1hash = models.CharField(_('Hash utilisé pour la création du dossier'), max_length=40, blank=True, null=True)
    type = models.IntegerField(_('Type de dossier'), choices=d_types, blank=True, null=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Dossier')
        verbose_name_plural = _('Dossiers')
        
        permissions = (
            ('ignore_quota', 'Ignore quota'),
            ('ingore_extensions', 'Ignore extensions'),
        )

class File(models.Model):
    name = models.CharField(_('Nom'), max_length=32)
    path = models.FileField(_('Chemin d\'accès'), upload_to='uploads/%Y/%m/%d/%H%M%S')
    directory = models.ForeignKey(Directory, verbose_name=_('Dossier parent'))
    size = models.IntegerField(_('Taille'))
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Fichier')
        verbose_name_plural = _('Fichiers')