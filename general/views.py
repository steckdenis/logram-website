# -*- coding: utf-8 -*-
#
# views.py
# This file is part of Logram Website
#
# Copyright (C) 2009, 2010 - Denis Steckelmacher <steckdenis@logram-project.org>
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
from pyv4.news.models import News
from pyv4.forum.models import Topic, Forum, Post, Alert, Poll, Choice, UserChoice
from pyv4.general.functions import *
from pyv4.general.forms import RegisterForm
from pyv4.upload.models import Directory
from pyv4.general.models import Profile
from pyv4.wiki.models import LogEntry
from pyv4.packages.models import Package
from pyv4.demands.models import Demand
from pyv4.general.index import complete_indexer

from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.contrib.auth import authenticate, login as lgin, logout as lg
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.utils.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib import messages

def index(request):
    # Nouvelles
    latest_news = cache.get('index_last_news', None)
    
    if not latest_news:
        latest_news = News.objects \
            .select_related('author') \
            .filter(published=True, is_private=False) \
            .order_by('-date_published')[:5]
            
        latest_news = list(latest_news)
        cache.set('index_last_news', latest_news, 60)
        
    # Journaux
    latest_journals = cache.get('index_last_journals', None)
    
    if not latest_journals:
        latest_journals = News.objects \
            .select_related('author') \
            .filter(published=True, is_private=True) \
            .order_by('-date_published')[:5]
            
        latest_journals = list(latest_journals)
        cache.set('index_last_journals', latest_journals, 60)
    
    # Messages du forum
    latest_topics = cache.get('index_last_topics', None)
    
    if not latest_topics:
        latest_topics = Topic.objects \
            .select_related('last_post', 'last_post__author') \
            .order_by('-last_post__date_created')[:5]
            
        latest_topics = list(latest_topics)
        cache.set('index_last_topics', latest_topics, 30)
    
    # Pages de wiki modifiées
    latest_wiki_changes = cache.get('index_last_wiki', None)
    
    if not latest_wiki_changes:
        latest_wiki_changes = LogEntry.objects \
            .select_related('page', 'author_user') \
            .filter(page__is_private=False) \
            .order_by('-date')[:5]
        
        latest_wiki_changes = list(latest_wiki_changes)
        cache.set('index_last_wiki', latest_wiki_changes, 60)
    
    # Derniers paquets
    latest_packages = cache.get('index_last_packages', None)
    
    if not latest_packages:
        latest_packages = Package.objects \
            .select_related('arch') \
            .order_by('-date')[:5]
            
        latest_packages = list(latest_packages)
        cache.set('index_last_packages', latest_packages, 300)

    # Dernières demandes
    latest_demands = cache.get('index_last_demands', None)
    
    if not latest_demands:
        latest_demands = Demand.objects \
            .select_related('author', 'd_type') \
            .order_by('-created_at')[:5]
            
        latest_demands = list(latest_demands)
        cache.set('index_last_demands', latest_demands, 60)
        
    # Sondage en cours
    mpoll = cache.get('index_last_poll', -1)
    
    if mpoll == -1:
        mpoll = Poll.objects \
                .select_related('topic') \
                .order_by('-pub_date')[:1]
        
        if len(mpoll) == 1:
            mpoll = get_poll(request, mpoll[0])
        else:
            mpoll = None
            
        cache.set('index_last_poll', mpoll, 60)
        
    # Savoir si on peut voter
    if request.user.is_anonymous():
         mpoll['can_vote'] = False
    else:
        user_choices = UserChoice.objects \
                        .filter(user=request.user.get_profile(), choice__poll=mpoll['object'])

        mpoll['can_vote'] = (user_choices.count() == 0)
    
    #Statistique
    stats = cache.get('index_stats', False)
    if not stats:
        # Prendre les statistiques
        stats = {}

        # stats['logram_users'] (TODO dans longtemps)
        stats['users'] = Profile.objects.count()
        stats['last_user'] = Profile.objects.order_by('-id')[0]
        stats['open_demands'] = Demand.objects.filter(status__closed=False).count()
        stats['demands'] = Demand.objects.count()
        stats['forums'] = Forum.objects.count()
        stats['topics'] = Topic.objects.filter(p_type=0).count()
        stats['messages'] = Post.objects.count()
        stats['packages'] = Package.objects.count()

        # Mettre en cache pour 20 minutes
        cache.set('index_stats', stats, 20*60)
    
    # Si l'utilisateur le peut, afficher les news en attente de validation et les alertes modos
    latest_validate_news = False
    moderator_alerts = False
    
    if request.user.has_perm('news.change_news'):
        latest_validate_news = News.objects \
            .select_related('author') \
            .filter(to_validate=True, published=False, is_private=False) \
            .order_by('-date_modified')
            
    if request.user.has_perm('forum.view_alerts') or request.user.has_perm('pastebin.view_alerts'):
        moderator_alerts = Alert.objects \
            .select_related('topic', 'author','paste')
        
    
    return tpl('global/index.html',
        {'latest_news': latest_news,
         'latest_journals': latest_journals,
         'latest_topics': latest_topics,
         'latest_packages': latest_packages,
         'latest_wiki': latest_wiki_changes,
         'latest_demands': latest_demands,
         'latest_validate_news': latest_validate_news,
         'moderator_alerts': moderator_alerts,
         'poll': mpoll,
         'stats': stats}, request)

