# -*- coding: utf-8 -*-
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.utils.cache import cache
from django.contrib.auth.models import User
from django.core.paginator import Paginator

from datetime import datetime
import time

from pyv4.general.functions import lcode as lc, get_list_page, list_languages, highlight_code
from pyv4.mp.models import UserTopic

register = template.Library()

ONLINE_TIMEOUT = 5*60

def mkcolorpseudo(pseudo, id, attr, uid):
    # Savoir si l'utilisateur est connecté
    online = (uid in cache.get('connected_users', []))
    style = cache.get('style_%i' % uid, '/style/default')
    
    if online:
        before = '<img class="login_image" src="%s" alt="" title="%s" /> ' % (style + '/img/user_online.png', _('En ligne'))
    else:
        before = '<img class="login_image" src="%s" alt="" title="%s" /> ' % (style + '/img/user_offline.png', _('Hors ligne'))
        
    return mark_safe(before + '<a href="user-1-%i.html" class="user_%s">%s</a>' % (id, attr, conditional_escape(pseudo)))

@register.filter
def color_pseudo(profile):
    # Colorie un pseudo et renvoie un lien vers son profil
    return mkcolorpseudo(profile.uname, profile.id, profile.main_group_name.lower(), profile.user_id)

@register.filter
def pagination(page, url):
    #page = Paginator.Page. L'url est de la forme "news-1-%i.html", %i est remplacé par les n° de page
    mlist = get_list_page(page.number, page.paginator.num_pages, 4)
    
    pagination = ''
    
    if page.has_previous():
        pagination += '<a href="%s">%s</a>' % (url % page.previous_page_number(), _('« Précédant'))
    
    for num in mlist:
        if num == page.number:
            pagination += '%i ' % num
        elif num == '...':
            pagination += num + ' '
        else:
            pagination += '<a href="%s">%i</a>' + (url % num, num)
    
    if page.has_next():
        pagination += '<a href="%s">%s</a>' % (url % page.next_page_number(), _('Suivant »'))
    
    return pagination

@register.filter
def format_date(date):
    #Retourne un timestamp sous forme "il y a 3s", "il y a 2min", "le .. a ..", "hier à ..", etc
    diff = datetime.now() - date

    # On specifie la difference de jour
    diffDay = datetime.now().day - date.day
    diffMonth = datetime.now().month - date.month
    diffYear = datetime.now().year - date.year 
    
    if diffYear == 0:
        if diffMonth != 0:
            return _('le %(d)i/%(mt)02i/%(y)i à %(h)ih%(m)02i') % {'d': date.date().day, 'mt': date.date().month, 'y': date.date().year, 'h': date.time().hour, 'm': date.time().minute}
        if diffDay == 0:
            if diff.seconds <= 60:
                return _('il y a %i secondes') % diff.seconds
            elif diff.seconds < (60*60):
                return ngettext('il y a %d minute', 'il y a %d minutes', diff.seconds / 60) % (diff.seconds / 60)
            elif diff.seconds < (4*60*60):
                # 4h maxi, sinon on ne voit plus rien
                return _('il y a %(h)ih%(m)02i') % {'h': diff.seconds / 60 / 60, 'm': diff.seconds % (60*60) / 60}
            else:
                # plus de 4h meme journee
                return _('aujourd\'hui à %(h)ih%(m)02i') % {'h': date.time().hour, 'm': date.time().minute}
        elif diffDay == 1:
            return _('hier à %(h)ih%(m)02i') % {'h': date.time().hour, 'm': date.time().minute}
        elif diffDay == -1:
            return _('demain à %(h)ih%(m)02i') % {'h': date.time().hour, 'm': date.time().minute}
        else:
            return _('le %(d)i/%(mt)02i/%(y)i à %(h)ih%(m)02i') % {'d': date.date().day, 'mt': date.date().month, 'y': date.date().year, 'h': date.time().hour, 'm': date.time().minute}
    else:
        return _('le %(d)i/%(mt)02i/%(y)i à %(h)ih%(m)02i') % {'d': date.date().day, 'mt': date.date().month, 'y': date.date().year, 'h': date.time().hour, 'm': date.time().minute}

