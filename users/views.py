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
from django.utils.translation import gettext as _
from django.utils.cache import cache
from django.shortcuts import get_object_or_404

from pyv4.general.functions import tpl, get_list_page
from pyv4.general.models import Profile, Style
from pyv4.users.forms import PseudoForm, PassForm, DesignForm, ProfileForm
from pyv4.pastebin.models import *

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
    onlines = cache.get('online_users', [0, 0])
    regs = onlines[0]
    anons = onlines[1]
    
    # 2. Ouvrir le fichier des membres connectés
    f = open('onlines/activity.log', 'r')
    
    # 3. Explorer chaque ligne pour trouver la liste des ID à récupérer
    ids = []
    
    for l in f:
        parts = l.strip().split(':')
        
        i = int(parts[2])
        
        if i != 0 and not i in ids:
            ids.append(i)
            
    f.close()
    
    # 4. Prendre les utilisateurs
    members = Profile.objects \
        .select_related('user') \
        .filter(user__id__in=ids) \
        .order_by('main_group', 'user__username')

    # 4. Paginer
    paginator = Paginator(members, 30)  # 30 utilisateurs par page

    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)

    # 5. Rendre la template
    return tpl('users/list.html',
        {'list_pages': get_list_page(page, paginator.num_pages, 4),
         'profiles': pg.object_list,
         'is_connected': True,
         'anons': anons,
         'pindex': 4,
         'regs': regs}, request)

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
            
            request.user.message_set.create(message=_('Profil modifié avec succès'))
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
            
            request.user.message_set.create(message=_('Pseudonyme et e-mail modifiés avec succès'))
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
            
            request.user.message_set.create(message=_('Mot de passe changé avec succès'))
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
            
            request.user.message_set.create(message=_('Design changé'))
            return HttpResponseRedirect('user-5.html')
    else:
        form = DesignForm({'rurl': request.user.get_profile().style, 'remote': True})
    
    return tpl('users/opts_design.html', {'form': form}, request)
