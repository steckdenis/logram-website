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
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from pyv4.general.functions import *
from pyv4.mp.models import *
from pyv4.mp.forms import *

@login_required
def index(request, page):
    # Afficher la liste des MP auxquels participe le membre
    page = int(page)
    
    # 1. Récupérer tous les UserTopics du membre
    usertopics = UserTopic.objects \
        .select_related('topic', 'topic__last_message', 'topic__last_message__author') \
        .filter(user=request.user.get_profile(), has_deleted=False) \
        .order_by('-topic__last_message__date_created')

    # 2. Paginer tout ça
    paginator = Paginator(usertopics, 20)        #20 MPs par page

    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)

    usertopics = pg.object_list

    # 3. Prendre les ID de tous les sujets
    topic_ids = [ ut.topic_id for ut in usertopics ]

    # 4. Prendre la liste des participants à chaque sujet
    parts = UserTopic.objects \
        .select_related('user') \
        .filter(topic__in=topic_ids)

    # 5. Ajouter la liste des participants aux MPs
    for usertopic in usertopics:
        usertopic.parts = []
        usertopic.read = usertopic.last_read_post_id == usertopic.topic.last_message_id
        
        for part in parts:
            if usertopic.topic_id == part.topic_id:
                usertopic.parts.append({'user': part.user,
                                        'read': part.last_read_post_id == usertopic.topic.last_message_id,
                                        'deleted': part.has_deleted})

        # Liste des pages
        numMsg = usertopic.topic.num_messages
        if numMsg <= 20:
            pages = '1'
        else:
            pages = range(1, (numMsg / 20)+2) #20 posts par page

        usertopic.pages = pages
    
    # 6. Préparer le formulaire
    if request.method == 'POST':
        form = NewForm(request.POST)
            
        if form.is_valid():
            # 1. Créer le sujet
            topic = Topic(title=form.cleaned_data['title'], subtitle=form.cleaned_data['subtitle'], num_messages=1)
            topic.save()

            # 2. Créer le message
            message = Message(author=request.user.get_profile(), body=request.POST['body'], topic=topic)
            message.save()

            # 3. Mettre à jour le sujet pour qu'il ait un dernier message
            topic.last_message = message
            topic.save()

            # 4. Splitter POST['parts'] pour avoir les participants, et prendre les profiles correspondants
            parts = request.POST['parts'].split(',')

            users = Profile.objects \
                .filter(uname__in=parts)

            users = list(users)
            users.append(request.user.get_profile())  # Nous aussi on participe :-°

            # 5. Créer les usertopics
            alreadyparts = []
            
            for user in users:
                if not user in alreadyparts:
                    usertopic = UserTopic(user=user, topic=topic, last_post_page=1, is_master=(user == request.user.get_profile()))
                    usertopic.save()
                    
                    alreadyparts.append(user)
            
            # 6. On a fini, afficher le MP
            request.user.message_set.create(message=_('Message personnel créé'))
            return HttpResponseRedirect('mp-2-%i-1.html' % topic.id)
    else:
        if request.GET.get('sendto', False):
            form = NewForm({'parts': request.GET['sendto']})
        else:
            form = NewForm()
            
    # 7. Rendre la template
    return tpl('mp/index.html',
        {'page': page,
         'usertopics': usertopics,
         'form': form,
         'pages': get_list_page(page, paginator.num_pages, 4)}, request)

@login_required
def view(request, topic_id, page):
    # Afficher un MP
    topic_id = int(topic_id)
    page = int(page)

    # 1. Récupérer les messages
    messages = Message.objects \
        .select_related('author', 'author__user') \
        .filter(topic=topic_id) \
        .order_by('date_created')

    # 2. Paginer
    paginator = Paginator(messages, 20)        #20 messages par page

    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)

    messages = pg.object_list

    # 3. Mettre à jour l'usertopic
    try:
        usertopic = UserTopic.objects \
            .select_related('topic') \
            .filter(topic=topic_id) \
            .get(user=request.user.get_profile())
    except UserTopic.DoesNotExist:
        raise Http404

    if usertopic.last_read_post_id != usertopic.topic.last_message_id:
        usertopic.last_post_page = page
        usertopic.last_read_post_id = messages[len(messages)-1].id
        usertopic.save()

    # 4. Prendre la liste des participants
    parts = UserTopic.objects \
        .select_related('user') \
        .filter(topic=topic_id)

    # 5. réactualiser le cache
    cache.delete('mps_%i' % request.user.id)

    # 6. Rendre la template
    return tpl('mp/view.html',
        {'msgs': messages,
         'usertopic': usertopic,
         'parts': parts,
         'upload_url': upload_url(request, D_TYPE_FORUM, 512*1024, usertopic.topic.id, usertopic.topic.title),
         'is_fr': request.LANGUAGE_CODE.startswith('fr'),
         'pages': get_list_page(page, paginator.num_pages, 4)}, request)

