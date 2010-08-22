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
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.utils.translation import gettext as _
from django.contrib import messages

from datetime import datetime

from pyv4.news.models import *
from pyv4.news.forms import *
from pyv4.general.functions import *
from pyv4.general.models import Profile
from pyv4.forum.views import list_posts
from pyv4.forum.models import Topic

def index(request, page, cat_id, user_id):
    #Afficher la liste des news, avec pagination
    page = int(page)
    cat_list = Category.objects.all()
    cat_id = int(cat_id)
    user_id = int(user_id)
    user_name = None
    
    news_list = News.objects \
        .select_related('category', 'author') \
        .order_by('-date_published') \
        .filter(published=True)
    
    if cat_id != 0:
        # On filtre une catégorie
        cat = get_object_or_404(Category, pk=cat_id)
        news_list = news_list.filter(category=cat)
    
    
    if user_id == 0:
        # Prendre seulement les nouvelles publiques
        news_list = news_list.filter(is_private=False)
    else:
        # Prendre les news privées du membre
        news_list = news_list.filter(is_private=True, author__id=user_id)
        user_name = get_object_or_404(Profile, user__id=user_id).uname
        
    paginator = Paginator(news_list, 15)        #15 news par page
    
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    try:
        news = paginator.page(page)
    except (EmptyPage, InvalidPage):
        news = paginator.page(paginator.num_pages)
    
    return tpl('news/list.html', 
        {'news_list': news.object_list,
         'list_pages': get_list_page(page, paginator.num_pages, 4),
         'cat_list': cat_list,
         'is_private': (user_id != 0),
         'user_name': user_name,
         'user_id': user_id,
         'cat_id': cat_id}, request)

def view(request, page, news_id):
    #Récupérer la news et l'afficher.
    try:
        news = News.objects.select_related('category', 'author', 'topic').get(pk=news_id)
    except News.DoesNotExist:
        raise Http404
    
    # Vérifier que la news est publiée, ou que c'est un admin
    if not news.published and not request.user.has_perm('news.view_all'):
        raise Http404
    
    cat = _(news.category.name)
    catid = news.category.id
    
    config = {'news': news,
              'cat': cat,
              'catid': catid,
              'title': news.title,
              'is_comments': True}
    
    # On affiche également les commentaires de la news, donc on a besoin d'un topic. Cette fonction
    # nous permet de respecter le principe DRY, en utilisant directement viewtopic du forum
    
    # On a fini
    return list_posts(request, news.topic, page, config, 'news/view.html')

@login_required
def my(request):
    #Liste les news de l'utilisateur et les afficher dans une template
    news_list = News.objects.select_related('category').filter(author=request.user.get_profile()).order_by('-date_modified')
    
    return tpl('news/my.html', {'news_list': news_list}, request)

