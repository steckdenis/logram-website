# -*- coding: utf-8 -*-
#
# views.py
# This file is part of Logram Website
#
# Copyright (C) 2009-2010 - Takahashi Keisuke <keisuke@logram-project.org>
# Copyright (C) 2010      - Denis Steckelmacher <steckdenis@logram-project.org>
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
import uuid
import re
import difflib
from datetime import *
from time import *
from calendar import *

from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages

from pyv4.general.functions import *
from pyv4.pastebin.models import *
from pyv4.forum.models import Alert
from pyv4.forum.forms import *

# Page d'accueil
def index(request):
    # On supprime les pastes dépassés
    nbe = Pastebin.objects.all().count()
    old = Pastebin.objects.all().order_by('created')
    i=0
    
    # Les dates de fin sont passées
    while i<nbe:
        if old[i].ended < datetime.now():
            old[i].delete()
            nbe-=1
        i+=1
        
    # Récupération des 10 derniers pastes
    latest_paste = cache.get('pastebin_latest', False)
    latest_paste = False
    if not latest_paste:
        latest_paste = Pastebin.objects.all().order_by('-created')[:10]
        # Ecris le cache de 5min
        cache.set('pastebin_latest', latest_paste, 5*60)
        
    return tpl('pastebin/index.html', {
        'latest_paste': latest_paste,
        'formats': list_languages('none'),
    }, request)


# Sauvegarde le paste
def save(request):
    # Vérification de la method utilisé
    if request.method != 'POST':
        raise Http404
    
    # Récupère les variables
    format = request.POST['format']
    contents = request.POST['body']
    fin = request.POST['fin']
    
    if request.POST['title']:
        title = request.POST['title']
    else:
        title = _('Sans titre')
    
    # On récupère l'uuid généré
    code = encodeUUID(fin)
    
    # On remplace les tabulations par des espaces
    contenu = contents.replace('\t', '    ')
    
    # Calcul de la date de fin
    ended = calc_end_date(fin)
        
    # Traitement
    if request.user.is_authenticated():
        Author = request.user.get_profile()
        paste = Pastebin(author=Author, format=format, contents=contenu, ended=ended, uniqid=code, title=title)
    else:
        # Paste anonyme
        paste = Pastebin(format=format, contents=contenu, ended=ended, uniqid=code, title=title)
    
    # Met a jour la BDD
    paste.save()
    
    # Renvoie sur le resultat du paste
    return HttpResponseRedirect('pastebin-3-%s.html' % code)


# Voir le paste
def view_paste(request, uniqid):
    try: # Teste la présence du paste
        paste = Pastebin.objects.get(uniqid=uniqid)
    except Pastebin.DoesNotExist: # il n'existe pas, on renvoie sur l'accueil
        return HttpResponseRedirect('pastebin-1.html')
    
    author_m = paste.author_m
        
    # L'utilisateur peut-il modifier le paste ?
    if request.user.is_authenticated():
        can_edit_paste = (request.user.has_perm('pastebin.edit_all_pastes') or paste.author == request.user.get_profile())
    else:
        can_edit_paste = False

    # Passage à la template
    data = {
        'uniqid': uniqid,
        'contents': paste.contents,
        'can_edit_paste': can_edit_paste,
        'paste': paste
    }
    
    # Gestion du diff
    if paste.author_m_id:
        contents_old = paste.contents_m

        # Generation du diff Html
        df = difflib.HtmlDiff().make_table(paste.contents_m.split('\n'), paste.contents.split('\n'), _('Ancienne version'), _('Nouvelle version'))
        
        # On enlève les nowrap
        df = df.replace('nowrap="nowrap"','')
        
        # Template pour le diff
        data['contents_old'] = contents_old
        data['difftable'] = df
    
    return tpl('pastebin/view.html', data, request)


