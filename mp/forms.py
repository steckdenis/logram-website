# -*- coding: utf-8 -*-
#
# forms.py
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
from django import forms
from django.utils.translation import gettext_lazy as _

class NewForm(forms.Form):
    title = forms.CharField(label=_('Titre'), required=True, max_length=200)
    subtitle = forms.CharField(label=_('Sous-titre'), required=False, max_length=200)
    parts = forms.CharField(label=_('Participants'), required=True, help_text=_('Pseudos séparés par une virgule, sans espaces, sans vous compter'))