@login_required
def my_tools(request, acti, news_id):
    #Supprime ou met en validation une news
    try:
        news = News.objects.select_related('category').get(pk=news_id)
    except News.DoesNotExist:
        raise Http404
        
    # Supprimer
    # Mettre en attente de validation ou pas
    # Publier ou pas (si privée)
    
    if acti == '1':
        #Supprimer
        nt = news.title
        news.topic.delete()
        news.delete()
        
        messages.add_message(request, messages.INFO,  _(u'Nouvelle "%s" supprimée') % nt)
        return HttpResponseRedirect('/news-3.html')
    elif acti == '2':
        #Mettre en attente de validation
        if news.to_validate == False:
            news.to_validate = True
            messages.add_message(request, messages.INFO,  _('Nouvelle "%s" mise en attente de validation') % news.title)
        else:
            news.to_validate = False
            messages.add_message(request, messages.INFO,  _('La nouvelle "%s" n\'est plus en attente de validation') % news.title)
        
        news.save()
        
        return HttpResponseRedirect('/news-3.html')
    elif acti == '3':
        #Publier ou pas, seulement si nouvelle privée
        if not news.is_private:
            raise Http404
            
        if news.published == False:
            news.published = True
            messages.add_message(request, messages.INFO,  _(u'Nouvelle "%s" publiée') % news.title)
        else:
            news.published = False
            messages.add_message(request, messages.INFO,  _(u'Nouvelle "%s" dépubliée') % news.title)
        
        news.save()
        
        return HttpResponseRedirect('/news-3.html')
    elif acti == '4':
        # Valider ou rejeter, pour les validateurs
        if request.method != 'POST' or not request.user.has_perm('news.view_all'):
            raise Http404
            
        # Savoir si on valide ou refuse
        act = request.POST['act']
        
        if act == 'validate':
            # Valider
            
            news.to_validate = False
            news.published = True
            news.date_published = datetime.datetime.now()
            
            message = _(u'La nouvelle «%s» est validée') % news.title
        elif act == 'reject':
            # Rejeter
            
            news.to_validate = False
            news.rejected = True
            news.rejected_reason = request.POST['reason']
            
            message = _(u'La nouvelle %s est rejetée') % news.title
        
        news.save()
        
        messages.add_message(request, messages.INFO, message)
        return HttpResponseRedirect('news-2-%i-1-%s.html' % (news.id, slugify(news.title)))
    else:
        raise Http404

@login_required
def edit(request, news_id):
    #Edite (ou crée) une nouvelle)
    
    if request.method == 'POST':
        form = EditForm(request.POST)
            
        body = request.POST['body']
        
        if form.is_valid():
            if news_id != '0':
                try:
                    news = News.objects.get(pk=news_id)
                except News.DoesNotExist:
                    raise Http404
                
                if news.published:
                    # On ne touche pas aux news publiées
                    raise Http404
                
                # Trouver la catégorie
                category = get_object_or_404(Category, name=form.cleaned_data['category'])
                
                news.title = form.cleaned_data['title']
                news.intro = form.cleaned_data['intro']
                news.body = body
                news.rejected = False
                news.is_private = form.cleaned_data['is_private']
                news.save()
                
                messages.add_message(request, messages.INFO,  _(u'Nouvelle "%s" éditée avec succès') % news.title)
                return HttpResponseRedirect('/news-3.html')
            else:
                topic = Topic(author=request.user.get_profile(),
                             parent_id=0,
                             p_type=1,
                             lang=request.LANGUAGE_CODE.split('_')[0],
                             title=form.cleaned_data['title'],
                             subtitle='',
                             last_post_page=1,
                             num_posts=0,
                             stick=False,
                             closed=False,
                             resolved=False)

                topic.save()
                
                # Trouver la catégorie
                category = get_object_or_404(Category, name=form.cleaned_data['category'])
                
                news = News(author=request.user.get_profile(),
                            title=form.cleaned_data['title'],
                            intro=form.cleaned_data['intro'],
                            body=body,
                            date_published=datetime.datetime.now(),
                            category=category,
                            published=False,
                            to_validate=False,
                            is_private=form.cleaned_data['is_private'],
                            rejected=False,
                            rejected_reason=False,
                            topic=topic)
                            
                news.save()
                
                topic.parent_id = news.id
                topic.save()

                messages.add_message(request, messages.INFO,  _(u'Nouvelle "%s" créée avec succès') % news.title)
                return HttpResponseRedirect('/news-3.html')
        
        upul = False
        body = request.POST['body']
    else:
        upul = False
        
        if news_id != '0':
            news = get_object_or_404(News, pk=news_id)
            
            form = EditForm({
                'title': news.title,
                'category': news.category_id,
                'is_private': news.is_private,
                'intro': news.intro})
            
            upul = upload_url(request, D_TYPE_FORUM, 4*1024*1024, news.id, news.title)
            body = news.body
        else:
            form = EditForm()
            body = ''
    
    return tpl('news/edit.html',
            {'id': news_id,
             'form': form,
             'upload_url': upul,
             'body': body}, request)
