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
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, Http404
from django.utils.translation import gettext as _
from django.core.cache import cache

from pyv4.demands.models import *
from pyv4.packages.models import Distribution
from pyv4.forum.models import Topic
from pyv4.general.functions import *
from pyv4.forum.views import list_posts

import datetime

def index(request):
    # Afficher les types de demandes

    types = Type.objects.all()

    return tpl('demands/index.html',
        {'types': types}, request)

def mlist(request, type_id, status_id, order_by, page):
    # Afficher la liste des demandes d'un certain type, classées, et paginées
    type_id = int(type_id)
    status_id = int(status_id)
    page = int(page)

    # 1. Construire la requête de base
    demands = Demand.objects \
        .select_related('author', 'status', 'category', 'priority') \
        .filter(d_type=type_id)

    # 2. Appliquer le filtre
    if status_id != 0:
        demands = demands.filter(status=status_id)

    # 3. Ordonner
    if order_by == 'datec':
        demands = demands.order_by('-created_at')
    elif order_by == 'datem':
        demands = demands.order_by('-updated_at')
    elif order_by == 'datea':
        demands = demands.order_by('-assigned_at')
    elif order_by == 'title':
        demands = demands.order_by('title')
    elif order_by == 'done':
        demands = demands.order_by('-done')
    elif order_by == 'drate':
        demands = demands.order_by('-demand_rate')
    elif order_by == 'wrate':
        demands = demands.order_by('-work_rate')
    elif order_by == 'status':
        demands = demands.order_by('status')
    elif order_by == 'priority':
        demands = demands.order_by('-priority__priority')
    elif order_by == 'author':
        demands = demands.order_by('author__uname')
    elif order_by == 'category':
        demands = demands.order_by('category__name')

    # 4. Obtenir l'objet Type, pour colorer la page
    t = get_object_or_404(Type, pk=type_id)

    # 7. Obtenir les status
    status = Status.objects.all()
    
    # 6. Paginer
    paginator = Paginator(demands, 30)        #30 demandes par pages

    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)

    # 6. Rendre la template
    return tpl('demands/list.html',
        {'type': t,
         'status': status,
         'st': status_id,
         'order_by': order_by,
         'page': page,
         'pg': pg}, request)

