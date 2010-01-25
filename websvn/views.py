# -*- coding: utf-8 -*-
#
# views.py
# This file is part of Logram Website
#
# Copyright (C) 2009 - Denis Steckelmacher <steckdenis@logram-project.org>
# Copyright (C) 2009 - Cleriot Simon <malgon33@gmail.com>
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
from pyv4.general.functions import *

from django.conf import settings
from django.http import Http404

from pygments.lexers import guess_lexer_for_filename, get_lexer_by_name
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

import pysvn
import re
from datetime import datetime

_formatter = HtmlFormatter(cssclass='codehilite', linenos='table')

def showdir(request):
    # Afficher un dossier, dont le chemin est passé dans GET['p']

    # 1. Récupérer le chemin et la révision à afficher
    if 'p' in request.GET:
        path = request.GET['p']
    else:
        path = '/'

    if 'r' in request.GET and request.GET['r'] != 'HEAD':
        rev = pysvn.Revision(pysvn.opt_revision_kind.number, request.GET['r'])
        rev_specified = True
    else:
        rev = pysvn.Revision(pysvn.opt_revision_kind.head)
        rev_specified = False
    
    url = settings.WEBSVN_BASE + path

    #  2. Obtenir un client
    client = pysvn.Client()

    # 3. Lister les fichiers
    entries = client.ls(url, revision=rev)

    for entry in entries:
        if entry.kind == pysvn.node_kind.dir:
            entry.type = 'dir'
        elif entry.kind == pysvn.node_kind.file:
            entry.type = 'file'

        log = client.log(entry.name,limit=1)
        entry.log=log[0]['message'].split('\n')[0]

        if len(entry.log) > 40:
            entry.log = entry.log[0:36] + '...'

        entry.date = datetime.fromtimestamp(entry.time)
        entry.filename = entry.name.split('/')[-1]
        entry.path = '/' + '/'.join(entry.name.split('/')[4:])

    # 4. Trouver un dossier parent, s'il existe
    parent = False
    
    if not path == '/':
        parent = '/'.join(path.split('/')[0:-1])
        if parent == '': parent = '/'

    # 5. Récupérer le dernier élément de log du dossier
    log = client.log(url, limit=1, revision_start=rev)
    log = log[0]
    log['date'] = datetime.fromtimestamp(log['date'])

    # 6. Paramètre -r de SVN
    if not rev.number:
        rev = {'number': 'HEAD'}
        svnparam = ''
    else:
        svnparam = '-r%i' % rev.number

    # 7. Préparer le fil d'ariane
    pathparts = []
    tp = ''
    
    for p in path.split('/'):
        if p != '':
            tp += '/' + p
            pathparts.append({
                'text': p,
                'path': tp
            })

    # 8. Rendre la template
    return tpl('websvn/showdir.html',
        {'path': path,
         'rev': rev,
         'url': url,
         'parent': parent,
         'rev_specified': rev_specified,
         'log': log,
         'svnparam': svnparam,
         'pathparts': pathparts,
         'entries': entries}, request)

def showfile(request):
    # Afficher le contenu d'un fichier

    # 1. Récupérer le chemin et la révision à afficher
    if 'p' in request.GET:
        path = request.GET['p']
    else:
        raise Http404

    if 'r' in request.GET:
        rev = pysvn.Revision(pysvn.opt_revision_kind.number, request.GET['r'])
    else:
        rev = pysvn.Revision(pysvn.opt_revision_kind.head)

    url = settings.WEBSVN_BASE + path

    # 2. Client
    client = pysvn.Client()

    # 3. Récupérer le contenu du fichier et son dernier log
    content = client.cat(url, revision=rev)
    log = client.log(url, limit=1, revision_start=rev)
    log = log[0]
    log['date'] = datetime.fromtimestamp(log['date'])
    
    # 4. Remplacer la ligne de copyright par des étoiles, pour conserver l'anonymité des développeurs
    content = re.sub(r'(\s*[#"*]+\s*Copyright[^-]+-).*', r'\1 **** see the real file, not the webSVN one', content)

    # 4. Colorer le code
    try:
        lexer = guess_lexer_for_filename(path.split('/')[-1], content)
    except ClassNotFound:
        lexer = get_lexer_by_name('text', stripnl=True, encoding='UTF-8')
        
    content = highlight(content, lexer, _formatter)

    # 5. Paramètre -r de SVN
    if not rev.number:
        rev = {'number': 'HEAD'}
        svnparam = ''
    else:
        svnparam = '-r%i' % rev.number
    
    # 6. Préparer le fil d'ariane
    pathparts = []
    tp = ''
    
    for p in path.split('/'):
        if p != '':
            tp += '/' + p
            pathparts.append({
                'text': p,
                'path': tp
            })

    # 7. Rendre la template
    return tpl('websvn/showfile.html',
        {'url': url,
         'path': path,
         'rev': rev,
         'content': content,
         'svnparam': svnparam,
         'pathparts': pathparts,
         'log': log}, request)
        
def showlog(request):
    # Afficher le log d'un fichier ou dossier
    client = pysvn.Client()

    # 1. Récupérer le chemin à afficher
    if 'p' in request.GET:
        path = request.GET['p']
    else:
        raise Http404

    url = settings.WEBSVN_BASE + path

    # 2. Récupérer le log
    log = client.log(url)

    for element in log:
        element['date'] = datetime.fromtimestamp(element['date'])

    # 3. Savoir si c'est un fichier ou un dossier
    info = client.info2(url, recurse=False)[0][1]

    if info['kind'] == pysvn.node_kind.file:
        is_file = True
    else:
        is_file = False
    
    # 4. Préparer le fil d'ariane
    pathparts = []
    tp = ''
    
    for p in path.split('/'):
        if p != '':
            tp += '/' + p
            pathparts.append({
                'text': p,
                'path': tp
            })

    # 5. Rendre la template
    return tpl('websvn/showlog.html',
        {'path': path,
         'is_file': is_file,
         'pathparts': pathparts,
         'log': log}, request)