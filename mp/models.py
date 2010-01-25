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

class Message(models.Model):
    author = models.ForeignKey(Profile, verbose_name=_('Auteur'))
    date_created = models.DateTimeField(_('Date de post'), auto_now_add=True)
    date_modified = models.DateTimeField(_('Date de modification'), auto_now=True)

    body = models.TextField(_('Corps du message'))

    topic = models.ForeignKey('Topic', verbose_name=_('Sujet'))

    def __unicode__(self):
        return self.topic.title

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')

class Topic(models.Model):
    title = models.CharField(_('Titre'), max_length=200)
    subtitle = models.CharField(_('Sous-titre'), max_length=200)

    last_message = models.ForeignKey(Message, verbose_name=_('Dernier message'), blank=True, null=True, related_name='mpt')
    num_messages = models.IntegerField(_('Nombre de messages'))

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Sujet')
        verbose_name_plural = _('Sujets')

class UserTopic(models.Model):
    user = models.ForeignKey(Profile, verbose_name=_('Utilisateur'), related_name='mps')
    topic = models.ForeignKey(Topic, verbose_name=_('Sujet'))

    has_deleted = models.BooleanField(_('Le membre a supprimé le MP'), default=False, blank=True)
    last_read_post = models.ForeignKey(Message, verbose_name=_('Dernier message lu'), null=True, blank=True)
    last_post_page = models.IntegerField(_('Page du dernier message'), blank=True, default=1)

    is_master = models.BooleanField(_('Le membre est maître de discussion'), default=False, blank=True)

    def __unicode__(self):
        return 'UserTopic : %i <-> %i' % (self.user_id, self.topic_id)

    class Meta:
        verbose_name = _('Lien utilisateur-sujet')
        verbose_name_plural = _('Liens utilisateur-sujet')