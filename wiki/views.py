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
from pyv4.wiki.models import *
from pyv4.wiki.forms import *
from pyv4.general.functions import *
from pyv4.general.templatetags.general_tags import format_date

from django.http import HttpResponseRedirect, Http404, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import gettext as _
from django.core.paginator import Paginator, EmptyPage, InvalidPage

import random

def index(request):
    return viewpagelang(request, 'index', 'auto')

def viewpage(request, slug):
    return viewpagelang(request, slug, 'auto')

def viewpagelang(request, slug, lang):
    # Afficher une page de wiki
    
    # 1. Récupérer toutes les pages qui ont le slug demandé (ces pages ont des langues différentes)
    pages = Page.objects.filter(slug=slug)
    
    # 2. Voir s'il y a au moins une page (len() fait une requête, c'est mieux, ça met en cache les résultats)
    if len(pages) == 0:
        # Pas de page, l'afficher
        return tpl('wiki/notfound.html',
            {'slug': slug}, request)
    
    # 3. Si plus d'une page a ce slug, alors prendre celle qui a la langue de l'utilisateur.
    #    Si aucune n'a sa langue, prendre la version en anglais
    if len(pages) == 1:
        page = pages[0]
    else:
        lang_found = False
        
        for pg in pages:
            if pg.lang == lang:
                page = pg
                lang_found = True
                break
                
            elif request.LANGUAGE_CODE.startswith(pg.lang) and lang == 'auto':
                # Langue de l'utilisateur, et il n'en a pas spécifiée
                page = pg
                lang_found = True
                break
                
            elif pg.lang == 'en':
                page_en = pg
        
        if not lang_found:
            page = page_en
    
    # 4. Si la page est privée, seul le staff y a accès
    if page.is_private and not request.user.has_perm('wiki.view_private_pages'):
        raise Http404
    
    # 5. Trouver toutes les langues de la page (utiliser l'identificateur pour ça)
    langs = Page.objects \
        .only('lang', 'slug') \
        .filter(identifier=page.identifier)
    
    # 6. Rendre la template
    return tpl('wiki/show.html', 
        {'page': page,
         'in_discover': slug.startswith('discover'),
         'langs': langs}, request)

@login_required
def edit(request, page_id, identifier, slug):
    # Créer une nouvelle page
    page_id = int(page_id)
    identifier = int(identifier)
    
    upl = False
    captcha_string = ''
    
    if request.method == 'POST':
        pbody = request.POST['body']
        page = False
        
        if page_id == 0:
            # Nouvelle page
            if not request.user.has_perm('wiki.add_page'):
                raise Http404
            
            form = NewForm(request.POST)
            
            if form.is_valid():
                if identifier != 0:
                    slug = slugify(form.cleaned_data['title'])
                
                page = Page(title=form.cleaned_data['title'],
                            slug=slug,
                            lang=form.cleaned_data['lang'],
                            body=request.POST['body'],
                            is_protected=False,
                            is_private=False)
                
                if identifier != 0:
                    page.identifier = identifier
                else:
                    page.save()
                    page.identifier = page.id
                
                page.save()
                
                # On a fini
                if not request.user.is_anonymous():
                    request.user.message_set.create(message=_(u'Page créée avec succès'))
                    
                return HttpResponseRedirect('wiki-%s.%s.html' % (slug, form.cleaned_data['lang']))
        else:
            page = get_object_or_404(Page, pk=page_id)
            lang = page.lang
            
            # Vérifier que la page n'est ni privée ni protégée
            if page.is_protected and request.user.is_anonymous():
                raise Http404
            elif page.is_private and not request.user.has_perm('wiki.view_private_pages'):
                raise Http404
            
            form = EditForm(request.POST)
                
            can = True
            
            # Vérifier le captcha
            if request.user.is_anonymous():
                if request.POST['captcha'] != request.session.get('captcha_good_letters', ''):
                    can = False
                
            if form.is_valid() and can:
                previous_body = page.body
                
                page.title = form.cleaned_data['title']
                page.body = request.POST['body']
                page.save()
                
                # Créer un enregistrement dans le log
                if request.user.is_anonymous():
                    logentry = LogEntry(page=page, body=previous_body, author_ip=request.META.get('REMOTE_ADDR'), comment=form.cleaned_data['log'])
                    logentry.save()
                else:
                    logentry = LogEntry(page=page, body=previous_body, author_user=request.user.get_profile(), comment=form.cleaned_data['log'])
                    logentry.save()
                
                # On a fini
                if not request.user.is_anonymous():
                    request.user.message_set.create(message=_(u'Page éditée avec succès'))
                    
                return HttpResponseRedirect('wiki-%s.%s.html' % (slug, page.lang))
    else:
        if page_id != 0:
            page = get_object_or_404(Page, pk=page_id)
            pbody = page.body
            
            if not request.user.is_anonymous():
                upl = upload_url(request, D_TYPE_WIKI, 8*1024*1024, page.id, page.title)
            
            form = EditForm({'title': page.title, 'identifier': identifier})
        else:
            # L'utilisateur doit avoir le droit d'ajouter une page, pour éviter le spam
            if not request.user.has_perm('wiki.add_page'):
                raise Http404
            
            page = False
            pbody = ''
            
            form = NewForm({'identifier': identifier, 'lang': ''})
                
        # Captcha si l'utilisateur n'est pas authentifié
        if request.user.is_anonymous():
            possible_color_names = [
                _('rouges'),
                _('verts'),
                _('bleus'),
                _('noirs')
            ]
            possible_color_rgb = [
                'rgb(255, 0,   0)',
                'rgb(0,   255, 0)',
                'rgb(0,   0,   255)',
                'rgb(0,   0,   0)'
            ]
            index = random.randint(0, len(possible_color_rgb) - 1)
            
            request.session['captcha_good_color_rgb'] = possible_color_rgb[index]
            good_name = possible_color_names[index]
            
            captcha_string = _('Saissez les caractères <span style="color: %(color)s;">%(name)s</span> de l\'image ci-dessus') % \
            {
                'color': possible_color_rgb[index],
                'name': good_name
            }
                
    # Afficher le formulaire
    return tpl('wiki/edit.html',
            {'slug': slug,
             'create': page_id == 0,
             'translate': identifier == 0,
             'page_id': page_id,
             'identifier': identifier,
             'upload_url': upl,
             'page': page,
             'body': pbody,
             'captcha_string': captcha_string,
             'form': form}, request)

