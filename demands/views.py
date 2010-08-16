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
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.translation import gettext as _
from django.core.cache import cache
from django.contrib import messages
from django.db.models import Q

from pyv4.demands.models import *
from pyv4.demands.forms import *
from pyv4.forum.models import Topic
from pyv4.general.functions import *
from pyv4.forum.views import list_posts

from pygments import highlight
from pygments.lexers import *
from pygments.formatters import HtmlFormatter

import datetime

def index(request):
    # Afficher les types de demandes
    types = Type.objects.all()

    return tpl('demands/index.html',
        {'types': types}, request)
        
def mlist(request, type_id, status_id, product_id, sort, page):
    # Afficher les demandes
    type_id = int(type_id)
    status_id = int(status_id)
    product_id = int(product_id)
    page = int(page)
    
    # 1. Requête de base
    demands = Demand.objects \
        .select_related('reporter', 'product', 'component', 'product_version', 'status', 'priority', 'type')
        
    # 2. Filtres demandés
    t = None
    
    if type_id != 0:
        t = get_object_or_404(Type, pk=type_id)
        demands = demands.filter(type=t)
    
    if status_id != 0:
        demands = demands.filter(status=status_id)
    
    product = None
    if product_id != 0:
        product = get_object_or_404(Product, pk=product_id)
        demands = demands.filter(product=product)
        
    # 3. Ordonner
    sign = ''
    
    if sort[0] == '-':
        sign = '-'
        
    osort = sort
    sort = sort[1:]
        
    if sort == 'update':
        demands = demands.order_by(sign + 'updated_at')
    elif sort == 'date':
        demands = demands.order_by(sign + 'created_at')
    elif sort == 'title':
        demands = demands.order_by(sign + 'title')
    elif sort == 'done':
        demands = demands.order_by(sign + 'done')
    elif sort == 'status':
        demands = demands.order_by(sign + 'status')
    elif sort == 'priority':
        demands = demands.order_by(sign + 'priority__priority')
    elif sort == 'author':
        demands = demands.order_by(sign + 'reporter__uname')
    elif sort == 'productversion':
        demands = demands.order_by(sign + 'product__name', sign + 'product_version__name')
    elif sort == 'productcomponent':
        demands = demands.order_by(sign + 'product__name', sign + 'component__name')
    elif sort == 'platform':
        demands = demands.order_by(sign + 'platform__name', sign + 'platform_version__name')
    elif sort == 'type':
        demands = demands.order_by(sign + 'type')
    else:
        raise Http404
        
    # 4. Obtenir des listes (liste des types par exemple)
    types = Type.objects.all()
    status = Status.objects.all()
    
    # 5. Paginer
    paginator = Paginator(demands, 15)        #15 demandes par pages

    try:
        pg = paginator.page(page)
    except (EmptyPage, InvalidPage):
        pg = paginator.page(paginator.num_pages)
        
    # 6. Rendre la template
    return tpl('demands/list.html',
        {'type_id': type_id,
         'status_id': status_id,
         'product_id': product_id,
         'sort': osort,
         'page': page,
         'demands': pg.object_list,
         'type': t,
         'product': product,
         'types': types,
         'status': status,
         'list_pages': get_list_page(page, paginator.num_pages, 4)}, request)
         
def updatefilter(request):
    if request.method != 'POST':
        raise Http404
    
    type_id = int(request.POST['type'])
    status_id = int(request.POST['status'])
    order = request.POST['order']
    desc = ('desc' in request.POST)
    product_id = int(request.POST['product'])
    page = int(request.POST['page'])
    
    if desc:
        o = '-' + order
    else:
        o = '+' + order
    
    # Rediriger
    return HttpResponseRedirect('demand-2-%i-%i-%i%s-%i.html' % (
        type_id,
        status_id,
        product_id,
        o,
        page))
        
