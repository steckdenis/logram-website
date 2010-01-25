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

from pyv4.wiki.models import Page

class BaseEditForm(forms.Form):
    title = forms.CharField(label=_('Titre'), max_length=300, required=True)

class EditForm(BaseEditForm):
    log = forms.CharField(label=_('Commentaire d\'édition'), max_length=300, required=True)

class NewForm(BaseEditForm):
    lang = forms.CharField(label=_('Code ISO de la langue'), max_length=2, required=True)
    identifier = forms.IntegerField(label=_('Identificateur'), required=True, widget=forms.HiddenInput())
    
    def clean(self):
        # Vérifier qu'il n'y a pas deux pages avec le même identifier et la même langue
        if not hasattr(self, 'cleaned_data'):
            return
            
        cleaned_data = self.cleaned_data
        lang = cleaned_data.get('lang', False)
        identifier = cleaned_data.get('identifier', False)
        
        if not (lang and identifier):
            return cleaned_data
         
        if identifier == 0:
            raise forms.ValidationError(_('Il faut un identificateur de page'))
             
        pages = Page.objects.filter(identifier=identifier, lang=lang)
         
        if pages.count() != 0:
            raise forms.ValidationError(_('Une traduction de cette page dans cette langue existe déjà'))

        return cleaned_data
