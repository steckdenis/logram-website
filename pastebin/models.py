# -*- coding: utf-8 -*-
#
# models.py
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

from django.db import models
from pyv4.general.models import Profile
from pyv4.general.functions import pygments_format
from django.contrib.auth.models import User

from django.utils.translation import gettext_lazy as _

class Pastebin(models.Model):
    title = models.CharField(_('Titre'), max_length=200)
    author = models.ForeignKey(Profile, related_name=_('Auteur'), blank=True, null=True)
    format = models.CharField(_('Format'), max_length=15)
    created = models.DateTimeField(_('Date de creation'), auto_now_add=True)
    contents = models.TextField(_('Contenu'))
    ended = models.DateTimeField(_('Date de fin'))
    uniqid = models.CharField(_('Unique ID'), max_length=150)
    
    author_m = models.ForeignKey(Profile, related_name=_('Auteur Modifié'), null=True)
    modified = models.DateTimeField(_('Date de modification'), auto_now=True,  null=True)
    contents_m = models.TextField(_('Contenu Modifié'), blank=True)
    
    def __unicode__(self):
        return title
        
    def format_str(self):
        return pygments_format.get(self.format, _('Format inconnu'))
    
    class Meta:
        verbose_name = _('Pastebin')
        verbose_name_plural = _('Pastebin')
        
        permissions = (
            ('view_alerts', 'View alerts'),
            ('edit_all_pastes', 'Edit all pastes'),
        )