def view(request, demand_id, page):
    # Afficher une demande
    demand_id = int(demand_id)
    page = int(page)
    
    try:
        demand = Demand.objects \
            .select_related('reporter', 'type', 'product', 'component', 'product_version', 'fixed_in', 'platform', 'platform_version', 'architecture', 'status', 'priority', 'topic') \
            .get(pk=demand_id)
    except Demand.DoesNotExist:
        raise Http404
    
    # Prendre les demandes liées
    relations = Relation.objects \
        .select_related('maindemand', 'subdemand', 'maindemand__status', 'subdemand__status') \
        .filter(Q(maindemand__id=demand_id) | Q(subdemand__id=demand_id)) \
        .order_by('type', 'maindemand')
    
    for rel in relations:
        if rel.type == 0:
            # Dépendance
            if rel.maindemand == demand:
                rel.type_title = _('Dépendances')
            else:
                rel.type_title = _('Bloque')
        elif rel.type == 1:
            # Liaison
            rel.type_title = _('Demandes liées')
        elif rel.type == 2:
            # Duplication
            rel.type_title = _('Doublons')
            
        if rel.maindemand == demand:
            rel.item = rel.subdemand
        else:
            rel.item = rel.maindemand
            
    
    # Prendre la liste des assignés
    assignees = Assignee.objects \
        .select_related('user') \
        .filter(demand=demand) \
        .order_by('type')
        
    # Prendre la liste des fichiers attachés
    attachments = Attachment.objects \
        .select_related('author') \
        .filter(demand=demand)
        
    # Configuration du forum
    config = {'demand': demand,
              'extends': 'demands/base.html',
              'relations': relations,
              'assignees': assignees,
              'attachments': attachments,
              'title': demand.title}
              
    # Affichage
    return list_posts(request, demand.topic, page, config, 'demands/view.html')
    
def viewattachment(request, attachment_id):
    # Afficher les informations d'un attachement
    attachment_id = int(attachment_id)
    
    try:
        attachment = Attachment.objects \
            .select_related('author', 'demand', 'demand__product', 'demand__type') \
            .get(pk=attachment_id)
    except Attachment.DoesNotExist:
        raise Http404
    
    if request.method == 'POST':
        # Vérifier les droits
        if request.user.is_authenticated() and (request.user.has_perm('demands.change_attachment') or attachement.author == request.user.get_profile()):
            attachment.invalidated = ('invalidated' in request.POST)
            attachment.save()
            
            messages.add_message(request, messages.INFO, _("Attachement modifié avec succès"))
            return HttpResponseRedirect("demand-5-%i.html" % attachment_id)
        else:
            raise Http404
    else:
        primarymime = attachment.mimetype.split('/')[0]
        
        # Si le mime est du texte, alors l'afficher avec coloration syntaxique
        content = ''
        
        if primarymime == 'text':
            fl = attachment.url
        
            fl.open(mode='rb')
            code = fl.read()
            fl.close()
            
            try:
                lexer = get_lexer_for_filename(fl.name, code)
            except:
                lexer = TextLexer()
            
            content = highlight(code, lexer, HtmlFormatter(linenos='table', cssclass='codehilite'))
        
        return tpl('demands/viewattachment.html',
            {'attachment': attachment,
            'primarymime': primarymime,
            'content': content}, request)

def downloadattachment(request, attachment_id):
    # Télécharger directement un attachement
    attachment_id = int(attachment_id)
    
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    
    # Ouvrir et lire le fichier
    fl = attachment.url
    
    fl.open(mode='rb')
    s = fl.read()
    fl.close()
    
    return HttpResponse(s, mimetype=attachment.mimetype)
    
@login_required
def addattachment(request, demand_id):
    # Ajout d'un attachement à une demande
    demand_id = int(demand_id)
    
    # Trouver la demande
    try:
        demand = Demand.objects \
            .select_related('type', 'product') \
            .get(pk=demand_id)
    except Demand.DoesNotExist:
        raise Http404
    
    if request.method == 'POST':
        form = AddAttachmentForm(request.POST, request.FILES)
            
        if form.is_valid():
            a = form.save(commit=False)
            a.author = request.user.get_profile()
            a.demand = demand
            a.invalidated = False
            a.save()
            
            messages.add_message(request, messages.INFO, _('Attachement ajouté'))
            return HttpResponseRedirect('demand-4-%i-1.html' % demand_id)
    else:
        form = AddAttachmentForm(initial={'mimetype': 'text/plain'})
    
    return tpl('demands/addattachment.html', 
        {'form': form,
         'demand': demand}, request)
    
