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
from pyv4.forum.models import *
from pyv4.forum.forms import *
from pyv4.general.functions import *
from pyv4.news.models import News
from pyv4.demands.models import Assignee

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect, Http404
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context, Template
from django.contrib import messages

def return_page(topic, msg_id):
    rs = ''
    if topic.p_type == 0:
        rs = 'forum-2-%i-%i-%s.html' % (
            topic.id, 
            topic.last_post_page, 
            slugify(topic.title))
    elif topic.p_type == 1:
        news = get_object_or_404(News, pk=topic.parent_id)
        rs = 'news-2-%i-%i-%s.html' % (
            topic.parent_id,
            topic.last_post_page,
            slugify(news.title))
    elif topic.p_type == 2:
        rs = 'demand-4-%i-%i.html' % (
            topic.parent_id,
            topic.last_post_page)
    elif topic.p_type == 3:
        rs = 'packages-9-%i-%i-1.html' % (
            topic.parent_id,
            topic.last_post_page)
            
    if msg_id:
        rs += '#r%i' % msg_id
        
    return rs

def index(request):
    # Afficher la liste des forums dans leurs catégories. La fonction est complexe, mais j'explique ;-)
    
    # Récupérer les forums, leur catégorie, et leurs informations sur les derniers posts (par qui quand et où)
    forums = Forum.objects.select_related('category', 'last_topic', 'last_topic__last_post', 'last_topic__last_post__author').all()
    
    # Récupérer la liste des topics lus par l'utilisateur, si pas anonyme
    if not request.user.is_anonymous():
        # On a besoin de la liste des derniers topics des forums
        last_topics = [ forum.last_topic for forum in forums ]
        
        # Une petite requête pour trouver tout ça, la seule autre de la page
        uts = UserTopic.objects.select_related('topic', 'last_read_post').filter(topic__in=last_topics, user=request.user.get_profile())
        
        # Maintenant, on explore tout ça, et on ajoute un attribu 'read = True' aux forums qui sont dedans
        for forum in forums:
            for ut in uts:
                if ut.topic == forum.last_topic:
                    # Vérifier qu'on a lu jusqu'au dernier message
                    if ut.last_read_post == forum.last_topic.last_post:
                        forum.read = True
    
    # À cause d'une limitation des templates (pas d'assignation de variables),
    #    on a besoin d'une autre liste : categories
    categories = [ frm.category for frm in forums ]
    categories = list(set(categories))
    
    # Valà, c'est fini, on rend la template. Simple non ? Vive django !
    return tpl('forum/index.html',
        {'forums': forums,
         'categories': categories}, request)

def list_topics(request, topics, page, conf):
    # Liste des topics
    
    # Paginer le tout
    paginator = Paginator(topics, 20)        #20 topics par page
    
    if int(page) < 1:
        page = 1
    
    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)
    
    topics = pg.object_list
    
    # Si l'utilisateur est connecté, récupérer les informations de lecture
    if not request.user.is_anonymous():
        uts = UserTopic.objects.select_related('topic', 'last_read_post').filter(topic__id__in=[ t.id for t in topics ], user=request.user.get_profile())
        
        # On ajoute "read" aux topics lus, ainsi que le lien vers le dernier message lu
        for topic in topics:
            for ut in uts:
                if ut.topic == topic:
                    topic.last_read_post_page = ut.last_read_post_page
                    topic.last_read_post_id = ut.last_read_post_id
                    if ut.last_read_post == topic.last_post:
                        topic.read = True
    
    # Toujours à cause des templates, il faut manuellement créer le tableau des pages
    for topic in topics:
        pages = range(1, (topic.num_posts / 20)+2) #20 posts par page
        topic.pages = pages
    
    # Rendre la template
    conf['topics'] = topics
    conf['list_pages'] = get_list_page(page, paginator.num_pages, 4)
    
    return tpl('forum/viewforum.html', conf, request)

