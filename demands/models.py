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
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_unicode

from pyv4.general.models import Profile
from pyv4.forum.models import Topic
from pyv4.packages.models import Arch

ASSIGNEE_TYPE = (
    (0, _('Utilisateur inscrit')),
    (1, _('Adresse e-mail')),
    (2, _('Url sur un autre bugtracker')),
)

RELATION_TYPE = (
    (0, _('La demande principale depend de la secondaire')),
    (1, _('Les demandes principales et secondaires sont liees')),
    (2, _('Les demandes principales et secondaires sont des duplicatas')),
)

class Type(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    color = models.CharField(_('Couleur'), max_length=6)
    icon = models.ImageField(_('Icône'), upload_to='uploads/%Y/%m/%d/%H%M%S')
    
    def color_vector(self):
        s = self.color
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        
        return (r, g, b)
        
    def vector_color(self, vec):
        return '%2X%2X%2X' % vec
        
    def neg_color(self, vec, amount):
        r = int(float(255 - vec[0]) * amount)
        g = int(float(255 - vec[1]) * amount)
        b = int(float(255 - vec[2]) * amount)
        
        return (r, g, b)
        
    def lightcolor(self):
        vec = self.color_vector()
        vec2 = self.neg_color(vec, 0.7)
        
        r = vec[0] + vec2[0]
        g = vec[1] + vec2[1]
        b = vec[2] + vec2[2]
        
        return self.vector_color((r, g, b))
        
    def darkcolor(self):
        vec = self.color_vector()
        vec2 = self.neg_color(vec, 0.5)
        
        r = vec[0] - vec2[0]
        g = vec[1] - vec2[1]
        b = vec[2] - vec2[2]
        
        return self.vector_color((r, g, b))
        
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Type')
        verbose_name_plural = _('Types')
    
class Status(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    closed = models.BooleanField(_('Demande fermée'))
    default = models.BooleanField(_('Type par défaut'))
    resolved = models.BooleanField(_('Demande résolue'))

    def __unicode__(self):
        return force_unicode(self.name)

    class Meta:
        verbose_name = _('Status')
        verbose_name_plural = _('Status')

class Product(models.Model):
    name = models.CharField(_('Nom'), max_length=64)
    title = models.CharField(_('Titre'), max_length=200)
    description = models.TextField(_('Description'))
    
    def __unicode__(self):
        return self.title + ' (' + self.name + ')'
        
    class Meta:
        verbose_name = _('Produit')
        verbose_name_plural = _('Produits')
        
class Component(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    product = models.ForeignKey(Product, verbose_name=_('Produit'))
    
    def __unicode__(self):
        return self.name
        
    class Meta:
        verbose_name = _('Composant')
        verbose_name_plural = _('Composants')
        
class DefaultAssignee(models.Model):
    type = models.IntegerField(_('Type'), choices=ASSIGNEE_TYPE)
    user = models.ForeignKey(Profile, verbose_name=_('Utilisateur'), blank=True, null=True)
    value = models.CharField(_('Url ou adresse e-mail'), max_length=256)
    product = models.ForeignKey(Product, verbose_name=_('Produit'))
    
    def __unicode__(self):
        if self.type == 0:
            return self.user.uname
        else:
            return self.value
            
    class Meta:
        verbose_name = _('CC par defaut')
        verbose_name_plural = _('CC par defaut')

class ProductVersion(models.Model):
    name = models.CharField(_('Texte de la version'), max_length=64)
    product = models.ForeignKey(Product, verbose_name=_('Produit'))
    
    old = models.BooleanField(_('Version périmée'))
    future = models.BooleanField(_('Version future'))
    
    def __unicode__(self):
        return self.product.name + ' ' + self.name
        
    class Meta:
        verbose_name = _('Version (produit)')
        verbose_name_plural = _('Versions (produit)')
        
class Platform(models.Model):
    name = models.CharField(_('Nom'), max_length=64)
    
    def __unicode__(self):
        return self.name
        
    class Meta:
        verbose_name = _('Plateforme')
        verbose_name_plural = _('Plateformes')
        
class PlatformVersion(models.Model):
    name = models.CharField(_('Texte de la version'), max_length=64)
    platform = models.ForeignKey(Platform, verbose_name=_('Plateforme'))
    
    def __unicode__(self):
        return self.platform.name + ' ' + self.name
    
    class Meta:
        verbose_name = _('Version (plateforme)')
        verbose_name_plural = _('Version (plateforme)')
        
class Priority(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    priority = models.IntegerField(_('Pourcentage de priorité'))
    default = models.BooleanField(_('Priorité par défaut'))

    def red(self):
        # Niveau de rouge de la couleur
        r = self.priority - 50
        if r < 0: return 0

        # 0 < r <= 50, passer à l'échelle 0 < r <= 256
        return r * 256 / 50

    def blue(self):
        # Niveau de bleu de la couleur
        r = 50 - self.priority
        if r > 50 or r < 0: return 0

        # 0 < r <= 50, passer à l'échelle 0 < r <= 256
        return r * 256 / 50

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Priorite')
        verbose_name_plural = _('Priorites')
        
class Demand(models.Model):
    title = models.CharField(_('Titre'), max_length=200)
    content = models.TextField(_('Contenu'))
    done = models.IntegerField(_('Pourcentage complété'))
    reporter = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    type = models.ForeignKey(Type, verbose_name=_('Type de demande'))
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet'))
    
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date de mise à jour'), auto_now=True)
    
    product = models.ForeignKey(Product, verbose_name=_('Produit'))
    component = models.ForeignKey(Component, verbose_name=_('Composant'))
    product_version = models.ForeignKey(ProductVersion, verbose_name=_('Version du produit'))
    fixed_in = models.ForeignKey(ProductVersion, blank=True, null=True, related_name='fixes', verbose_name=_('Fixé dans la version'))
    
    platform = models.ForeignKey(Platform, verbose_name=_('Plateforme'))
    platform_version = models.ForeignKey(PlatformVersion, verbose_name=_('Version de la plateforme'))
    
    architecture = models.ForeignKey(Arch, verbose_name=_('Architecture'))
    status = models.ForeignKey(Status, verbose_name=_('Status'))
    priority = models.ForeignKey(Priority, verbose_name=_('Priorité'))
    
    def __unicode__(self):
        return self.title
        
    class Meta:
        verbose_name = _('Demande')
        verbose_name_plural = _('Demandes')
        
class Relation(models.Model):
    type = models.IntegerField(_('Type'), choices=RELATION_TYPE)
    maindemand = models.ForeignKey(Demand, verbose_name=_('Demande principale'), related_name='relations_as_main')
    subdemand = models.ForeignKey(Demand, verbose_name=_('Sous-demande'), related_name='relations_as_sub')
    
    def __unicode__(self):
        return RELATION_TYPE[self.type][1] + ': ' + self.maindemand.title + ' > ' + self.subdemand.title
        
    class Meta:
        verbose_name = _('Relation')
        verbose_name_plural = _('Relations')
        
class Attachment(models.Model):
    author = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    url = models.FileField(_('Fichier'), upload_to='uploads/%Y/%m/%d/%H%M%S')
    mimetype = models.CharField(_('Type MIME'), max_length=64)
    description = models.CharField(_('Description'), max_length=200)
    demand = models.ForeignKey(Demand, verbose_name=_('Demande'))
    
    def __unicode__(self):
        return self.description
        
    class Meta:
        verbose_name = _('Attachement')
        verbose_name_plural = _('Attachements')
        
class Assignee(models.Model):
    type = models.IntegerField(_('Type'), choices=ASSIGNEE_TYPE)
    user = models.ForeignKey(Profile, verbose_name=_('Utilisateur'), blank=True, null=True)
    value = models.CharField(_('Url ou adresse e-mail'), max_length=256)
    demand = models.ForeignKey(Demand, verbose_name=_('Demande'))
    
    def __unicode__(self):
        if self.type == 0:
            return self.user.uname
        else:
            return self.value
            
    class Meta:
        verbose_name = _('Assignee')
        verbose_name_plural = _('Assignees')