@permission_required('demands.change_demand')
def handlerelated(request, demand_id):
    # Gérer les demandes liées
    demand_id = int(demand_id)
    
    # Trouver la demande
    try:
        demand = Demand.objects \
            .select_related('type', 'product') \
            .get(pk=demand_id)
    except Demand.DoesNotExist:
        raise Http404
    
    if request.method == 'POST':
        # Récupérer les ids des liaisons à supprimer
        ids = []

        for p in request.POST:
            if p.startswith('relation'):
                ids.append(int(p.split('[')[1][0:-1]))
        
        if len(ids) != 0:
            # Prendre toutes les relations qui correspondent
            Relation.objects.filter(id__in=ids).delete()
            
            messages.add_message(request, messages.INFO, _('Les relations demandées ont été supprimées'))
            
        # Voir si on ajoute une relation
        newrelation = request.POST['newrelation']
        
        try:
            newrelation = len(newrelation) and int(newrelation) # '' et 0 ==> 0. x ==> x
        except:
            raise Http404
        
        if newrelation != 0:
            newrelationtype = request.POST['newrelationtype']
            subdemand = get_object_or_404(Demand, pk=newrelation)
            
            # Créer la relation
            if newrelationtype == 'depend':
                rel = Relation(type=0, maindemand=demand, subdemand=subdemand)
            elif newrelationtype == 'block':
                rel = Relation(type=0, maindemand=subdemand, subdemand=demand)
            elif newrelationtype == 'duplicate':
                rel = Relation(type=2, maindemand=demand, subdemand=subdemand)
            elif newrelationtype == 'link':
                rel = Relation(type=1, maindemand=demand, subdemand=subdemand)
            else:
                raise Http404
            
            rel.save()
            messages.add_message(request, messages.INFO, _('La nouvelle relation a été ajoutée'))
        
        # Traitement fini, on redirige
        return HttpResponseRedirect('demand-4-%i-1.html' % demand_id)
    
    # Prendre la liste des demandes liées
    relations = Relation.objects \
        .select_related('maindemand', 'subdemand', 'maindemand__status', 'subdemand__status') \
        .filter(Q(maindemand__id=demand_id) | Q(subdemand__id=demand_id)) \
        .order_by('type', 'maindemand')
    
    for rel in relations:
        if rel.type == 0:
            # Dépendance
            if rel.maindemand == demand:
                rel.type_title = _('Dépend de')
            else:
                rel.type_title = _('Bloque')
        elif rel.type == 1:
            # Liaison
            rel.type_title = _('Liée à')
        elif rel.type == 2:
            # Duplication
            rel.type_title = _('Doublon de')
            
        if rel.maindemand == demand:
            rel.item = rel.subdemand
        else:
            rel.item = rel.maindemand
            
    # Afficher la template
    return tpl('demands/handlerelated.html',
        {'demand': demand,
         'relations': relations}, request)
         
@permission_required('demands.change_demand')
def handleassignees(request, demand_id):
    # Gérer les demandes liées
    demand_id = int(demand_id)
    
    # Trouver la demande
    try:
        demand = Demand.objects \
            .select_related('type', 'product') \
            .get(pk=demand_id)
    except Demand.DoesNotExist:
        raise Http404
    
    if request.method == 'POST':
        # Récupérer les ids des liaisons à supprimer
        ids = []

        for p in request.POST:
            if p.startswith('assignee'):
                ids.append(int(p.split('[')[1][0:-1]))
        
        if len(ids) != 0:
            # Prendre toutes les relations qui correspondent
            Assignee.objects.filter(id__in=ids).delete()
            
            messages.add_message(request, messages.INFO, _('Les assignations demandées ont été supprimées'))
            
        # Voir si on ajoute une relation
        newassignee = request.POST['newassignee']
        
        if len(newassignee) != 0:
            newassigneetype = request.POST['newassigneetype']
            
            # Créer la relation
            if newassigneetype == 'user':
                try:
                    user = Profile.objects.select_related('user').get(uname=newassignee)
                except Profile.DoesNotExist:
                    messages.add_message(request, messages.ERROR, _('L\'utilisateur demandé n\'existe pas'))
                    return HttpResponseRedirect('demand-9-%i.html' % demand_id)
                    
                a = Assignee(type=0, demand=demand, user=user, value=user.user.email)
            elif newassigneetype == 'email':
                a = Assignee(type=1, demand=demand, value=newassignee)
            elif newassigneetype == 'url':
                a = Assignee(type=2, demand=demand, value=newassignee)
            else:
                raise Http404
            
            a.save()
            messages.add_message(request, messages.INFO, _('La nouvelle assignation a été ajoutée'))
        
        # Traitement fini, on redirige
        return HttpResponseRedirect('demand-4-%i-1.html' % demand_id)
    
    # Prendre la liste des demandes liées
    assignees = Assignee.objects \
        .select_related('user') \
        .filter(demand=demand)
    
    for a in assignees:
        a.type_title = ASSIGNEE_TYPE[a.type]
            
    # Afficher la template
    return tpl('demands/handleassignees.html',
        {'demand': demand,
         'assignees': assignees}, request)