def viewforum(request, forum_id, page):
    # Afficher un forum
    
    # Récupérer les infos du forum (pour afficher titre et sous-titre)
    forum = get_object_or_404(Forum, pk=forum_id)
    
    # Récupérer les topics de ce forum TODO: filtrer les langues que l'utilisateur veut
    topics = Topic.objects.select_related('last_post', 'author', 'last_post__author').filter(p_type=0, parent_id=forum_id).order_by('-stick', '-last_post__date_created')
    
    # Plein de fonctions affichent des topics, donc tout est regroupé
    return list_topics(request, topics, page, 
        {'forum': forum})

# Equivalent de viewtopic, mais peut etre réutilisée pour afficher les commentaires de bugs, wiki et autres
def list_posts(request, topic, page, config, template):
    # Récupérer la liste des messages du topic
    posts = Post.objects.select_related('author', 'topic', 'topic__author', 'author__user').filter(topic=topic).order_by('date_created')
    
    # Paginer tout ça
    paginator = Paginator(posts, 20)        #20 posts par page
    
    if int(page) < 1:
        page = 1
    
    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)
    
    posts = pg.object_list
    
    # Récupérer les historiques des posts
    edits = History.objects.select_related('author', 'post').filter(post__id__in=[ p.id for p in posts ])
    
    # Associer les éditions aux posts
    for post in posts:
        for edit in edits:
            if post == edit.post:
                if not hasattr(post, 'edits'):
                    post.edits = [edit]
                else:
                    post.edits.append(edit)
    
    # Mettre à jour le dernier post lu
    if not request.user.is_anonymous() and len(posts) != 0:
        try:
            ut = UserTopic.objects.get(topic=topic, user=request.user.get_profile())
            
            last_post_id = posts[len(posts)-1].id
            
            if ut.last_read_post_id != last_post_id:
                ut.last_read_post_id = last_post_id
                ut.last_read_post_page = page
                ut.save()
                
        except UserTopic.DoesNotExist:
            ut = UserTopic(topic=topic, user=request.user.get_profile(), last_read_post=posts[len(posts)-1], last_read_post_page=page)
            ut.save()
    
    # Si modo (ou autre), afficher la liste des forums dans lequel le topic peut être déplacé
    if topic.p_type == 0:
        forums = {}
        if request.user.has_perm('forum.can_change_topic'):
            forums = Forum.objects.all()
        config['forums'] = forums
    
    # Prendre le sondage
    poll = False
    
    if topic.poll_id:
        poll = get_poll(request, topic.poll)
    
    # Si l'utilisateur est enregistré, savoir s'il surveille le sujet
    watch = False
    
    if not request.user.is_anonymous():
        bookmarks = Bookmark.objects.filter(user=request.user, topic=topic)
        
        watch = (bookmarks.count() != 0)
    
    # Rendre la template
    config['posts'] = posts
    config['topic'] = topic
    config['poll'] = poll
    config['list_pages'] = get_list_page(page, paginator.num_pages, 4)
    config['watch'] = watch

    if not request.user.is_anonymous():
        config['upload_url'] = upload_url(request, D_TYPE_FORUM, 2*1024*1024, topic.id, topic.title)
    
    return tpl(template, config, request)

def viewtopic(request, topic_id, page):
    # Afficher un topic
    # Prendre le sujet
    topic = get_object_or_404(Topic, pk=topic_id)
    
    # Prendre le forum
    forum = get_object_or_404(Forum, pk=topic.parent_id)
    
    # Afficher les posts
    return list_posts(request, topic, page, {
        'forum': forum}, 'forum/viewtopic.html')

