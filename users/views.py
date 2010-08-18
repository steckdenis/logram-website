# -*- coding: utf-8 -*-
#
# views.py
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
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.translation import gettext as _, gettext_lazy
from django.utils.cache import cache
from django.shortcuts import get_object_or_404
from django.contrib import messages

from pyv4.general.functions import tpl, get_list_page
from pyv4.general.models import Profile, Style, Activity
from pyv4.users.forms import PseudoForm, PassForm, DesignForm, ProfileForm
from pyv4.pastebin.models import *

actnames = {
    'demands/addattachment.html': gettext_lazy('Ajout d\'un attachement'),
    'demands/edit_step1.html': gettext_lazy('Édition d\'une demande, étape 1'),
    'demands/edit_step2.html': gettext_lazy('Édition d\'une demande, étape 2'),
    'demands/handleassignees.html': gettext_lazy('Gestion des assignés à une demande'),
    'demands/handlerelated.html': gettext_lazy('Gestion des demandes liées'),
    'demands/index.html': gettext_lazy('Index des demandes'),
    'demands/list.html': gettext_lazy('Liste des demandes'),
    'demands/viewattachment.html': gettext_lazy('Affichage d\'un attachement'),
    'demands/view.html': gettext_lazy('Affichage d\'une demande'),
    'feeds/index.html': gettext_lazy('Liste des flux RSS'),
    'forum/addpoll.html': gettext_lazy('Ajout d\'un sondage'),
    'forum/alert.html': gettext_lazy('Création d\'une alerte'),
    'forum/edit.html': gettext_lazy('Édition d\'un message'),
    'forum/index.html': gettext_lazy('Accueil des forums'),
    'forum/viewforum.html': gettext_lazy('Affichage d\'un forum'),
    'forum/viewpoll.html': gettext_lazy('Affichage d\'un sondage'),
    'forum/viewtopic.html': gettext_lazy('Affichage d\'un sujet du forum'),
    'global/devcorner.html': gettext_lazy('Centre du développeur'),
    'global/index.html': gettext_lazy('Page d\'accueil'),
    'global/login.html': gettext_lazy('Connexion'),
    'global/register.html': gettext_lazy('Enregistrement'),
    'global/search.html': gettext_lazy('Recherche'),
    'news/list.html': gettext_lazy('Liste des nouvelles'),
    'news/view.html': gettext_lazy('Affichage d\'une nouvelle'),
    'packages/changelog.html': gettext_lazy('Historique d\'un paquet'),
    'packages/files.html': gettext_lazy('Fichiers d\'un paquet'),
    'packages/home.html': gettext_lazy('Accueil des paquets'),
    'packages/index.html': gettext_lazy('Téléchargements'),
    'packages/list.html': gettext_lazy('Liste des paquets'),
    'packages/loginfo.html': gettext_lazy('Informations sur la construction d\'un paquet'),
    'packages/mirrors.html': gettext_lazy('Liste des mirroirs'),
    'packages/sections.html': gettext_lazy('Sections d\'une distribution'),
    'packages/view.html': gettext_lazy('Affichage d\'un paquet'),
    'packages/viewsource.html': gettext_lazy('Informations sur un paquet source'),
    'pastebin/alert.html': gettext_lazy('Création d\'une alerte dans le pastebin'),
    'pastebin/index.html': gettext_lazy('Accueil du pastebin'),
    'pastebin/liste.html': gettext_lazy('Liste des snippets de code'),
    'pastebin/view.html': gettext_lazy('Affichage d\'un snippet de code'),
    'users/list.html': gettext_lazy('Liste des utilisateurs'),
    'users/show.html': gettext_lazy('Profil d\'un utilisateur'),
    'wiki/changes.html': gettext_lazy('Changements d\'une page de wiki'),
    'wiki/edit.html': gettext_lazy('Édition d\'une page de wiki'),
    'wiki/notfound.html': gettext_lazy('Tentative d\'accès à une page de wiki inexistante'),
    'wiki/show.html': gettext_lazy('Affichage d\'une page de wiki'),
}

def view(request, user_id):
    # Afficher les informations d'un utilisateur
    try:
        usr = Profile.objects.select_related('user').get(pk=user_id)
    except Profile.DoesNotExist:
        raise Http404
        
    try:
        paste = Pastebin.objects.filter(author=user_id).order_by('-created')[:1]
    except Pastebin.DoesNotExist:
        raise Http404
    
    if paste:
        ok = True
        temp = {'profile': usr, 'ok': ok, 'paste':paste[0]}
    else:
        ok = False
        temp = {'profile': usr, 'ok': ok}
    
    # Rendre la template
    return tpl('users/show.html', temp, request)

