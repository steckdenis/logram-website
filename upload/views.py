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
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, Http404
from django.utils.translation import gettext as _
from django.conf import settings
from django.contrib import messages

from os import makedirs, path

from pyv4.upload.models import Directory, File
from pyv4.upload.forms import UploadForm
from pyv4.general.functions import tpl, upload_hash

import datetime

EXTS = ['png', 
        'gif', 
        'jpg', 
        'tga', 
        'svg', 
        'odt', 
        'c', 
        'cpp', 
        'xcf', 
        'bz2', 
        'zip',
        'tar', 
        'z', 
        'lzma', 
        'gz', 
        'txt',
        'diff',
        'patch',
        'xml']

@login_required
def viewdir(request, dir_id):
    # Affichage du contenu d'un dossier de l'utilisateur.
    # Si dir_id = 0, alors c'est son dossier principal
    # Affiche aussi un formulaire d'upload si le quota du dossier n'est pas dépassé
    dir_id = int(dir_id)
    
    if dir_id == 0:
        mdir = request.user.get_profile().main_dir
    else:
        mdir = get_object_or_404(Directory, pk=dir_id)
    
    #Vérifier que c'est bien le dossier de l'utilisateur
    if mdir.user != request.user:
        raise Http404
    
    # Vérifier le quota restant
    available = mdir.quota - mdir.used
    render_form = False
    form = 0
    
    if (available != 0 or request.user.has_perm('upload.ignore_quota')) and dir_id != 0:
        # Créer le formulaire d'envoi
        form = UploadForm()
        render_form = True
    
    # Obtenir la liste des fichiers et dossiers
    files = File.objects.filter(directory=mdir)
    dirs = Directory.objects.filter(parent=mdir)
    
    # Rendre la template
    return tpl('upload/view.html',
        {'dir': mdir,
         'dir_id': dir_id,
         'available': available,
         'form': form,
         'render_form': render_form,
         'files': files,
         'exts': EXTS,
         'dirs': dirs}, request)

@login_required
def upload(request, dir_id):
    if request.method != 'POST':
        raise Http404
    
    form = UploadForm(request.POST, request.FILES)
    dir_id = int(dir_id)
    
    if form.is_valid():
        mfl = request.FILES['path']
        mdir = get_object_or_404(Directory, pk=dir_id)
        
        # Vérifier l'extension
        ext = mfl.name.split('.')[-1].lower()
        
        if (not ext in EXTS) and (not request.user.has_perm('upload.ingore_extensions')):
            messages.add_message(request, messages.INFO, _('Extension non valide'))
            return HttpResponseRedirect('upload-1-%i.html' % dir_id)
        
        # Vérifier le quota
        if mdir.quota < (mdir.used + mfl.size) and not request.user.has_perm('upload.ignore_quota'):
            messages.add_message(request, messages.INFO, _('Quota dépassé'))
            return HttpResponseRedirect('upload-1-%i.html' % dir_id)
        
        # Vérifier que l'utilisateur envoie bien sans _son_ dossier
        if mdir.user != request.user:
            raise Http404
        
        # Mettre à jour le dossier
        mdir.used += mfl.size
        mdir.save()
        
        # Sauver le fichier
        fl = form.save(commit=False)
        fl.size = mfl.size
        fl.directory = mdir
        fl.save()
        
        messages.add_message(request, messages.INFO, _('Le fichier a été envoyé avec succès'))
        return HttpResponseRedirect('upload-1-%i.html' % dir_id)
    else:
        messages.add_message(request, messages.INFO, _('Le formulaire n\'était <strong>pas</strong> valide, veuillez le vérifier'))
        return HttpResponseRedirect('upload-1-%i.html' % dir_id)
 
def delete(request, file_id):
    try:
        fl = File.objects.select_related('directory').get(pk=file_id)
    except File.DoesNotExist:
        raise Http404
    
    mdir = fl.directory
    
    # Libérer de la place dans le dossier
    mdir.used = mdir.used - fl.size
    mdir.save()
    
    # Supprimer le fichier
    fl.delete()
    
    messages.add_message(request, messages.INFO, _('Le fichier a été supprimé'))
    return HttpResponseRedirect('upload-1-%i.html' % mdir.id)

@login_required
def newdir(request, hash, parent_type, quota, uniqid):
    # Créer un nouveau dossier avec un bon quota

    # Trouver le hash
    h = upload_hash(parent_type, quota, uniqid)

    # Vérifier que c'est le bon hash
    if h != hash:
        raise Http404

    # Vérifier qu'il n'y a encore aucun dossier avec ce hash et appartenant à l'utilisateur
    ds = Directory.objects.filter(user=request.user, sha1hash=hash)

    if len(ds) != 0:
        # Un dossier a déjà été créé
        return HttpResponseRedirect('upload-1-%i.html' % ds[0].id)

    # Trouver le dossier du membre qui a le bon uniqid
    try:
        d = Directory.objects.filter(user=request.user).get(type=parent_type)
    except Directory.DoesNotExist:
        raise Http404

    # Créer un nouveau dossier qui a ce dossier comme parent
    ndir = Directory(name=request.session['create_dir_name'], quota=quota, used=0, user=request.user, parent=d, sha1hash=hash)
    ndir.save()

    # Rediriger l'utilisateur vers ce dossier
    messages.add_message(request, messages.INFO, _('Le dossier a été créé'))
    return HttpResponseRedirect('upload-1-%i.html' % ndir.id)