@permission_required('forum.add_post')
def post(request, topic_id):
    # Poster un message
    if request.method != 'POST':
        raise Http404
    
    # Vérifier que le topic n'est pas fermé
    topic = get_object_or_404(Topic, pk=topic_id)
    
    if topic.closed:
        raise Http404
    
    # Poster le message
    msg = Post(topic=topic, author=request.user.get_profile(), has_helped=False, contents=request.POST['body'])
    msg.save()
    
    # Incrémenter l'occupation du topic, et définir son dernier post
    topic.last_post = msg
    topic.num_posts += 1
    topic.last_post_page = (topic.num_posts / 20) + 1
    
    if topic.p_type == 0:
        # Les topics de commentaire n'ont pas de forum parent
        forum = get_object_or_404(Forum, pk=topic.parent_id)
        
        forum.num_posts += 1
        forum.last_topic = topic
        forum.save()
        
    topic.save()
    
    # Trouver l'url de redirection
    redirect_url = return_page(topic, msg.id)
    
    # Envoyer, si nécessaire, un mail aux assignés de la demande
    demanddests = []
    
    if topic.p_type == 2:
        assignees = Assignee.objects \
            .filter(demand__id=topic.parent_id, type__in=[0, 1])
            
        for a in assignees:
            demanddests.append(a.value)
    
    # Envoyer un mail à tous ceux qui surveillent ce topic
    bookmarks = Bookmark.objects \
        .select_related('user') \
        .filter(topic=topic)
    
    forumdests = []
    
    for bk in bookmarks:
        if bk.user != request.user:
            forumdests.append(bk.user.email)
    
    # Envoyer le mail
    tpl = get_template('forum/mail.html')
    c = Context({
        'type': 'forum',
        'topic': topic.title,
        'body': request.POST['body'],
        'url': redirect_url,
        'user': request.user.username})
    
    if len(forumdests) != 0:
        mailforum = tpl.render(c)
        
        send_mail( \
            u'%(user)s a posté un message dans «%(topic)s»' % {
                'user': request.user.username, 
                'topic': topic.title}, \
            mailforum, \
            'website@logram-project.org', \
            forumdests, \
            fail_silently=True)
    
    if len(demanddests) != 0:
        c['type'] = 'demand'
    
        maildemand = tpl.render(c)
    
        send_mail( \
            u'[DEMAND %(id)i] New message from %(user)s in "%(topic)s"' % {
                'id': topic.parent_id,
                'user': request.user.username, 
                'topic': topic.title}, \
            maildemand, \
            'website@logram-project.org', \
            demanddests, \
            fail_silently=True)
    
    # On a fini
    messages.add_message(request, messages.INFO, _('Message posté avec succès'))
    return HttpResponseRedirect(redirect_url)

@permission_required('forum.change_post')
def edit(request, post_id):
    # Éditer un message
    
    # Vérifier que le message appartient à l'utilisateur, ou que celui-ci peut les éditer
    try:
        post = Post.objects.select_related('topic').get(pk=post_id)
    except Post.DoesNotExist:
        raise Http404
    
    if post.author != request.user.get_profile() and not request.user.has_perm('forum.edit_all_posts'):
        raise Http404
    
    can_change_topic = ((request.user.get_profile() == post.topic.author and post.topic.p_type == 0) or request.user.has_perm('form.change_topic'))
    
    if request.method == 'POST':
        if can_change_topic:
            form = EditTopicForm(request.POST)
        else:
            form = EditForm(request.POST)
        
        if form.is_valid():
            post.contents = request.POST['body']
            post.save()
            
            # On a peut-être changé le titre du sujet
            if can_change_topic:
                post.topic.title = form.cleaned_data['title']
                post.topic.subtitle = form.cleaned_data['subtitle']
                post.topic.save()
            
            # Ajouter un message dans le log
            log = History(post=post, author=request.user.get_profile(), comment=form.cleaned_data['log'])
            log.save()
            
            # On a fini
            messages.add_message(request, messages.INFO, _('Message édité avec succès'))
        
            # NOTE: On poste dans un topic, mais aussi dans des commentaires, donc on doit savoir sur quelle
            # page on retourne
            redirect_url = return_page(post.topic, post.id)
            
            # On a vraiment fini
            return HttpResponseRedirect(redirect_url)
        
        postcontents = request.POST['body']
    else:
        postcontents = post.contents
        
        if can_change_topic:
            form = EditTopicForm(
                {'title': post.topic.title,
                 'subtitle': post.topic.subtitle,
                 'lang': post.topic.lang})
        else:
            form = EditForm()
   
    upl = False
        
    if not request.user.is_anonymous():
        upl = upload_url(request, D_TYPE_FORUM, 2*1024*1024, post.topic_id, post.topic.title)
            
    return tpl('forum/edit.html', 
            {'body': postcontents,
             'form': form,
             'pid': post.id,
             'url': 4,
             'log': True,
             'upload_url': upl}, request)