@login_required
def post(request, topic_id):
    # Poster un message (dans body)
    topic_id = int(topic_id)

    if request.method != 'POST':
        raise Http404

    # 1. Vérifier que l'utilisateur participe bien au MP
    try:
        usertopic = UserTopic.objects \
            .select_related('topic') \
            .filter(topic=topic_id) \
            .get(user=request.user.get_profile())
    except UserTopic.DoesNotExist:
        raise Http404

    # 2. Créer le message
    message = Message(author=request.user.get_profile(), body=request.POST['body'], topic=usertopic.topic)
    message.save()

    # 3. Mettre à jour le topic
    usertopic.topic.last_message = message
    usertopic.topic.num_messages += 1
    usertopic.topic.save()

    # 4. On a fini
    request.user.message_set.create(message=_('Message posté'))
    return HttpResponseRedirect('mp-2-%i-%i.html#r%i' % (usertopic.topic_id, (usertopic.topic.num_messages / 20) + 1, message.id))

@login_required
def edit(request, post_id):
    # Éditer un post
    post_id = int(post_id)

    # 1. Récupérer le post
    try:
        post = Message.objects \
            .get(pk=post_id)
    except Message.DoesNotExist:
        raise Http404

    # 2. Vérifier que l'utilisateur modifie bien _son_ post
    if post.author != request.user.get_profile():
        raise Http404

    if request.method == 'POST':
        # Mettre à jour le message
        post.body = request.POST['body']
        post.save()

        request.user.message_set.create(message=_('Message édité'))
        return HttpResponseRedirect('mp-2-%i-1.html' % post.topic_id)
    else:
        # Afficher le formulaire
        return tpl('forum/edit.html',
            {'is_mp': True,
             'pid': post.id,
             'body': post.body}, request)

@login_required
def newmp(request):
    # Nouveau MP

    if not request.method == 'POST':
        raise Http404

    

    # 1. Créer le sujet
    topic = Topic(title=request.POST['title'], subtitle=request.POST['subtitle'], num_messages=1)
    topic.save()

    # 2. Créer le message
    message = Message(author=request.user.get_profile(), body=request.POST['body'], topic=topic)
    message.save()

    # 3. Mettre à jour le sujet pour qu'il ait un dernier message
    topic.last_message = message
    topic.save()

    # 4. Splitter POST['parts'] pour avoir les participants, et prendre les profiles correspondants
    parts = request.POST['parts'].split(',')

    users = Profile.objects \
        .filter(uname__in=parts)

    users = list(users)
    users.append(request.user.get_profile())  # Nous aussi on participe :-°

    # 5. Créer les usertopics
    for user in users:
        usertopic = UserTopic(user=user, topic=topic, last_post_page=1, is_master=(user == request.user.get_profile()))
        usertopic.save()

    # 6. On a fini, afficher le MP
    request.user.message_set.create(message=_('Message personnel créé'))
    return HttpResponseRedirect('mp-2-%i-1.html' % topic.id)

@login_required
def addparts(request, topic_id):
    # Ajouter des participants
    topic_id = int(topic_id)
    
    # 1. Récupérer le usertopic
    try:
        usertopics = UserTopic.objects \
            .select_related('user') \
            .filter(topic=topic_id)
    except UserTopic.DoesNotExist:
        raise Http404
        
    alreadyparts = []
    
    for usertopic in usertopics:
        alreadyparts.append(usertopic.user.uname)

    # 2. Splitter la chaîne des utilisateurs et prendre ces utilisateurs
    parts = request.POST['parts'].split(',')

    users = Profile.objects \
        .filter(uname__in=parts)

    # 3. Créer les usertopics, pour ceux qui ne participent pas déjà
    for user in users:
        #user = unicode(user)
        if not user in alreadyparts:
            usertopic = UserTopic(user=user, topic=usertopic.topic, last_post_page=1, is_master=False)
            usertopic.save()
            
            alreadyparts.append(user)

    # 4. On a fini
    request.user.message_set.create(message=_('Participants ajoutés'))
    return HttpResponseRedirect('mp-2-%i-1.html' % usertopic.topic.id)

@login_required
def delete(request):
    # Supprimer des MPs

    if not request.method == 'POST':
        raise Http404

    # 1. Parser POST, qui contient des champs de la forme mp[id]
    ids = []

    for p in request.POST:
        if p.startswith('mp'):
            ids.append(int(p.split('[')[1][0:-1]))

    # 2. Mettre à jour les usertopics concernés
    UserTopic.objects \
        .filter(user=request.user.get_profile(), topic__in=ids) \
        .update(has_deleted=True)
        
    # 3. Réactualiser le cache
    cache.delete('mps_%i' % request.user.id)

    # 4. On a fini
    request.user.message_set.create(message=_('Les messages privés ont été supprimés'))
    return HttpResponseRedirect('mp-1-1.html')