def randompage(request):
    # Une page au hasard, dans la langue de l'utilisateur
    
    # 1. Prendre une page
    pages = Page.objects \
        .filter(lang=request.LANGUAGE_CODE.split('-')[0], is_private=False) \
        .order_by('?')
    
    page = pages[0]
    
    # 3. Trouver toutes les langues de la page (utiliser l'identificateur pour ça)
    langs = Page.objects \
        .only('lang', 'slug') \
        .filter(identifier=page.identifier)
    
    # 4. Rendre la template
    return tpl('wiki/show.html', 
        {'page': page,
         'langs': langs}, request)

def changes(request, page):
    # Historique de tout le wiki
    page = int(page)
    
    # 1. Récupérer tout l'historique du wiki
    changes = LogEntry.objects \
        .select_related('author_user', 'author_user', 'page') \
        .defer('body') \
        .filter(page__is_private=False) \
        .order_by('-date')
    
    # 2. Paginer tout ça
    paginator = Paginator(changes, 20)        # 20 changements par page
    
    if page < 1:
        page = 1
    
    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)
        
    # 3. Construire manuellement une page pour la template (ok, c'est sale, mais quand-même plus propre que des hacks dans la template)
    dict_page = {'title': _('Le wiki'), 'ignore_breadcrumb': True}
    
    # 4. Afficher
    return tpl('wiki/changes.html',
        {'page': dict_page,
         'list_pages': get_list_page(page, paginator.num_pages, 4),
         'global_changes': True,
         'changes': pg.object_list}, request)

def pagedate(request, change_id):
    # Affiche une page à un certain niveau de changement
    change_id = int(change_id)
    
    # 1. Prendre le changement
    try:
        change = LogEntry.objects \
            .select_related('page') \
            .get(pk=change_id)
    except LogEntry.DoesNotExist:
        raise Http404
    
    # 2. Adapter la page
    page = change.page
    page.body = change.body     # Ancien contenu
    
    # 3. Trouver toutes les langues de la page (utiliser l'identificateur pour ça)
    langs = Page.objects \
        .only('lang', 'slug') \
        .filter(identifier=page.identifier)
    
    # 4. Rendre la template
    return tpl('wiki/show.html', 
        {'page': page,
         'langs': langs}, request)

@permission_required('wiki.change_page')
def cancelchange(request, change_id):
    # Défaire un changement
    change_id = int(change_id)
    
    # Vérifier que c'est un membre du staff qui fait ça
    if not request.user.is_staff:
        raise Http404
    
    # 1. Prendre le changement
    try:
        change = LogEntry.objects \
            .select_related('page') \
            .get(pk=change_id)
    except LogEntry.DoesNotExist:
        raise Http404
    
    # 2. Remettre la page comme elle était
    page = change.page
    previous_body = page.body
    
    page.body = change.body
    page.save()
    
    # 3. Créer un autre changement pour cette page
    nchange = LogEntry(page=page, 
        comment=_('Retour en arrière : %s') % change.date.strftime('%d/%m/%Y %H:%M:%S'),
        body=previous_body,
        author_user=request.user.get_profile())
    
    nchange.save()
    
    # 4. On a fini
    request.user.message_set.create(message=_('Changement défait'))
    return HttpResponseRedirect('wiki-%s.%s.html' % (page.slug, page.lang))

def history(request, page_id):
    # Historique d'une page
    page_id = int(page_id)
    
    # 1. Récupérer la page
    page = get_object_or_404(Page, pk=page_id)
    
    # 2. Récupérer tout l'historique de la page
    changes = LogEntry.objects \
        .select_related('author_user', 'author_user') \
        .defer('body') \
        .filter(page=page) \
        .order_by('-date')
    
    # 3. Afficher
    return tpl('wiki/changes.html',
        {'page': page,
         'changes': changes}, request)

@permission_required('wiki.change_page')
def toggle_protect(request, page_id):
    # Protéger ou pas une page
    
    # Modifier la page
    page = get_object_or_404(Page, pk=page_id)
    
    if page.is_protected:
        page.is_protected = False
        message = _('La page a été dé-protégée')
    else:
        page.is_protected = True
        message = _('La page a été protégée')
        
    page.save()
    
    # On a fini
    request.user.message_set.create(message=message)
    return HttpResponseRedirect('wiki-%s.%s.html' % (page.slug, page.lang))

@permission_required('wiki.private_page')
def toggle_private(request, page_id):
    # Rendre privée ou pas une page
    
    # Modifier la page
    page = get_object_or_404(Page, pk=page_id)
    
    if page.is_private:
        page.is_private = False
        message = _('La page n\'est plus privée')
    else:
        page.is_private = True
        message = _('La page est maintenant privée')
        
    page.save()
    
    # On a fini
    request.user.message_set.create(message=message)
    return HttpResponseRedirect('wiki-%s.%s.html' % (page.slug, page.lang))
