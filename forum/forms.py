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

class EditForm(forms.Form):
    log = forms.CharField(label=_('Commentaire d\'édition'), required=True, max_length=200)

class NewTopicForm(forms.Form):
    title = forms.CharField(label=_('Titre du sujet'), required=True, max_length=150)
    subtitle = forms.CharField(label=_('Sous-titre du sujet'), required=False, max_length=200)
    lang = forms.CharField(label=_('Code ISO de la langue'), required=True, max_length=2)

class EditTopicForm(EditForm, NewTopicForm):
    pass
    
class AlertForm(forms.Form):
    comment = forms.CharField(label=_('Raison de l\'alerte'), required=True, max_length=400)

class PollForm(forms.Form):
    question = forms.CharField(label=_('Question'), required=True, max_length=200)
    choices = forms.CharField(label=_('Choix'), required=True, widget=forms.Textarea(), help_text=_('Un choix par ligne'))
    
    def clean(self):
        if not hasattr(self, 'cleaned_data'):
            return
        
        # Vérifier que les entrées sont bonnes
        cleaned_data = self.cleaned_data
        cs = cleaned_data['choices']
        
        # Splitter les choix
        css = cs.split('\n')
        
        # Compter les choix valides
        count = 0
        
        for c in css:
            if len(c.strip()) != 0:
                count += 1
        
        if count < 2:
            raise forms.ValidationError(_('Il faut au moins deux questions non-nulles, séparées par des retours à la ligne'))
        
        if len(cleaned_data['question'].strip()) == 0:
            raise forms.ValidationError(_('La question ne peut pas être composée de caractères vides'))
        
        return cleaned_data