@login_required
def newdemand(request, type_id, product_id, component_id):
    # Créer une demande, étape 1
    type_id = int(type_id)
    product_id = int(product_id)
    component_id = int(component_id)
    
    if request.method == 'GET':
        return edit_step1(request, type_id, product_id, component_id, 0)
    else:
        demand_id = int(request.POST['demand_id'])
        platform_id = int(request.POST['platform_id'])
        product_id = int(request.POST['product_id'])
        type_id = int(request.POST['type_id'])
        
        if demand_id != 0 and not request.user.has_perm('demands.change_demand'):
            raise Http404
        
        if demand_id != 0:
            # Prendre la demande, mettre à jour ses informations, et revenir sur la page d'édition des demandes
            demand = get_object_or_404(Demand, pk=demand_id)
            pl = get_object_or_404(Platform, pk=platform_id)
            p = get_object_or_404(Product, pk=product_id)
            t = get_object_or_404(Type, pk=type_id)
            
            demand.platform = pl
            demand.product = p
            demand.type = t
            demand.save()
            
            return HttpResponseRedirect('demand-11-%i.html' % demand_id)
        else:
            # Simplement rediriger vers l'étape 2
            return HttpResponseRedirect('demand-12-%i-%i-%i-%i.html' % (type_id, product_id, component_id, platform_id))

@login_required
def setstep1(request, demand_id, component_id):
    # POST de l'étape 1
    demand_id = int(demand_id)
    component_id = int(component_id)
    
    if request.method != 'POST':
        raise Http404
    
    platform_id = int(request.POST['platform_id'])
    product_id = int(request.POST['product_id'])
    type_id = int(request.POST['type_id'])
    
    if demand_id != 0 and not request.user.has_perm('demands.change_demand'):
        raise Http404
    
    if demand_id != 0:
        # Prendre la demande, mettre à jour ses informations, et revenir sur la page d'édition des demandes
        demand = get_object_or_404(Demand, pk=demand_id)
        pl = get_object_or_404(Platform, pk=platform_id)
        p = get_object_or_404(Product, pk=product_id)
        t = get_object_or_404(Type, pk=type_id)
        
        demand.platform = pl
        demand.product = p
        demand.type = t
        demand.save()
        
        return HttpResponseRedirect('demand-11-%i.html' % demand_id)
    else:
        # Simplement rediriger vers l'étape 2
        return HttpResponseRedirect('demand-12-%i-%i-%i-%i.html' % (type_id, product_id, component_id, platform_id))

@permission_required('demands.change_demand')
def edit_demand(request, demand_id):
    # Éditer une demande
    demand_id = int(demand_id)
    
    if request.method == 'GET':
        return edit_step2(request, 0, 0, 0, 0, demand_id)
    else:
        title = request.POST['title']
        body = request.POST['body']
        type_id = int(request.POST['type_id'])
        product_id = int(request.POST['product_id'])
        component_id = int(request.POST['component_id'])
        pversion_id = int(request.POST['pversion_id'])
        platform_id = int(request.POST['platform_id'])
        platform_version_id = int(request.POST['platform_version_id'])
        arch_id = int(request.POST['arch_id'])
        
        if demand_id:
            status_id = int(request.POST['status_id'])
            priority_id = int(request.POST['priority_id'])
            done = int(request.POST['done'])
            done = done if done < 100 else 100
        
        fixed_in_id = request.POST.get('fixed_in_id', 'none')
        
        if fixed_in_id == 'none':
            fixed_in_id = None
        else:
            fixed_in_id = int(fixed_in_id)
        
        type = get_object_or_404(Type, pk=type_id)
        product = get_object_or_404(Product, pk=product_id)
        component = get_object_or_404(Component, pk=component_id)
        product_version = get_object_or_404(ProductVersion, pk=pversion_id)
        platform = get_object_or_404(Platform, pk=platform_id)
        platform_version = get_object_or_404(PlatformVersion, pk=platform_version_id)
        arch = get_object_or_404(Arch, pk=arch_id)
        
        if demand_id:
            status = get_object_or_404(Status, pk=status_id)
            priority = get_object_or_404(Priority, pk=priority_id)
            
            if fixed_in_id:
                fixed_in = get_object_or_404(ProductVersion, pk=fixed_in_id)
            else:
                fixed_in = None
                
            demand = get_object_or_404(Demand, pk=demand_id)
            demand.title = title
            demand.content = body
            demand.done = done
            demand.reporter = request.user.get_profile()
            demand.type = type
            demand.product = product
            demand.component = component
            demand.product_version = product_version
            demand.fixed_in = fixed_in
            demand.platform = platform
            demand.platform_version = platform_version
            demand.architecture = arch
            demand.status = status
            demand.priority = priority
            
            # TODO: Stats
            
            demand.save()
            messages.add_message(request, messages.INFO, _('La demande a été éditée'))
            return HttpResponseRedirect('demand-4-%i-1.html' % demand_id)
        else:
            pass

