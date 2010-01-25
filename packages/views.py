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
from pyv4.packages.models import *
from pyv4.general.functions import tpl, slugify
from pyv4.general.templatetags.general_tags import format_date
from pyv4.general.models import Profile

from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import gettext as _
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import smart_unicode, smart_str

import os

def string_of_package(package, language, type, strs):
    # Retourner la chaîne correspondant, ou en créer une nouvelle si elle n'existe pas

    for str in strs:
        if str.type == type and str.language == language:
            return str

    # On n'a pas trouvé
    str = String(language=language, package=package, type=type)

    return str

def str_of_package(package, language, type, strs):
    rs = string_of_package(package, language, type, strs)

    if rs.id == None and language != package.primarylang:
        rs = str_of_package(package, package.primarylang, type, strs)
    elif rs.id == None:
        return String()

    return rs

def index(request):
    # Page d'accueil des téléchargements, doit être claire
    
    # 1. Récupérer la liste des derniers paquets
    packages = Package.objects \
        .select_related('distribution', 'arch') \
        .order_by('-date')[:10]
        
    # 2. Récupérer la liste des téléchargements
    dws = DwVariant.objects \
        .select_related('download', 'download__cat') \
        .order_by('download__cat__weight', 'download__weight')
        
    # 3. Créer l'arbre des téléchargements, les templates ne sachant pas le faire
    downloads = {}
    
    for dw in dws:
        # Ajouter la catégorie
        if dw.download.cat.id in downloads:
            cat = downloads[dw.download.cat.id]
        else:
            cat = {
                'name': dw.download.cat.name,
                'description': dw.download.cat.description,
                'downloads': {}
            }
            downloads[dw.download.cat.id] = cat
            dwls = cat['downloads']
        
        # Ajouter le téléchargement
        if dw.download.id in dwls:
            dwl = dwls[dw.download.id]
        else:
            dwl = {
                'name': dw.download.name,
                'description': dw.download.description,
                'screen': dw.download.screen,
                'thb': dw.download.thb,
                'variants': {}
            }
            dwls[dw.download.id] = dwl
            variants = dwl['variants']
        
        # Ajouter la variante
        variants[dw.name] = dw
    
    # 4. Afficher la template
    return tpl('packages/index.html', 
        {'packages': packages,
         'downloads': downloads}, request)

def home(request):
    # Affichage des paquets des distributions et recherche de paquets
    
    # 1. Récupérer la liste des distributions
    distros = Distribution.objects.all()
    
    # 2. Rendre la template (c'est elle qui fait tout)
    return tpl('packages/home.html',
        {'distros': distros}, request)

def sections(request, distro_id):
    # Affichage des sections d'une distribution
    distro_id = int(distro_id)
    
    # 1. Récupérer la distribution
    distro = get_object_or_404(Distribution, pk=distro_id)
    
    # 2. Prendre la liste des sections
    sections = Section.objects.all()
    
    # 3. Rendre la template
    return tpl('packages/sections.html',
        {'distro': distro,
         'sections': sections}, request)

def listsection(request, distro_id, section_id):
    # Affichage des paquets d'une section
    distro_id = int(distro_id)
    section_id = int(section_id)
    
    # 1. Récupérer la distribution
    distro = get_object_or_404(Distribution, pk=distro_id)
    
    # 2. Récupérer la section
    section = get_object_or_404(Section, pk=section_id)
    
    # 3. Récupérer les versions (et leurs paquets) de la distribution dans la bonne section
    packages = Package.objects \
        .select_related('arch') \
        .filter(distribution=distro, section=section) \
        .order_by('name')
    
    # 4. Rendre la template
    return tpl('packages/list.html',
        {'distro': distro,
         'section': section,
         'packages': packages}, request)

def search(request):
    # Recherche q, method, distro
    
    # 1. Pas de GET, seulement des POST
    if request.method != 'POST':
        raise Http404
    
    # 2. Construire le début de la requete
    packages = Package.objects \
        .select_related('arch', 'distribution') \
        .order_by('-distribution', 'name')
    
    # 3. Récupérer les variables
    q = request.POST['q']
    method = request.POST['method']
    distro = request.POST['distro']
    
    # 4. Filtrer pour la distro (dans ce cas le order_by est ignoré)
    di = False
    
    if distro != 'all':
        packages = packages.filter(distribution=int(distro))
        
        di = get_object_or_404(Distribution, pk=distro)
    
    # 5. Filtrer suivant le critère de recherche
    if method == 'match':
        packages = packages.filter(name__exact=q)
    elif method == 'contains':
        packages = packages.filter(name__contains=q)
    elif method == 'starts':
        packages = packages.filter(name__startswith=q)
    elif method == 'ends':
        packages = packages.filter(name__endswith=q)
    else:
        raise Http404
    
    # 6. Rendre la template
    return tpl('packages/list.html', 
        {'packages': packages,
         'distro': di}, request)

def showpackage(request, package_id):
    # Afficher un paquet. Pas oublier de gérer distro_id=0
    package_id = int(package_id)
    
    # 1. Récupérer le paquet
    try:
        package = Package.objects \
            .select_related('arch', 'distribution', 'section') \
            .get(pk=package_id)
    except Package.DoesNotExist:
        raise Http404

    # 2. Splitter les chaînes
    package.depends = package.depends.split(';')
    package.conflicts = package.conflicts.split(';')
    package.suggests = package.suggests.split(';')
    package.provides = package.provides.split(';')
    package.replaces = package.replaces.split(';')

    # 3. Prendre les paquets qui ont le même nom pour proposer un joli
    #    menu à l'utilisateur
    pkgs = Package.objects \
        .select_related('arch', 'distribution') \
        .filter(name__exact=package.name) \
        .order_by('-distribution')

    # 4. Prendre les chaînes du paquet
    strings = String.objects.filter(package=package)

    package.title = str_of_package(package, request.LANGUAGE_CODE.split('-')[0], 0, strings).content
    package.short_desc = str_of_package(package, request.LANGUAGE_CODE.split('-')[0], 1, strings).content
    package.long_desc = str_of_package(package, request.LANGUAGE_CODE.split('-')[0], 2, strings).content
    
    # 5. Rendre la template
    return tpl('packages/view.html', 
        {'package': package,
         'pkgs': pkgs}, request)

def viewmirrors(request, package_id):
    # Afficher les mirroirs et proposer le téléchargement du paquet
    package_id = int(package_id)
    
    # 1. Récupérer le paquet
    package = get_object_or_404(Package, pk=package_id)
    
    # 2. Récupérer la liste des mirroirs
    mirrors = Mirror.objects.order_by('place')
    
    # 3. Rendre la template
    return tpl('packages/mirrors.html', 
        {'package': package,
         'mirrors': mirrors}, request)

def viewfiles(request, package_id):
    # Afficher les fichiers d'un paquet
    package_id = int(package_id)
    
    # 1. Récupérer le paquet
    package = get_object_or_404(Package, pk=package_id)
    
    # 2. Nom du fichier qui contient la liste des fichiers contenus dans l'archive
    filename = settings.LOCAL_MIRROR + package.download_url + '.files'

    # 3. Lire le fichier, et retirer tout ce qui ne doit pas être affiché
    f = open(filename)
    files = []

    for line in f:
        if line.startswith('__LOGRAM'):
            continue

        files.append(line)
    
    # 4. Rendre la template
    return tpl('packages/files.html',
        {'files': files,
         'pkg': package.name + '-' + package.version + ' (' + package.arch.name + ')'}, request)

