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

from pyv4.news.models import Category

class EditForm(forms.Form):
    title = forms.CharField(label=_('Titre'), required=True, max_length=200)
    category = forms.ModelChoiceField(label=_('Catégorie'), queryset=Category.objects.all(), required=True, empty_label=None)
    is_private = forms.BooleanField(label=_('Privée'), required=False)
    intro = forms.CharField(label=_('Introduction'), required=True, widget=forms.Textarea(), help_text=_('Non-formatée, affichée en page d\'accueil ou sur votre blog'))