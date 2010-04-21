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
from pyv4.forum.models import Topic

MIRROR_LOCATIONS = (
    (0, _('Inconnu')),
    (1, _('Europe')),
    (2, _('Amérique')),
    (3, _('Asie')),
    (4, _('Océanie')),
    (5, _('Afrique')),
)

STRING_TYPE = (
    (0, _('Titre')),
    (1, _('Description courte')),
    (2, _('Description longue')),
    (3, _('Entrée de changelog')),
)

CHANGELOG_TYPE = (
    (1, _('Faible priorité')),
    (2, _('Fonctionnalité')),
    (3, _('Correction de bogue')),
    (4, _('Correction de sécurité')),
)

class Section(models.Model):
    name = models.CharField(_('Nom générique pour la création de paquets'), max_length=16)
    
    long_name = models.CharField(_('Nom'), max_length=32)
    desc = models.TextField(_('Description en français'))
    
    def __unicode__(self):
        return self.name + ' : ' + self.long_name
    
    class Meta:
        verbose_name = _('Section')
        verbose_name_plural = _('Sections')

class Arch(models.Model):
    name = models.CharField(_('Nom'), max_length=10)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Architecture')
        verbose_name_plural = _('Architectures')

class Distribution(models.Model):
    name = models.CharField(_('Nom de la version'), max_length=32)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Distribution')
        verbose_name_plural = _('Distributions')