@login_required
def toggle_helped(request, post_id):
    # Changer le has_helped du post, seulement après quelques vérifications
    
    # Vérifier que l'utilisateur est l'auteur du topic
    try:
        post = Post.objects.select_related('topic', 'topic__author').get(pk=post_id)
    except:
        raise Http404
    
    if post.topic.author != request.user.get_profile():
        raise Http404
    
    # Changer le has_helped
    if post.has_helped:
        post.has_helped = False
        message = _('Le message ne vous a pas aidé')
    else:
        post.has_helped = True
        message = _('Le message vous a aidé')
    
    post.save()
    
    # On a fini
    messages.add_message(request, messages.INFO, message)
    return HttpResponseRedirect(return_page(post.topic, post.id))

@permission_required('forum.add_topic')
def newtopic(request, forum_id):
    # Créer un nouveau sujet
    
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        
        if form.is_valid():
            body = request.POST['body']
            
            # Prendre le forum
            forum = get_object_or_404(Forum, pk=forum_id)
            
            # Créer le sujet
            topic = Topic(parent_id=forum_id,
                          p_type=0,
                          author=request.user.get_profile(),
                          lang=form.cleaned_data['lang'],
                          title=form.cleaned_data['title'],
                          subtitle=form.cleaned_data['subtitle'],
                          last_post_page=1,
                          num_posts=1,
                          stick=False,
                          closed=False,
                          resolved=False)
            
            topic.save()
            
            # Créer le message
            message = Post(topic=topic, author=request.user.get_profile(), has_helped=False, contents=body)
            message.save()
            
            # Mettre à jour les données
            topic.last_post = message
            forum.num_topics += 1
            forum.num_posts += 1
            forum.last_topic = topic
            
            topic.save()
            forum.save()
            
            messages.add_message(request, messages.INFO, _('Nouveau sujet créé avec succès'))
            return HttpResponseRedirect(return_page(topic, message.id))
    else:
        form = NewTopicForm({'lang': request.LANGUAGE_CODE.split('_')[0]})
    
    return tpl('forum/edit.html',
            {'pid': forum_id,
             'url': 6,
             'log': False,
              'form': form}, request)

@login_required
def unread(request, forum_id, page):
    # Liste des topics non-lus
    forum_id = int(forum_id)
    
    # On reprend la liste des topics lus
    if forum_id == 0:
        forum = {'id': 0}
        read_topics = UserTopic.objects \
            .select_related('topic') \
            .extra(where=['forum_usertopic.last_read_post_id=forum_topic.last_post_id', 'forum_topic.id=forum_usertopic.topic_id'], tables=['forum_topic']) \
            .filter(user=request.user.get_profile(), topic__p_type=0) \
            .values('topic')
    else:
        forum = get_object_or_404(Forum, pk=forum_id)
        read_topics = UserTopic.objects \
            .select_related('topic', 'topic__forum') \
            .extra(where=['forum_usertopic.last_read_post_id=forum_topic.last_post_id']) \
            .filter(user=request.user.get_profile(), topic__parent_id=forum_id, topic__p_type=0) \
            .values('topic')
    
    if len(read_topics) != 0:
        # On prend tous les topics qui ne sont pas dedans
        ft = ', '.join([ str(e['topic']) for e in read_topics])
        unread_topics = Topic.objects \
            .select_related('last_post', 'author', 'last_post__author') \
            .extra(where=['forum_topic.id NOT IN (%s)' % ft]) \
            .filter(p_type=0) \
            .order_by('-stick', '-last_post__date_created')
    
        if forum_id != 0:
            unread_topics = unread_topics.filter(parent_id=forum_id)
    else:
        unread_topics = Topic.objects.none()
        
    # Rendre la liste
    return list_topics(request, unread_topics, page,
        {'forum': forum,
         'isnt_a_forum': True,
         'title': _('Sujets non-lus'),
         'func': 7,
         'on_unread_topics': True})