# Modification d'un paste
@login_required
def modif(request, uniqid):
    try: # Teste la présence du paste et récupère les données.
        paste = Pastebin.objects.get(uniqid=uniqid)
    except Pastebin.DoesNotExist:
        return HttpResponseRedirect('pastebin-1.html')
        
    # Vérifier que l'utilisateur pouvait modifier le paste
    can_edit_paste = (request.user.has_perm('pastebin.edit_all_pastes') or paste.author == request.user.get_profile())
    
    if not can_edit_paste:
        raise Http404

    if request.method == 'POST':
        # On poste les modifications
        body = request.POST['body']
        title = request.POST['title']
        expires = request.POST['fin']
        format = request.POST['format']
        
        # Sauvegarder l'ancien contenu, pour le diff
        paste.contents_m = paste.contents
        paste.author_m = request.user.get_profile()
        
        # Nouveau contenu et titre
        paste.contents = body
        paste.title = title
        paste.format = format
        
        # Expiration
        ended = calc_end_date(expires)
        paste.ended = ended
        
        # Enregistrer le paste
        paste.save()
        messages.add_message(request, messages.INFO, _(u'Post «%s» modifié avec succès') % title)
        return HttpResponseRedirect('pastebin-3-%s.html' % paste.uniqid)
    else:
        # Afficher le formulaire
        return tpl('pastebin/modif.html', {
            'uniqid': uniqid,
            'body': paste.contents,
            'title': paste.title,
            'expires': paste.uniqid[0],
            'formats': list_languages(paste.format),
            'paste': paste,
        }, request)


@login_required
def my_pastes(request):
    try:
        paste = Pastebin.objects.filter(author=request.user.get_profile()).order_by('-created')
    except Pastebin.DoesNotExist:
        return HttpResponseRedirect('pastebin-1.html')  
    
    for p in paste:
        if len(p.contents) >= 250:
            p.contents = p.contents[:250]
            p.contents = re.sub('\s(.+)$', '...', p.contents)
            
    return tpl('pastebin/liste.html',{'paste': paste}, request)

# Téléchargement du paste
def download(request, uniqid):
    # On recupere les donnees, s'il existe toujours
    try:
        paste = Pastebin.objects.get(uniqid=uniqid)
    except Pastebin.DoesNotExist:
        raise Http404
    
    # Nom de fichier pour le navigateur
    file_name = slugify(paste.title) + '.txt'
    
    # Header pour tous les types de fichier text
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=' + file_name
    response.write(paste.contents)
    
    return response

# Créer une alerte
@permission_required('pastebin.add_alert')
def alert(request, uniqid):
    # Alerter les modérateurs
    if request.method == 'POST':
        form = AlertForm(request.POST)
            
        if form.is_valid():            
            pb = Pastebin.objects.get(uniqid=uniqid)
            # Créer l'alerte
            alert = Alert(paste=pb, author=request.user.get_profile(), comment=form.cleaned_data['comment'])
            alert.save()
            
            # On a fini
            messages.add_message(request, messages.INFO, _('Modérateurs alertés'))
            return HttpResponseRedirect('pastebin-3-%s.html' % uniqid)
    else:
        form = AlertForm()
            
    # Afficher le formulaire
    return tpl('pastebin/alert.html', 
        {'uniqid': uniqid,
         'form': form}, request)

         
# Calcul de date de fin
def calc_end_date(fin):
    # Calcul de la date de fin
    now = datetime.now()
    one_day = 24*60*60 #86400s
    
    if fin == 'w':
        end = now.fromtimestamp(mktime(gmtime()) + 7 * one_day) # Ajoute une semaine
    elif fin == 'm':
        end = now.fromtimestamp(mktime(gmtime()) + (monthrange(now.year,now.month)[1]) * one_day) # Ajoute un mois
    elif fin == 'n':
        # Un timestamp ne dépasse pas 2038
        Endedyear = now.year + 200 # Ajoute 200 ans
        end = datetime(Endedyear, now.month, now.day, now.hour, now.minute, now.second)
    else:
        end = now.fromtimestamp(mktime(gmtime()) + 1 * one_day) # Ajoute un jour, par défaut
    
    return end
    
        
# Encode le uuid
def encodeUUID(fin):
    # Generation uuid
    tmpUUID = uuid.uuid1()
    # On le transforme en string
    strUUID = str(tmpUUID)
    # On recupere les deux premières parties
    parties = strUUID.split('-')
    # On rajoute au debut le type: (d,w,m)
    return fin+parties[0]+parties[1]