@login_required
def newdemand_step2(request, type_id, product_id, component_id, platform_id):
    # Passer à la deuxième étape quand on a créé la demande
    type_id = int(type_id)
    product_id = int(product_id)
    component_id = int(component_id)
    platform_id = int(platform_id)
    
    return edit_step2(request, type_id, product_id, component_id, platform_id, 0)

@permission_required('demands.change_demand')
def change_product(request, demand_id):
    # Changer le produit ou la plateforme d'une demande déjà existante
    demand_id = int(demand_id)
    
    return edit_step1(request, 0, 0, 0, demand_id)

def edit_step1(request, type_id, product_id, component_id, demand_id):
    # Afficher un formulaire permettant de choisir le produit et la plateforme d'une demande,
    # car on a besoin de ces informations pour sélectionner, dans step2, la version affectée du
    # produit ou de la plateforme.
    demand = None
    
    if demand_id != 0:
        try:
            demand = Demand.objects \
                .select_related('type', 'product') \
                .get(pk=demand_id)
        except Demand.DoesNotExist:
            raise Http404
        
        product_id = demand.product_id
        component_id = demand.component_id
        type_id = demand.type_id
        
    products = Product.objects.all()
    platforms = Platform.objects.all()
    types = Type.objects.all()
        
    return tpl('demands/edit_step1.html',
        {'demand': demand,
         'products': products,
         'platforms': platforms,
         'types': types,
         'demand_id': demand_id,
         'type_id': type_id,
         'component_id': component_id,
         'product_id': product_id}, request)

def edit_step2(request, type_id, product_id, component_id, platform_id, demand_id):
    # Deuxième phase de l'édition ou création d'une demande. On a maintenant son produit
    # et sa plateforme, ainsi que son type. On renseigne ici tous les autres champs.
    demand = None
    
    if demand_id != 0:
        try:
            demand = Demand.objects \
                .select_related('platform', 'product', 'type') \
                .get(pk=demand_id)
        except Demand.DoesNotExist:
            raise Http404
        
        pl = demand.platform
        p = demand.product
        t = demand.type
        
        type_id = t.id
        product_id = p.id
        component_id = demand.component_id
        platform_id = pl.id
        
    else:
        pl = get_object_or_404(Platform, pk=platform_id)
        p = get_object_or_404(Product, pk=product_id)
        t = get_object_or_404(Type, pk=type_id)
    
    # Différentes listes (TODO: Pas moyen de cacher toutes ces requêtes ?)
    pversions = ProductVersion.objects.filter(product=p)
    plversions = PlatformVersion.objects.filter(platform=pl)
    components = Component.objects.filter(product=p)
    archs = Arch.objects.all()
    status = None
    priorities = None
    
    if demand_id != 0:
        status = Status.objects.all()
        priorities = Priority.objects.all()
        
    return tpl('demands/edit_step2.html',
        {'demand': demand,
         'type_id': type_id,
         'product_id': product_id,
         'component_id': component_id,
         'platform_id': platform_id,
         'demand_id': demand_id,
         'platform': pl,
         'product': p,
         'type': t,
         'pversions': pversions,
         'plversions': plversions,
         'components': components,
         'archs': archs,
         'status': status,
         'priorities': priorities}, request)
        