def logout(request, user_id):
    if request.user.id != int(user_id):
        raise Http404

    lg(request)
    return HttpResponseRedirect('/')

def login(request):
    return tpl('global/login.html',
        {'is_error': False,
         'pseudo': ''}, request)
    
def login_validate(request):
    username = request.POST['username']
    password = request.POST['password']    
    
    user = authenticate(username=username, password=password)
    error_string = ''
    
    if user is not None:
        if user.is_active:
            lgin(request, user)
            
            messages.add_message(request, messages.INFO, _('Vous êtes connecté'))
            
            return HttpResponseRedirect(request.POST['next'])
        else:
            error_string = _('Votre compte d\'utilisateur est bloqué, vous ne pouvez plus vous connecter.')
    else:
        error_string = _('Nom d\'utilisateur ou mot de passe incorrect.')
    
    return tpl('global/login.html',
        {'is_error': True,
         'pseudo': username,
         'error_string': error_string}, request)
 
# Prévisualisation normale
def ajax_preview(request):
    msg = request.POST['text']
    
    return HttpResponse(lcode(msg))
    
# Prévisualisation PasteBin
def ajax_preview_pastebin(request, format):
    # On remplace les tabulations par des espaces
    msg = request.POST['text']
    msg = msg.replace('\t', '    ')
    
    return HttpResponse(highlight_code(msg, format))

ajax_preview_pastebin = csrf_exempt(ajax_preview_pastebin)
ajax_preview = csrf_exempt(ajax_preview)

def register(request):
    # Enregistre un nouvel utilisateur
    #print request.method
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        form.clean()
        if form.is_valid() and len(request.POST['test']) == 0:
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            g = get_object_or_404(Group, name=settings.DEFAULT_GROUP_NAME)
            md = get_object_or_404(Directory, pk=1)
            
            # Créer l'utilisateur
            usr = User.objects.create_user(username, email, password)
            
            # L'ajouter au groupe Utilisateurs
            usr.groups.add(g)
            
            # Créer l'arborescence des dossiers :
            #  - Dossier de username
            #     - Dossier Personnel
            #     - Messages du forum
            #     - Pages de documentation
            #     - Rapport de bugs et demandes
            
            d = Directory(name=(_('Dossier de %s') % username), user=usr, parent=md)
            d.save()
            d2 = Directory(name=_('Dossier personnel'), user=usr, parent=d, quota=4*1024*1024)
            d2.save()
            d2 = Directory(name=_('Messages du forum'), user=usr, parent=d, type=D_TYPE_FORUM)
            d2.save()
            d2 = Directory(name=_('Pages de documentation'), user=usr, parent=d, type=D_TYPE_WIKI)
            d2.save()
            d2 = Directory(name=_('Rapport de bugs et demandes'), user=usr, parent=d, type=D_TYPE_DEMANDS)
            d2.save()
            d2 = Directory(name=_('Avatar'), user=usr, parent=d, quota=32*1024)
            d2.save()
            
            # Créer le profile
            p = Profile(user=usr, uname=usr.username, main_group_name=g.name, website='', quote=_(u'Heureux d\'être là'), pperso='', avatar='', sign='', point=0, show_email=True, main_dir=d, main_group=g, style='/style/default')
            p.save()
            
            # Ouf ! On a fini
            
            return HttpResponseRedirect('/')
    else:
        # Afficher le formulaire
        form = RegisterForm()
    
    return tpl('global/register.html',
        {'form': form}, request)
        
def devcorner(request):
    # Page quasi statique
    return tpl('global/devcorner.html', {}, request)
        
def search(request, page):
    # Recherche
    page = int(page)
    q = request.GET['q']

    # 1. Prendre les résultats
    results = complete_indexer.search(q).prefetch()

    # 2. Paginer le tout
    paginator = Paginator(results, 20)        # 20 résultats par page

    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)

    # 3. Trouver le type des résultats
    rs = pg.object_list
    
    for r in rs:
        r.type = r.instance.__class__.__name__

    # 4. Rendre la template
    return tpl('global/search.html',
        {'page': page,
         'q': q,
         'results': pg.object_list,
         'list_pages': get_list_page(page, paginator.num_pages, 4)}, request)