@login_required
def mytopics(request, forum_id, page):
    # Topics dont on est l'auteur
    forum_id = int(forum_id)
    
    my_topics = Topic.objects \
        .select_related('last_post', 'author', 'last_post__author') \
        .filter(author=request.user.get_profile(), p_type=0) \
        .order_by('-stick', '-last_post__date_created')
    
    if forum_id != 0:
        my_topics = my_topics.filter(forum__id=forum_id)
        forum = get_object_or_404(Forum, pk=forum_id)
    else:
        forum = {'id': 0}
       
    # C'est fini, on peut rendre
    return list_topics(request, my_topics, page,
        {'forum': forum,
         'isnt_a_forum': True,
         'title': _('Sujets que j\'ai créés'),
         'func': 8,
         'on_my_topics': True})

@login_required
def visited(request, forum_id, page):
    # Topics visités
    forum_id = int(forum_id)
    
    visited_topics = Topic.objects \
        .select_related('last_post', 'author', 'last_post__author') \
        .extra(tables=['forum_usertopic'], where=['forum_usertopic.topic_id=forum_topic.id']) \
        .filter(usertopic__user=request.user.get_profile(), p_type=0) \
        .order_by('-stick', '-last_post__date_created')

    if forum_id != 0:
        visited_topics = visited_topics.filter(forum__id=forum_id)
    
    return list_topics(request, visited_topics, page,
        {'forum': {'id': forum_id},
         'isnt_a_forum': True,
         'title': _('Sujets que j\'ai visités'),
         'func': 9,
         'on_visited_topics': True})

@login_required
def posted(request, forum_id, page):
    # Topics dans lesquels on a posté
    forum_id = int(forum_id)
    
    # Récupérer nos messages et leurs topics
    my_messages = Post.objects \
        .select_related('topic') \
        .filter(author=request.user.get_profile(), topic__p_type=0)
    
    # Filter par forum si nécessaire
    if forum_id != 0:
        my_messages = my_messages.filter(topic__forum__id=forum_id)
    
    # Récupérer les topics qui vont avec
    my_topics = [ p['topic'] for p in my_messages.values('topic') ]
    my_topics = list(set(my_topics))        # Pas besoin de doublons, on ne veut pas une requête SQL de 3 kilomètres
    posted_topics = Topic.objects \
        .select_related('last_post', 'author', 'last_post__author') \
        .filter(id__in=my_topics) \
        .order_by('-stick', '-last_post__date_created')

    return list_topics(request, posted_topics, page,
        {'forum': {'id': forum_id},
         'isnt_a_forum': True,
         'title': _('Sujets auxquels j\'ai participé'),
         'func': 10,
         'on_posted_topics': True})

@login_required
def toggle_solve(request, topic_id):
    # Résoudre ou pas un sujet. Vérifier que c'est bien son auteur qui résoud
    topic_id = int(topic_id)
    topic = get_object_or_404(Topic, pk=topic_id)
    
    if topic.author != request.user.get_profile():
        raise Http404
    
    # Toggler
    topic.resolved = not topic.resolved
    topic.save()
    
    # On a fini
    messages.add_message(request, messages.INFO, _('Résolution du sujet mise à jour'))
    return HttpResponseRedirect(return_page(topic, 0))