@permission_required('demands.add_demand')
def post(request, action, type_or_demand_id):
    # Poster/Proposer/Éditer une demande. type_or_demand_id est un paeramètre qui change en
    # fonction de action, qui prend les valeurs suivantes :
    #  - 1 : Poster une nouvelle demande dans type_id
    #  - 2 : Proposer une nouvelle demande dans type_id
    #  - 3 : Éditer une demande
    action = int(action)
    type_or_demand_id = int(type_or_demand_id)

    # Vérifier que l'action est ok
    if action < 1 or action > 3:
        raise Http404

    # Vérifier que l'utilisateur a bien le droit de faire ce qu'il fait
    t = False
    
    if action != 3:
        # Prendre le type
        t = get_object_or_404(Type, pk=type_or_demand_id)

        # Vérifier
        if action == 1 and not t.can_new:
            raise Http404
        elif action == 2 and not t.can_propose:
            raise Http404

    demand = False
    if action == 3:
        demand = get_object_or_404(Demand, pk=type_or_demand_id)

    # Savoir si on peut définir l'avancement
    can_set_done = False

    if request.user.has_perm('demands.change_demand'):
        can_set_done = True
    elif action == 3:
        if request.user.get_profile() == demand.assigned_to:
            can_set_done = True
    
    if request.method == 'POST':
        # Poster la demande (ou l'éditer)
        title = request.POST['title']
        body = request.POST['body']
        cat_id = request.POST['category']
        
        if request.user.has_perm('demands.change_demand'):
            priority_id = request.POST['priority']
            status_id = request.POST['status']
            target_version_id = request.POST['target_version']

        done = 0
        if can_set_done:
            done = request.POST['done']

            try:
                done = int(done)
            except ValueError:
                done = 0

            if done < 0: done = 0
            if done > 100: done = 100
            
        if action == 1 or action == 2:
            # Créer un sujet
            topic = Topic(author=request.user.get_profile(), 
                          title=title, 
                          subtitle='', 
                          lang=request.LANGUAGE_CODE.split('_')[0],
                          last_post_page=1, 
                          num_posts=0, 
                          stick=False, 
                          closed=False, 
                          resolved=False, 
                          p_type=2, 
                          parent_id=0)
            topic.save()
            
            demand = Demand(topic=topic, d_type=t, author=request.user.get_profile())

        # Sauvegarder les champs de la demande
        demand.title = title
        demand.body = body
        demand.done = done
        demand.category_id = cat_id

        if action == 2:
            demand.url = request.POST['url']
            demand.is_proposed = True

        if request.user.has_perm('demands.change_demand'):
            demand.priority_id = priority_id
            demand.status_id = status_id
            demand.target_version_id = target_version_id
        else:
            # Statut et priorités par défaut
            demand.priority_id = 1
            demand.status_id = 1

        # Sauvegarder la demande
        demand.save()
        
        # Mettre à jour le sujet
        if action == 1 or action == 2:
            topic.parent_id = demand.id
            topic.save()

        # On a fini
        request.user.message_set.create(message=_("La demande a été éxécutée avec succès"))
        return HttpResponseRedirect("demand-5-%i-1.html" % demand.id)
        
    else:
        if action != 3:
            type_id = type_or_demand_id
        else:
            type_id = demand.d_type_id

        # Envoi de fichiers
        upl = False
        
        if action == 2:
            upl = upload_url(request, D_TYPE_DEMANDS, 32*1024*1024, Demand.objects.count(), _('Demande'))

        # On a besoin de la liste des catégories
        categories = Category.objects.filter(d_type=type_id)

        # Besoin aussi de la priorité, version cible et statut (pour le staff)
        priorities = False
        versions = False
        status = False
        if request.user.has_perm('demands.change_demand'):
            priorities = Priority.objects.all()
            versions = Distribution.objects.all()
            status = Status.objects.all()
        
        # Rendre la template
        return tpl('demands/edit.html',
            {'action': action,
             'type': t,
             'demand': demand,
             'categories': categories,
             'priorities': priorities,
             'versions': versions,
             'status': status,
             'can_set_done': can_set_done,
             'upl': upl,
             'type_or_demand_id': type_or_demand_id}, request)

def view(request, demand_id, page):
    # Afficher une demande
    demand_id = int(demand_id)
    page = int(page)
    
    # 1. Récupérer la demande
    try:
        demand = Demand.objects \
            .select_related('author', 'status', 'category', 'priority', 'target_version', 'assigned_to', 'd_type') \
            .get(pk=demand_id)
    except Demand.DoesNotExist:
        raise Http404

    # 2. Savoir si le vote est permis ou pas
    if not request.user.has_perm('demands.vote_demand'):
        vote_allowed = False
    else:
        vote_allowed = not cache.get('user_%i_already_voted_%i_%i' % (request.user.id, demand_id, demand.status.resolved), False)

    # Ainsi que la prise de la demande et l'édition
    can_take = False
    can_edit = False
    
    if not demand.assigned_to:
        if request.user.has_perm('demands.take_demand'):
            can_take = True

    if request.user.has_perm('demands.change_demand') or request.user == demand.author.user:
        can_edit = True

    # 3. Prendre les sous-demandes, et les demandes liées
    related_demands = demand.related.all()
    children_demands = demand.children.all()

    # S'il y a des enfants, calculer le pourcentage d'avancement en fonction des enfants
    total = 0
    pourcent = 0
    
    if len(children_demands) != 0: #len précharge la demande, on gagne une requête
        for child in children_demands:
            total += 100
            pourcent += child.done

        demand.done = pourcent * 100 / total

    
    
    # 4. Configuration de la liste des sujets
    config = {'demand': demand,
              'extends': 'demands/base.html',
              'vote_allowed': vote_allowed,
              'can_take': can_take,
              'can_edit': can_edit,
              'related_demands': related_demands,
              'children_demands': children_demands,
              'rel_len': len(related_demands),
              'child_len': len(children_demands),
              'title': demand.title}

    # On a fini
    return list_posts(request, demand.topic, page, config, 'demands/view.html')

