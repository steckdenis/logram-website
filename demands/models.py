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

from pyv4.general.models import Profile
from pyv4.forum.models import Topic
from pyv4.packages.models import Distribution

# Create your models here.

class Type(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    header = models.TextField(_('En-têtes (consignes)'))
    color = models.CharField(_('Couleur'), max_length=6)
    icon = models.CharField(_('Url de l\'icône'), max_length=256)

    can_new = models.BooleanField(_('L\'utilisateur peut poster une nouvelle demande'), blank=True)
    can_propose = models.BooleanField(_('L\'utilisateur peut proposer une demande'), blank=True)
    is_bug = models.BooleanField(_('Cette demande est un bug'), blank=True)

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
        return self.name

    class Meta:
        verbose_name = _('Status')
        verbose_name_plural = _('Status')

class Category(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    d_type = models.ForeignKey(Type, verbose_name=_('Type de demande dedans'))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Categorie')
        verbose_name_plural = _('Categories')

class Priority(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    priority = models.IntegerField(_('Pourcentage de priorité'))

    def red(self):
        # Niveau de rouge de la couleur
        r = self.priority - 50
        if r < 0: return 0

        # 0 < r <= 50, passer à l'échelle 0 < r <= 200 (pas 256, trop clair)
        return r * 256 / 50

    def blue(self):
        # Niveau de bleu de la couleur
        r = 50 - self.priority
        if r > 50 or r < 0: return 0

        # 0 < r <= 50, passer à l'échelle 0 < r <= 200 (pas 256, trop clair)
        return r * 256 / 50

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Priorite')
        verbose_name_plural = _('Priorites')

class Demand(models.Model):
    title = models.CharField(_('Titre'), max_length=200)
    body = models.TextField(_('Contenu'))

    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date de mise à jour'), auto_now=True)
    assigned_at = models.DateTimeField(_('Date d\'assignation'), blank=True, null=True)

    done = models.IntegerField(_('Pourcentage d\'effectué'), default=0)
    demand_rate = models.IntegerField(_('Votes pour la demande'), default=0)
    work_rate = models.IntegerField(_('Votes pour la qualité de réalisation'), default=0)
    is_proposed = models.BooleanField(_('La demande est proposée'), blank=True, default=False)

    d_type = models.ForeignKey(Type, verbose_name=_('Type de demande'))
    author = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet'))
    status = models.ForeignKey(Status, verbose_name=_('Status'))
    category = models.ForeignKey(Category, verbose_name=_('Catégorie'))
    priority = models.ForeignKey(Priority, verbose_name=_('Priorité'))
    target_version = models.ForeignKey(Distribution, verbose_name=_('Version cible'), blank=True, null=True)
    assigned_to = models.ForeignKey(Profile, verbose_name=_('Personne assignée'), blank=True, null=True, related_name='assignated_demands')

    url = models.CharField(_('Url d\'un fichier'), max_length=256, blank=True, null=True)
    upstream_url = models.CharField(_('Url du bug upstream, si existant'), max_length=256, blank=True, null=True)

    children = models.ManyToManyField('self', verbose_name=_('Sous-demandes'), symmetrical=False, related_name='parents', blank=True)
    related = models.ManyToManyField('self', verbose_name=_('Demandes liées'), blank=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Demande')
        verbose_name_plural = _('Demandes')
        
        permissions = (
            ('vote_demand', 'Vote one demand'),
            ('take_demand', 'Take one demand'),
        )