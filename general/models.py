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
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext_lazy as _, gettext

from pyv4.upload.models import Directory

# Create your models here.
class Profile(models.Model):
    user = models.ForeignKey(User, verbose_name=_('Utilisateur'))
    main_group = models.ForeignKey(Group, verbose_name=_('Groupe principal'))

    uname = models.CharField(_('Nom de l\'utilisateur'), max_length=200)
    main_group_name = models.CharField(_('Nom du groupe principal'), max_length=64)
    
    website = models.CharField(_('Site web'), max_length=200, blank=True, null=True)
    quote = models.CharField(_('Citation'), max_length=50, blank=True, null=True)
    pperso = models.TextField(_('Texte personnel'), blank=True, null=True)
    avatar = models.CharField(_('Avatar'), max_length=256, blank=True, null=True)
    sign = models.TextField(_('Signature'), blank=True, null=True)
    style = models.CharField(_('Design'), max_length=256)
    
    point = models.IntegerField(_('Nombre de points'), default=0)
    show_email = models.BooleanField(_('Afficher l\'adresse e-mail'), default=True)
    main_dir = models.ForeignKey(Directory, verbose_name=_('Dossier principal de l\'utilisateur'))
    
    def group(self):
        return gettext(self.main_group)
    
    def __unicode__(self):
        return self.uname

    def username(self):
        return self.uname
    
    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

class Style(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    url = models.CharField(_('Url'), max_length=200)
    
    def __unicode__(self):
        return self.name