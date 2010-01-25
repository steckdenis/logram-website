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

from pyv4.general.models import Style
from pyv4.general.fields import ImageURLField

class PseudoForm(forms.Form):
    pseudo = forms.CharField(label=_('Pseudonyme'), max_length=64)
    email = forms.EmailField(label=_('Adresse e-mail'))
    show_email = forms.BooleanField(label=_('Afficher l\'adresse e-mail'), required=False)

class PassForm(forms.Form):
    password = forms.CharField(label=_('Mot de passe'), required=True, max_length=64, widget=forms.PasswordInput())
    password2 = forms.CharField(label=_('Retapez le mot de passe'), required=True, max_length=64, widget=forms.PasswordInput())
    
    def clean(self):
        if not hasattr(self, 'cleaned_data'):
            return
            
        cleaned_data = self.cleaned_data
        pwd1 = cleaned_data.get('password')
        pwd2 = cleaned_data.get('password2')
        
        if pwd1 != pwd2:
            raise forms.ValidationError(_('Les deux mots de passe ne sont pas les mêmes'))
        
        return cleaned_data

class DesignForm(forms.Form):
    design = forms.ModelChoiceField(label=_('Design utilisé'), queryset=Style.objects.all(), required=True, empty_label=None)
    remote = forms.BooleanField(label=_('Utiliser un design distant'), required=False)
    rurl = forms.CharField(label=_('Url du design distant'), required=False, max_length=256)

class ProfileForm(forms.Form):
    website = forms.URLField(label=_('Votre site web'), required=False, max_length=200)
    quote = forms.CharField(label=_('Votre citation'), help_text=_('Affichée au dessus de votre avatar sur les forums'), required=False, max_length=50)
    sign = forms.CharField(label=_('Votre signature'), required=False, help_text=_('LCode autorisé'), widget=forms.Textarea())
    avatar = ImageURLField(label=_('Url de votre avatar'), required=False, help_text=_('Utilisez «Envoi de fichiers» pour envoyer votre avatar sur internet'), max_width=100, max_height=100)