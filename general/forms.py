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

from django.contrib.auth.models import User

class RegisterForm(forms.Form):
    username = forms.CharField(label=_('Nom d\'utilisateur'), max_length=64, required=True, min_length=3)
    email = forms.EmailField(label=_('Adresse e-mail'), required=True, min_length=5, help_text=_('Cette adresse e-mail sert uniquement à vous permettre de recevoir des mails quand quelqu\'un répond à un sujet que vous surveillez.'))
    password = forms.CharField(label=_('Mot de passe'), required=True, max_length=64, widget=forms.PasswordInput())
    password2 = forms.CharField(label=_('Retapez le mot de passe'), required=True, max_length=64, widget=forms.PasswordInput())
    
    def clean(self):
        if not hasattr(self, 'cleaned_data'):
            return
        
        # Vérifier que les mots de passe sont bons
        cleaned_data = self.cleaned_data
        pwd1 = cleaned_data.get('password')
        pwd2 = cleaned_data.get('password2')
        
        if pwd1 != pwd2:
            raise forms.ValidationError(_('Les deux mots de passe ne sont pas les mêmes'))
        
        # Vérifier que le nom d'utilisateur n'est pas déjà pris
        usrs = User.objects.filter(username=cleaned_data.get('username'))
        
        if usrs.count() != 0:
            raise forms.ValidationError(_('Le nom d\'utilisateur est déjà pris'))
        
        return cleaned_data