@permission_required('demands.vote_demand')
def note(request, action, demand_id):
    # Noter une demande
    action = int(action)
    demand_id = int(demand_id)

    # Vérifier que l'utilisateur peut voter
    dr = (action == 1 or action == 2)
    if cache.get('user_%i_already_voted_%i_%i' % (request.user.id, demand_id, dr), False):
        raise Http404

    # 1. Récupérer la demande
    demand = get_object_or_404(Demand, pk=demand_id)

    # 2. Exécuter l'action
    if action == 1:
        demand.work_rate += 1
    elif action == 2:
        demand.work_rate -= 1
    elif action == 3:
        demand.demand_rate += 1
    elif action == 4:
        demand.demand_rate -= 1
    else:
        raise Http404
    
    # 3. Enregistrer la demande
    demand.save()

    cache.set('user_%i_already_voted_%i_%i' % (request.user.id, demand_id, dr), True, 24*60*60)

    # 4. Rediriger
    request.user.message_set.create(message=_("Votre vote a été pris en compte"))
    return HttpResponseRedirect('demand-5-%i-1.html' % demand_id)

@permission_required('demands.take_demand')
def take(request, demand_id):
    # Prendre une demande
    demand_id = int(demand_id)
    
    # 1. Récupérer la demande
    demand = get_object_or_404(Demand, pk=demand_id)

    # 2. Prendre la demande
    demand.assigned_to = request.user.get_profile()
    demand.assigned_at = datetime.datetime.now()
    demand.save()

    # 3. On a fini
    request.user.message_set.create(message=_('La demande vous a bien été attribuée'))
    return HttpResponseRedirect('demand-5-%i-1.html' % demand_id)

@permission_required('demands.change_demand')
def add_child(request, child_type, demand_id):
    # Ajouter une demande
    child_type = int(child_type)
    demand_id = int(demand_id)

    if request.method == 'POST':
        # Ajouter la demande
        demand = get_object_or_404(Demand, pk=demand_id)
        sd = get_object_or_404(Demand, pk=request.POST['did'])

        if child_type == 1:
            demand.children.add(sd)
        else:
            demand.related.add(sd)

        # On a fini
        request.user.message_set.create(message=_('Sous-demande ajoutée'))
        return HttpResponseRedirect('demand-5-%i-1.html' % demand_id)
    else:
        # Afficher la template

        return tpl('demands/add_child.html',
            {'child_type': child_type,
             'demand': get_object_or_404(Demand, pk=demand_id),
             'demand_id': demand_id}, request)

@permission_required('demands.change_demand')
def remove_child(request, child_type, demand_id, child_id):
    # Supprimer une demande liée/enfant
    child_type = int(child_type)
    child_id = int(child_id)
    demand_id = int(demand_id)

    # 1. Récupérer la demande
    demand = get_object_or_404(Demand, pk=demand_id)

    # 2. Supprimer le bon type d'enfant
    if child_type == 1:
        # Sous-demande
        demand.children.remove(get_object_or_404(Demand, pk=child_id))
    else:
        # Demande liée
        demand.related.remove(get_object_or_404(Demand, pk=child_id))

    # 3. On a fini
    request.user.message_set.create(message=_('La demande enfant a été retirée de la liste'))
    return HttpResponseRedirect('demand-5-%i-1.html' % demand_id)