#@permission_required('demands.add_demand')
#def post(request, action, type_or_demand_id):
    ## Poster/Proposer/Éditer une demande. type_or_demand_id est un paeramètre qui change en
    ## fonction de action, qui prend les valeurs suivantes :
    ##  - 1 : Poster une nouvelle demande dans type_id
    ##  - 2 : Proposer une nouvelle demande dans type_id
    ##  - 3 : Éditer une demande
    #action = int(action)
    #type_or_demand_id = int(type_or_demand_id)

    ## Vérifier que l'action est ok
    #if action < 1 or action > 3:
        #raise Http404

    ## Vérifier que l'utilisateur a bien le droit de faire ce qu'il fait
    #t = False
    
    #if action != 3:
        ## Prendre le type
        #t = get_object_or_404(Type, pk=type_or_demand_id)

        ## Vérifier
        #if action == 1 and not t.can_new:
            #raise Http404
        #elif action == 2 and not t.can_propose:
            #raise Http404

    #demand = False
    #if action == 3:
        #demand = get_object_or_404(Demand, pk=type_or_demand_id)

    ## Savoir si on peut définir l'avancement
    #can_set_done = False

    #if request.user.has_perm('demands.change_demand'):
        #can_set_done = True
    #elif action == 3:
        #if request.user.get_profile() == demand.assigned_to:
            #can_set_done = True
    
    #if request.method == 'POST':
        ## Poster la demande (ou l'éditer)
        #title = request.POST['title']
        #body = request.POST['body']
        #cat_id = request.POST['category']
        
        #if request.user.has_perm('demands.change_demand'):
            #priority_id = request.POST['priority']
            #status_id = request.POST['status']
            #target_version_id = request.POST['target_version']

        #done = 0
        #if can_set_done:
            #done = request.POST['done']

            #try:
                #done = int(done)
            #except ValueError:
                #done = 0

            #if done < 0: done = 0
            #if done > 100: done = 100
            
        #if action == 1 or action == 2:
            ## Créer un sujet
            #topic = Topic(author=request.user.get_profile(), 
                          #title=title, 
                          #subtitle='', 
                          #lang=request.LANGUAGE_CODE.split('_')[0],
                          #last_post_page=1, 
                          #num_posts=0, 
                          #stick=False, 
                          #closed=False, 
                          #resolved=False, 
                          #p_type=2, 
                          #parent_id=0)
            #topic.save()
            
            #demand = Demand(topic=topic, d_type=t, author=request.user.get_profile())

        ## Sauvegarder les champs de la demande
        #demand.title = title
        #demand.body = body
        #demand.done = done
        #demand.category_id = cat_id

        #if action == 2:
            #demand.url = request.POST['url']
            #demand.is_proposed = True

        #if request.user.has_perm('demands.change_demand'):
            #demand.priority_id = priority_id
            #demand.status_id = status_id
            #demand.target_version_id = target_version_id
        #else:
            ## Statut et priorités par défaut
            #demand.priority_id = 1
            #demand.status_id = 1

        ## Sauvegarder la demande
        #demand.save()
        
        ## Mettre à jour le sujet
        #if action == 1 or action == 2:
            #topic.parent_id = demand.id
            #topic.save()

        ## On a fini
        #messages.add_message(request, messages.INFO, _("La demande a été éxécutée avec succès"))
        #return HttpResponseRedirect("demand-5-%i-1.html" % demand.id)
        
    #else:
        #if action != 3:
            #type_id = type_or_demand_id
        #else:
            #type_id = demand.d_type_id

        ## Envoi de fichiers
        #upl = False
        
        #if action == 2:
            #upl = upload_url(request, D_TYPE_DEMANDS, 32*1024*1024, Demand.objects.count(), _('Demande'))

        ## On a besoin de la liste des catégories
        #categories = Category.objects.filter(d_type=type_id)

        ## Besoin aussi de la priorité, version cible et statut (pour le staff)
        #priorities = False
        #versions = False
        #status = False
        #if request.user.has_perm('demands.change_demand'):
            #priorities = Priority.objects.all()
            #versions = Distribution.objects.all()
            #status = Status.objects.all()
        
        ## Rendre la template
        #return tpl('demands/edit.html',
            #{'action': action,
             #'type': t,
             #'demand': demand,
             #'categories': categories,
             #'priorities': priorities,
             #'versions': versions,
             #'status': status,
             #'can_set_done': can_set_done,
             #'upl': upl,
             #'type_or_demand_id': type_or_demand_id}, request)