class SourcePackage(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet'))
    
    def __unicode__(self):
        return self.name
        
    class Meta:
        verbose_name = _('Paquet source')
        verbose_name_plural = _('Paquets source')
        
class SourceLog(models.Model):
    source = models.ForeignKey(SourcePackage, verbose_name=_('Paquet source'))
    flags = models.IntegerField(_('Flags'))
    arch = models.ForeignKey(Arch, verbose_name=_('Architecture'))
    date = models.DateTimeField(_('Date'))
    author = models.CharField(_('Auteur, si import manuel'), max_length=200)
    maintainer = models.CharField(_('Mainteneur'), max_length=200)
    upstream_url = models.CharField(_('Url du site web upstream'), max_length=256)
    version = models.CharField(_('Version'), max_length=200)
    distribution = models.ForeignKey(Distribution, verbose_name=_('Distribution'))
    license = models.CharField(_('Licence'), max_length=64)
    
    date_rebuild_asked = models.DateTimeField(_('Date de demande de reconstruction'), blank=True, null=True)
    
    depends = models.TextField(_('Dépendances'))
    suggests = models.TextField(_('Suggestions'))
    conflicts = models.TextField(_('Conflits'))
    
    def maintainer_san(self):
        return self.maintainer.replace('@', ' at ')
        
    def maintainer_email(self):
        return self.maintainer.split('<')[-1].split('>')[0]

    def maintainer_user(self):
        # Renvoyer l'utilisateur (Profile) qui a la bonne url
        if not hasattr(self, 'maint_user'):
            rs = Profile.objects \
                .select_related('user', 'main_group') \
                .filter(user__email=self.maintainer_email())

            if len(rs) == 0:
                self.maint_user = None
            else:
                self.maint_user = rs[0]
            
        return self.maint_user
        
    def author_san(self):
        return self.author.replace('@', ' at ')
    
    def author_email(self):
        return self.author.split('<')[-1].split('>')[0]

    def author_name(self):
        return self.author.split('<')[0].strip()

    def __unicode__(self):
        return self.source.name + '~' + self.version
        
    class Meta:
        verbose_name = _('Historique de source')
        verbose_name_plural = _('Historiques de source')

class Package(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    sourcepkg = models.ForeignKey(SourcePackage, verbose_name=_('Paquet source'))
    
    maintainer = models.CharField(_('Mainteneur'), max_length=200)
    section = models.ForeignKey(Section, verbose_name=_('Section'))

    version = models.CharField(_('Version'), max_length=200)
    arch = models.ForeignKey(Arch, verbose_name=_('Architecture'))
    distribution = models.ForeignKey(Distribution, verbose_name=_('Distribution'), related_name='pkg')
    primarylang = models.CharField(_('Langue principale de l\'empaquetage'), max_length=2)
    download_size = models.IntegerField(_('Taille du téléchargement'))
    install_size = models.IntegerField(_('Taille d\'installation'))

    download_url = models.CharField(_('Url de téléchargement'), max_length=256)
    date = models.DateTimeField(_('Date de création/modification'), auto_now=True)

    depends = models.TextField(_('Dépendances'))
    suggests = models.TextField(_('Suggestions'))
    conflicts = models.TextField(_('Conflits'))
    provides = models.TextField(_('Fournitures'))
    replaces = models.TextField(_('Remplacements'))
    
    source = models.CharField(_('Paquet source'), max_length=200)
    license = models.CharField(_('Licence'), max_length=20)
    flags = models.IntegerField(_('Flags'))
    packageHash = models.CharField(_('Hash SHA1 du paquet'), max_length=40)
    metadataHash = models.CharField(_('Hash SHA1 des métadonnées'), max_length=40)
    upstream_url = models.CharField(_('Adresse upstream'), max_length=200)

    # Fonctions d'accès aux informations du paquet
    def upstream_version(self):
        return self.version.split('~')[0]

    def logram_version(self):
        if '~' in self.version:
            return self.version.split('~')[1]
        else:
            return 0

    def maintainer_san(self):
        return self.maintainer.replace('@', ' at ')

    def maintainer_email(self):
        return self.maintainer.split('<')[-1].split('>')[0]

    def maintainer_user(self):
        # Renvoyer l'utilisateur (Profile) qui a la bonne url
        if not hasattr(self, 'maint_user'):
            rs = Profile.objects \
                .select_related('user', 'main_group') \
                .filter(user__email=self.maintainer_email())

            if len(rs) == 0:
                self.maint_user = None
            else:
                self.maint_user = rs[0]
            
        return self.maint_user

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Paquet')
        verbose_name_plural = _('Paquets')

class ChangeLog(models.Model):
    version = models.CharField(_('Version'), max_length=64)
    distribution = models.ForeignKey(Distribution, verbose_name=_('Distribution'))
    package = models.ForeignKey(Package, verbose_name=_('Paquet'))
    email = models.CharField(_('Email'), max_length=200)
    author = models.CharField(_('Auteur'), max_length=200)
    type = models.IntegerField(_('Type'), choices=CHANGELOG_TYPE)
    date = models.DateTimeField(_('Date'))
    
    def __unicode__(self):
        return self.version + ' ' + self.author + ' <' + self.email + '>'
        
    def tt(self):
        for t in CHANGELOG_TYPE:
            if t[0] == self.type:
                return t[1]
        
    class Meta:
        verbose_name = _('ChangeLog')
        verbose_name_plural = _('ChangeLogs')

class String(models.Model):
    package = models.ForeignKey(Package, verbose_name=_('Paquet'))
    changelog = models.ForeignKey(ChangeLog, verbose_name=_('ChangeLog'), blank=True, null=True)
    language = models.CharField(_('Code ISO de langue'), max_length=2)
    type = models.IntegerField(_('Type'), choices=STRING_TYPE)
    content = models.TextField(_('Contenu'))

    def __unicode__(self):
        return '[' + self.language + '] ' + self.content

    class Meta:
        verbose_name = _('Chaine')
        verbose_name_plural = _('Chaines')

class Mirror(models.Model):
    url = models.CharField(_('Url'), max_length=256)
    place = models.IntegerField(_('Emplacement'), choices=MIRROR_LOCATIONS)
    
    def __unicode__(self):
        return self.url
    
    class Meta:
        verbose_name = _('Mirroir')
        verbose_name_plural = _('Mirroirs')

class Category(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))

    weight = models.IntegerField(_('Poids, pour classer'))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Categorie')
        verbose_name_plural = _('Categories')

class Download(models.Model):
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    cat = models.ForeignKey(Category, verbose_name=_('Categorie'))

    screen = models.FileField(_('Capture d\'écran'), upload_to='uploads/%Y/%m/%d/%H%M%S')
    thb = models.FileField(_('Miniature de la capture'), upload_to='uploads/%Y/%m/%d/%H%M%S')

    weight = models.IntegerField(_('Poids, pour classer'))
    
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Telechargement')
        verbose_name_plural = _('Telechargements')

class DwVariant(models.Model):
    download = models.ForeignKey(Download, verbose_name=_('Telechargement parent'))
    url = models.FileField(_('Chemin d\'accès'), upload_to='uploads/%Y/%m/%d/%H%M%S')

    name = models.CharField(_('Nom'), max_length=30)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Variante')
        verbose_name_plural = _('Variantes')