@permission_required('forum.add_alert')
def alert(request, topic_id):
    # Alerter les modérateurs
    topic_id = int(topic_id)
    
    if request.method == 'POST':
        form = AlertForm(request.POST)
            
        if form.is_valid():
            # Récupérer le topic
            topic = get_object_or_404(Topic, pk=topic_id)
            
            # Créer l'alerte
            alert = Alert(topic=topic, author=request.user.get_profile(), comment=form.cleaned_data['comment'])
            alert.save()
            
            # On a fini
            messages.add_message(request, messages.INFO, _('Modérateurs alertés'))
            return HttpResponseRedirect(return_page(topic, 0))
    else:
        form = AlertForm()
            
    # Afficher le formulaire
    return tpl('forum/alert.html', 
        {'topic_id': topic_id,
         'form': form}, request)

@permission_required('forum.change_topic')
def moderate(request, topic_id):
    # Opérations qu'on peut faire sur un sujet
    topic_id = int(topic_id)
    
    # POST seulement (sécu)
    if request.method != 'POST':
        raise Http404
    
    topic = get_object_or_404(Topic, pk=topic_id)
    
    # Un if pour savoir ce qu'on veut faire
    action = request.POST['action']
    
    if action == 'lock':
        topic.closed = True
        message = _('Sujet fermé')
        
    elif action == 'dlock':
        topic.closed = False
        message = _('Sujet réouvert')
        
    elif action == 'solve':
        topic.resolved = True
        message = _('Sujet résolu')
        
    elif action == 'dsolve':
        topic.resolved = False
        message = _('Sujet plus résolu')
        
    elif action == 'stick':
        topic.stick = True
        message = _('Sujet mis en post-it')
        
    elif action == 'dstick':
        topic.stick = False
        message = _('Sujet plus en post-it')
    
    elif action == 'move':
        forum_id = request.POST['forum']
        
        if topic.p_type != 0:
            raise Http404
        
        # Décompter les messages du sujet à son ancien forum
        old_forum = get_object_or_404(Forum, pk=topic.parent_id)
        old_forum.num_topics -= 1
        old_forum.num_posts -= topic.num_posts
        old_forum.save()
        
        # Déplacer le sujet
        frm = get_object_or_404(Forum, pk=forum_id)
        topic.parent_id = forum_id
        topic.save()
        
        # Ajouter au nouveau forum les messages du sujet
        frm.num_topics += 1
        frm.num_posts += topic.num_posts
        frm.save()
        
        # NOTE: On ne change pas last_topic dans le forum. Ce n'est rien, c'est comme
        # une trace du transfert, l'utilisateur arrivera toujours sur le bon sujet.
        # On ne met pas non-plus à jour la date du topic. Le modérateur aura normalement posté dedans,
        # et s'il ne l'a pas fait, tant pis, c'est que le topic n'était pas intéressant :-° .
        
        # On a fini
        messages.add_message(request, messages.INFO, _('Sujet déplacé avec succès'))
        
        nforum = _(frm.name)
        
        return HttpResponseRedirect('forum-1-%i-1-%s.html' % (frm.id, slugify(nforum)))
    else:
        raise Http404
    
    topic.save()
    
    messages.add_message(request, messages.INFO, message)
    return HttpResponseRedirect(return_page(topic, 0))

@permission_required('forum.delete_alert')
def rmalert(request, alert_id):
    # Suppression d'une alerte modérateurs
    
    alert = get_object_or_404(Alert, pk=alert_id)
    alert.delete()
    
    messages.add_message(request, messages.INFO, _('Alerte modérateur supprimée'))
    
    return HttpResponseRedirect('/')
    