def list(request, page):
    # Lister les membres, par pseudo
    page = int(page)
    members = Profile.objects.select_related('user').order_by('-main_group', 'user__username')
    
    paginator = Paginator(members, 30)  # 30 utilisateurs par page
    
    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)
    
    return tpl('users/list.html',
        {'list_pages': get_list_page(page, paginator.num_pages, 4),
         'profiles': pg.object_list,
         'pindex': 2,
         'is_staff': False}, request)

def staff(request):
    # Même que list, mais seulement les membres du staff
    members = Profile.objects.select_related('user').exclude(main_group=1).order_by('main_group')
    
    return tpl('users/list.html',
        {'profiles': members,
         'is_staff': True}, request)

def online(request, page):
    # Afficher les utilisateurs en ligne
    page = int(page)
    
    # 1. Récupérer les informations du cache des connectés
    activities = Activity.objects \
                .select_related('user') \
                .order_by('-date')
    
    # 2. Compter
    anon = 0
    users = 0
    
    connected_users = []
    
    for act in activities:
        if act.user_id:
            users += 1
        else:
            anon += 1
            
        if act.template in actnames:
            act.activity = actnames[act.template]
        else:
            act.activity = _('Page privée')
            
    # 3. Paginer
    paginator = Paginator(activities, 30)  # 30 utilisateurs par page

    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)

    # 4. Rendre la template
    return tpl('users/list.html',
        {'list_pages': get_list_page(page, paginator.num_pages, 4),
         'profiles': pg.object_list,
         'is_connected': True,
         'anons': anon,
         'pindex': 4,
         'regs': users}, request)

@login_required
def opts_index(request):
    # Page statique, juste afficher la template
    return tpl('users/opts_index.html', {}, request)

@login_required
def opts_profile(request):
    # Changer le profile
    prof = request.user.get_profile()
    
    if request.method == 'POST':
        form = ProfileForm(request.POST)
            
        if form.is_valid():
            prof.website = form.cleaned_data['website']
            prof.quote = form.cleaned_data['quote']
            prof.pperso = request.POST['body']
            prof.avatar = form.cleaned_data['avatar']
            prof.sign = form.cleaned_data['sign']
            
            prof.save()
            
            messages.add_message(request, messages.INFO, _('Profil modifié avec succès'))
            return HttpResponseRedirect('user-5.html')
    else:
        form = ProfileForm(
            {'website': prof.website,
             'quote': prof.quote,
             'avatar': prof.avatar,
             'sign': prof.sign}
        )
    
    return tpl('users/opts_profile.html',
        {'form': form,
         'body': prof.pperso}, request)

@login_required
def opts_pseudo(request):
    # Pseudo et adresse e-mail
    if request.method == 'POST':
        form = PseudoForm(request.POST)
        
        if form.is_valid():
            usr = request.user
            prof = request.user.get_profile()
            
            usr.username = form.cleaned_data['pseudo']
            usr.email = form.cleaned_data['email']
            prof.show_email = form.cleaned_data['show_email']
            
            usr.save()
            prof.save()
            
            messages.add_message(request, messages.INFO, _('Pseudonyme et e-mail modifiés avec succès'))
            return HttpResponseRedirect('user-5.html')
    else:
        form = PseudoForm(
            {'pseudo': request.user.username,
             'email': request.user.email,
             'show_email': request.user.get_profile().show_email}
        )
        
    return tpl('users/opts_pseudo.html', {'form': form}, request)

@login_required
def opts_mdp(request):
    # Mot de passe
    if request.method == 'POST':
        form = PassForm(request.POST)
        
        if form.is_valid():
            usr = request.user
            
            # On vérifie que l'ancien mot de passe est connu
            
            
            usr.set_password(form.cleaned_data['password'])
            
            usr.save()
            
            messages.add_message(request, messages.INFO, _('Mot de passe changé avec succès'))
            return HttpResponseRedirect('user-5.html')
    else:
        form = PassForm()
        
    return tpl('users/opts_pass.html', {'form': form}, request)

@login_required
def opts_design(request):
    # Design du site
    
    if request.method == 'POST':
        form = DesignForm(request.POST)
            
        if form.is_valid():
            prof = request.user.get_profile()
            
            if form.cleaned_data['remote']:
                durl = form.cleaned_data['rurl']
            else:
                design = get_object_or_404(Style, name=form.cleaned_data['design'])
                
                durl = design.url
            
            prof.style = durl
            prof.save()
            
            # Vider le cache de session
            request.session['style'] = durl
            
            messages.add_message(request, messages.INFO, _('Design changé'))
            return HttpResponseRedirect('user-5.html')
    else:
        form = DesignForm({'rurl': request.user.get_profile().style, 'remote': True})
    
    return tpl('users/opts_design.html', {'form': form}, request)