@register.filter
def convertFormat(f):
    try:
        # 1. Ouvre le fichier
        file = open('pastebin/listeFormat.txt','r')
        
        # 2. Lire le fichier
        while True:
            ligne = file.readline()
            
            # Condition de sortie
            if ligne=='':
                break
                
            # On regarde s'il y a le format de la requête
            if ligne.startswith(str(f)):
                format = ligne.split('\t\t')[1]
                break
                
        file.close()
    except:
        format = _('Erreur lors de la lecture du format !')

    return format

@register.filter
def lcode(code):
    return mark_safe(lc(code))
lcode.is_safe = True

@register.tag(name='languages')
def do_languages(parser, token):
    return LanguagesNode()
    
class LanguagesNode(template.Node):
    def __init__(self):
        pass
        
    def render(self, context):
        return list_languages('none')

# Code venant de http://www.djangosnippets.org/snippets/1213/
@register.tag(name='code')
def do_code(parser,token):
    code = token.split_contents()[-1]
    nodelist = parser.parse(('endcode',))
    parser.delete_first_token()
    return CodeNode(code,nodelist)

# Code venant de http://www.djangosnippets.org/snippets/1213/
class CodeNode(template.Node):
    def __init__(self,lang,code):
        self.lang = lang
        self.nodelist = code
        
    def render(self,context):
        try:        
            language = template.Variable(self.lang).resolve(context)
        except:
            language = self.lang
        code = self.nodelist.render(context)
        
        return highlight_code(code, language)


class NumMpsNode(template.Node):
    def __init__(self):
        self.profile = template.Variable('user.get_profile')

    def render(self, context):
        # Obtenir le nombre de MPs en attente du membre
        prof = self.profile.resolve(context)

        cnt = cache.get('mps_%i' % prof.id, False)
        if not cnt:
            cnt = 0
            
            usertopics = UserTopic.objects \
                .select_related('topic') \
                .filter(user=prof, has_deleted=False)

            for ut in usertopics:
                if ut.last_read_post_id != ut.topic.last_message_id:
                    cnt += 1

            # Mettre à jour le cache
            cache.set('mps_%i' % prof.id, cnt + 1, 2*60) # 0 = False, on ne le veut pas, donc +1
        else:
            cnt = cnt - 1 # On a mis +1 au début, ici on le retire

        if cnt != 0:
            return '<strong>(%i)</strong>' % cnt
        else:
            return ''

class OnlinesNode(template.Node):
    def __init__(self):
        self.user = template.Variable('user')
        self.req = template.Variable('request')

    def render(self, context):
        user = self.user.resolve(context)
        request = self.req.resolve(context)
        
        anon = user.is_anonymous()
        ip = request.META.get('REMOTE_ADDR')
        
        f = open('onlines/activity.log', 'a')
        
        # Ajouter une ligne dedans avec nos informations
        if (anon):
            uid = 0
        else:
            uid = user.get_profile().id
            
        f.write('%f:%s:%i\n' % (time.time(), ip, uid))
        f.close()
        
        # Si on a les informations nécessaires dans le cache, les utiliser
        onlines = cache.get('online_users', False)
        
        if onlines != False:
            return '%i (%i)' % (onlines[0], onlines[1])
        
        # On doit gérer le fichier
        lines = {}
        anons = 0
        regs = 0
        cuids = []
        
        f = open('onlines/activity.log', 'r+')
        
        for l in f:
            parts = l.strip().split(':')
            
            # Si le timestamp n'est pas passé, ajouter la ligne à ce qu'on va sauvegarder
            old = float(parts[0])
            now = time.time()
            
            if now - old <= 300.0:
                # Vérifier qu'on n'a pas déjà cette IP d'enregistrée
                if not parts[1] in lines:
                    lines[parts[1]] = ':'.join(parts)
                    
                    if parts[2] == '0':
                        anons += 1
                    else:
                        regs += 1
                        cuids.append(int(parts[2]))
        
        # Ecrire le fichier
        f.close()
        
        f = open('onlines/activity.log', 'w')
        
        for l in lines.values():
            if len(l) != 0:
                f.write(l + '\n')
        
        f.close()
        
        # Ecrire le cache
        cache.set('online_users', [regs, anons], 5 * 60)
        cache.set('connected_users', cuids, 5 * 60)
        
        return '%i (%i)' % (regs, anons)

@register.tag(name='num_mps')
def do_num_mps(parser, token):
    return NumMpsNode()

@register.tag(name='onlines')
def do_onlines(parser, token):
    return OnlinesNode()