@login_required
def addpoll(request, topic_id):
    # Ajouter un sondage au sujet
    topic_id = int(topic_id)
    
    # Récupérer le sujet
    topic = get_object_or_404(Topic, pk=topic_id)
    
    # Si le sujet a déjà un sondage, abandonner
    if topic.poll_id:
        raise Http404
    
    # Vérifier que l'utilisateur est sur son topic et a les droits add_poll, ou qu'il a le droit poll_on_all_topics
    if topic.author != request.user.get_profile() and not request.user.has_perm('forum.poll_on_all_topics'):
        raise Http404
    
    # Soit topic.author == request.user.get_profile(), soit le droit forum.poll_on_all_topics est ok
    if topic.author == request.user.get_profile() and not request.user.has_perm('forum.add_poll'):
        raise Http404
        
    # Afficher le formulaire
    if request.method == 'POST':
        form = PollForm(request.POST)
        
        if form.is_valid():
            question = form.cleaned_data['question'].strip()
            
            # Trouver les choix valides
            choices = []
            
            for c in form.cleaned_data['choices'].split('\n'):
                if len(c.strip()) != 0:
                    choices.append(c.strip())
            
            # Créer le sondage
            poll = Poll(question=question, topic=topic)
            poll.save()
            
            # Créer les choix
            for c in choices:
                choice = Choice(poll=poll, choice=c, votes=0)
                choice.save()
            
            # Ajouter le sondage au sujet
            topic.poll = poll
            topic.save()
            
            # On a fini
            messages.add_message(request, messages.INFO, _(u'Sondage ajouté'))
            return HttpResponseRedirect(return_page(topic, 0))
    else:
        form = PollForm()
    
    # Afficher la template
    return tpl('forum/addpoll.html',
        {'topic': topic,
         'form': form}, request)

@permission_required('forum.poll_on_all_topics')
def view_votes(request, poll_id):
    # Afficher les résultats d'un sondage
    poll_id = int(poll_id)
    
    # Récupérer le sondage
    try:
        poll = Poll.objects \
                .select_related('topic') \
                .get(pk=poll_id)
    except:
        raise Http404
    
    poll = get_poll(request, poll)
    
    # Prendre les choix des utilisateurs
    choices = UserChoice.objects \
                .select_related('user', 'choice') \
                .filter(choice__poll=poll['object']) \
                .order_by('choice')
                
    # Afficher
    return tpl('forum/viewvotes.html',
        {'topic': poll['object'].topic,
         'poll': poll,
         'choices': choices}, request)

@login_required
def vote(request, poll_id):
    # Voter à un sondage
    poll_id = int(poll_id)
    
    if request.method != 'POST':
        raise Http404
    
    # Vérifier que l'utilisateur peut voter
    user_choices = UserChoice.objects \
                    .filter(user=request.user.get_profile(), choice__poll=poll_id)
                    
    poll_can_vote = (user_choices.count() == 0)
    
    if not poll_can_vote:
        raise Http404
        
    # Récupérer le vote qui appartient au sondage et qui a l'ID envoyée en POST
    choices = Choice.objects.filter(poll=poll_id, pk=request.POST['choice'])
    
    if len(choices) == 0:
        raise Http404
        
    # Lui ajouter un vote
    choice = choices[0]
    choice.votes += 1
    choice.save()
    
    # Dire qu'on a voté
    user_choice = UserChoice(user=request.user.get_profile(), choice=choice)
    user_choice.save()
    
    # On a fini
    topic = get_object_or_404(Topic, poll=poll_id)
    
    messages.add_message(request, messages.INFO, _(u'Votre vote a été pris en compte'))
        
    return HttpResponseRedirect(return_page(topic, 0))

@login_required
def toggle_watch(request, topic_id):
    # Placer un topic sous surveillance
    
    # Récupérer le sujet
    topic = get_object_or_404(Topic, pk=topic_id)
    
    # Récupérer les bookmarks déjà existants
    bookmarks = Bookmark.objects.filter(topic=topic, user=request.user)
    
    if bookmarks.count() == 0:
        # Créer le Bookmark, l'utilisateur n'en ayant pas encore
        bk = Bookmark(topic=topic, user=request.user)
        bk.save()
        
        message = _(u'Vous êtes abonné au sujet «%s»') % topic.title
    else:
        # Supprimer l'unique bookmark
        bk = bookmarks[0]
        
        bk.delete()
        
        message = _(u'Vous n\'êtes plus abonné au sujet «%s»') % topic.title
    
    # Retourner au sujet
    messages.add_message(request, messages.INFO, message)
    return HttpResponseRedirect(return_page(topic, 0))