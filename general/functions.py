# -*- coding: utf-8 -*-
#
# functions.py
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
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.cache import cache

from django.utils.translation import gettext_lazy as _

import markdown
import hashlib
import datetime

from pygments import highlight
from pygments.lexers import *
from pygments.formatters import HtmlFormatter

D_TYPE_FORUM = 1
D_TYPE_WIKI = 2
D_TYPE_DEMANDS = 3

SMILEYS = [
        (':angel: ', '/style/smilies/ange.png'),
        (':angry: ', '/style/smilies/angry.gif'),
        ('o_O ', '/style/smilies/blink.gif'),
        (';) ', '/style/smilies/clin.png'),
        (':evil: ', '/style/smilies/diable.png'),
        (':D ', '/style/smilies/heureux.png'),
        ('^^ ', '/style/smilies/hihi.png'),
        (':o ', '/style/smilies/huh.png'),
        (':p ', '/style/smilies/langue.png'),
        (':magician: ', '/style/smilies/magicien.png'),
        ('x( ', '/style/smilies/mechant.png'),
        (':ninja: ', '/style/smilies/ninja.png'),
        ('&gt;_&lt; ', '/style/smilies/pinch.png'),
        (':pirate: ', '/style/smilies/pirate.png'),
        (':\'( ', '/style/smilies/pleure.png'),
        (':lol: ', '/style/smilies/rire.gif'),
        (':euh: ', '/style/smilies/rouge.png'),
        (u':-° ', '/style/smilies/siffle.png'),
        (':) ', '/style/smilies/smile.png'),
        ('B-) ', '/style/smilies/soleil.png'),
        (':( ', '/style/smilies/triste.png'),
        (':unsure: ', '/style/smilies/unsure.gif'),
        (':O ', '/style/smilies/waw.png'),
        (':zorro: ', '/style/smilies/zorro.png'),
    ]
    
pygments_format = {
    'abap': _('ABAP'),
    'antlr': _('ANTLR'),
    'antlr-as': _('ANTLR avec cible ActionScript'),
    'antlr-csharp': _('ANTLR avec cible C#'),
    'antlr-cpp': _('ANTLR avec cible CPP'),
    'antlr-java': _('ANTLR avec cible Java'),
    'antlr-objc': _('ANTLR avec cible ObjectiveC'),
    'antlr-perl': _('ANTLR avec cible Perl'),
    'antlr-python': _('ANTLR avec cible Python'),
    'antlr-ruby': _('ANTLR avec cible Ruby'),
    'as': _('ActionScript'),
    'as3': _('ActionScript 3'),
    'apacheconf': _('ApacheConf'),
    'applescript': _('AppleScript'),
    'bbcode': _('BBCode'),
    'bash': _('Bash'),
    'console': _('Bash Session'),
    'bat': _('Batchfile'),
    'befunge': _('Befunge'),
    'boo': _('Boo'),
    'brainfuck': _('Brainfuck'),
    'c': _('C'),
    'csharp': _('C#'),
    'cpp': _('C++'),
    'cmake': _('CMake'),
    'css': _('CSS'),
    'css+django': _('CSS+Django/Jinja'),
    'css+genshitext': _('CSS+Genshi Text'),
    'css+mako': _('CSS+Mako'),
    'css+myghty': _('CSS+Myghty'),
    'css+php': _('CSS+PHP'),
    'css+erb': _('CSS+Ruby'),
    'css+smarty': _('CSS+Smarty'),
    'cheetah': _('Cheetah'),
    'clojure': _('Clojure'),
    'common-lisp': _('Common Lisp'),
    'cython': _('Cython'),
    'd': _('D'),
    'dpatch': _('Darcs Patch'),
    'control': _('Fichier de Contrôle Debian'),
    'sourceslist': _('Liste de sources Debian'),
    'delphi': _('Delphi'),
    'diff': _('Diff'),
    'django': _('Django/Jinja'),
    'dylan': _('Dylan'),
    'erb': _('ERB'),
    'ragel-em': _('Ragel Embarqué'),
    'erlang': _('Erlang'),
    'erl': _('Erlang erl session'),
    'evoque': _('Evoque'),
    'fortran': _('Fortran'),
    'gas': _('GAS'),
    'glsl': _('GLSL'),
    'genshi': _('Genshi'),
    'genshitext': _('Genshi Text'),
    'pot': _('Gettext Catalog'),
    'Cucumber': _('Gherkin'),
    'gnuplot': _('Gnuplot'),
    'go': _('Go'),
    'groff': _('Groff'),
    'html': _('HTML'),
    'html+cheetah': _('HTML+Cheetah'),
    'html+django': _('HTML+Django/Jinja'),
    'html+evoque': _('HTML+Evoque'),
    'html+genshi': _('HTML+Genshi'),
    'html+mako': _('HTML+Mako'),
    'html+myghty': _('HTML+Myghty'),
    'html+php': _('HTML+PHP'),
    'html+smarty': _('HTML+Smarty'),
    'haskell': _('Haskell'),
    'ini': _('INI'),
    'irc': _('IRC logs'),
    'io': _('Io'),
    'java': _('Java'),
    'jsp': _('Java Server Page'),
    'js': _('JavaScript'),
    'js+cheetah': _('JavaScript+Cheetah'),
    'js+django': _('JavaScript+Django/Jinja'),
    'js+genshitext': _('JavaScript+Genshi Text'),
    'js+mako': _('JavaScript+Mako'),
    'js+myghty': _('JavaScript+Myghty'),
    'js+php': _('JavaScript+PHP'),
    'js+erb': _('JavaScript+Ruby'),
    'js+smarty': _('JavaScript+Smarty'),
    'llvm': _('LLVM'),
    'lighty': _('Lighttpd configuration file'),
    'lhs': _('Literate Haskell'),
    'logtalk': _('Logtalk'),
    'lua': _('Lua'),
    'moocode': _('MOOCode'),
    'mxml': _('MXML'),
    'basemake': _('Makefile'),
    'make': _('Makefile'),
    'mako': _('Mako'),
    'matlab': _('Matlab'),
    'matlabsession': _('Matlab session'),
    'minid': _('MiniD'),
    'modelica': _('Modelica'),
    'trac-wiki': _('MoinMoin/Trac Wiki markup'),
    'mupad': _('MuPAD'),
    'mysql': _('MySQL'),
    'myghty': _('Myghty'),
    'nasm': _('NASM'),
    'newspeak': _('Newspeak'),
    'nginx': _('Fichier de Configuration Nginx'),
    'numpy': _('NumPy'),
    'ocaml': _('OCaml'),
    'objective-c': _('Objective-C'),
    'ooc': _('Ooc'),
    'php': _('PHP'),
    'pov': _('POVRay'),
    'perl': _('Perl'),
    'prolog': _('Prolog'),
    'python': _('Python'),
    'python3': _('Python 3'),
    'py3tb': _('Python 3.0 Traceback'),
    'pytb': _('Python Traceback'),
    'pycon': _('Python console session'),
    'rebol': _('REBOL'),
    'rhtml': _('RHTML'),
    'ragel': _('Ragel'),
    'ragel-c': _('Ragel avec hôte C'),
    'ragel-cpp': _('Ragel avec hôte CPP'),
    'ragel-d': _('Ragel avec hôte D'),
    'ragel-java': _('Ragel avec hôte Java'),
    'ragel-objc': _('Ragel avec hôte Objective C'),
    'ragel-ruby': _('Ragel avec hôte Ruby'),
    'raw': _('Raw token data'),
    'redcode': _('Redcode'),
    'rb': _('Ruby'),
    'rbcon': _('Ruby irb session'),
    'splus': _('S'),
    'sql': _('SQL'),
    'scala': _('Scala'),
    'scheme': _('Scheme'),
    'smalltalk': _('Smalltalk'),
    'smarty': _('Smarty'),
    'squidconf': _('SquidConf'),
    'tcl': _('Tcl'),
    'tcsh': _('Tcsh'),
    'tex': _('TeX'),
    'text': _('Text only'),
    'vb.net': _('VB.net'),
    'vala': _('Vala'),
    'vim': _('VimL'),
    'xml': _('XML'),
    'xml+cheetah': _('XML+Cheetah'),
    'xml+django': _('XML+Django/Jinja'),
    'xml+evoque': _('XML+Evoque'),
    'xml+mako': _('XML+Mako'),
    'xml+myghty': _('XML+Myghty'),
    'xml+php': _('XML+PHP'),
    'xml+erb': _('XML+Ruby'),
    'xml+smarty': _('XML+Smarty'),
    'xslt': _('XSLT'),
    'yaml': _('YAML'),
    'aspx-cs': _('aspx-cs'),
    'aspx-vb': _('aspx-vb'),
    'c-objdump': _('c-objdump'),
    'cpp-objdump': _('cpp-objdump'),
    'd-objdump': _('d-objdump'),
    'objdump': _('objdump'),
    'rst': _('reStructuredText'),
    'sqlite3': _('sqlite3con'),
}

pygments_format_list = pygments_format.items()
pygments_format_list.sort()

#Rend une template, en fournissant un contexte
def tpl(name, args, request):
    # Style à utiliser
    if request.user.is_anonymous():
        # Style par défaut
        style = '/style/default'
    else:
        style = request.session.get('style', False)
        
        if not style:
            style = request.user.get_profile().style
            request.session['style'] = style

    # Enregistrer l'activité
    from pyv4.general.models import Activity
    act = Activity(ip=request.META.get('REMOTE_ADDR'), template=name)
    act.date = datetime.datetime.now()
    
    if not request.user.is_anonymous():
        act.user = request.user.get_profile()
        
    act.save()

    # Rendre la template
    return render_to_response(name, args, context_instance=RequestContext(request, {
        'style': style,
        'settings': settings}))

def lcode(text):
    h = hash(text)
    
    rs = cache.get('lcode_%i' % h, False)

    markdown.TAB_LENGTH = 4 # Tabulation normale

    if rs == False:
        rs = markdown.markdown(force_unicode(text.replace('\\', '\\\\')), ['toc', 'def_list', 'tables', 'codehilite', 'wikilinks(base_url=/wiki-,end_url=.html'], True)
        
        # Gérer les smileys
        
        for smiley in SMILEYS:
            rs = rs.replace(smiley[0], ' <img src="%s" alt="%s" class="smiley" /> ' % (smiley[1], smiley[0]))

        cache.set('lcode_%i' % h, rs)

    return rs
    
def highlight_code(code, lang):
    if lang == 'auto':
        lexer = guess_lexer(code)
    else:
        try:
            lexer = get_lexer_by_name(lang)
        except:
            try:
                lexer = guess_lexer(code)
            except:
                lexer = PythonLexer()
    
    return highlight(code, lexer, HtmlFormatter(linenos='table', cssclass='codehilite'))

# Adaptation en Python de get_list_page de Winzou, sur le SdZ
def get_list_page(page, nb_pages, nb):
    list_page = []
    i = 1
    while i <= nb_pages:
        if ((i < nb) or (i > nb_pages - nb) or ((i < page + nb) and (i > page - nb))):
            list_page.append(i)
        else:
            if i >= nb and i <= (page - nb):
                i = page - nb
                list_page.append('...')
            elif i >= (page + nb) and i <= (nb_pages - nb):
                i = nb_pages - nb
                list_page.append('...')
        i = i + 1
    return list_page
    
def list_languages(current):
    rs = ''
    
    for (key, value) in pygments_format_list:
        enabled = (current == key)
        
        if enabled:
            enabled = ' selected="selected"'
        else:
            enabled = ''
            
        rs += '<option value="%s"%s>%s</option>' % (key, enabled, value)

    return rs

# Hash en fonction de l'ID d'un dossier et du quota du sous-dossier qui sera créé
def upload_hash(parent_type, quota, uniqid):
    s = str(int(parent_type) + 35)
    s += 'yUU'
    s += settings.UPLOAD_PASSWORD
    s += str(int(quota) - 376 * 2)
    s += settings.UPLOAD_PASSWORD
    s += str(uniqid)
    s += '8uudC'

    return hashlib.sha1(s).hexdigest()

def upload_url(request, parent_type, quota, uniqid, dirname):
    h = upload_hash(parent_type, quota, uniqid)
    parent_type = int(parent_type)
    quota = int(quota)
    uniqid = int(uniqid)

    request.session['create_dir_name'] = dirname
    
    return 'upload-4-%s-%i-%i-%i.html' % (h, parent_type, quota, uniqid)

# Du code de django, BSD
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    import re
    value = unicodedata.normalize('NFKD', unicode(value)).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

def get_poll(request, poll):
    from pyv4.forum.models import Choice, UserChoice
    # Retourner un sondage
    rs = {}
    
    choices = Choice.objects \
        .filter(poll=poll)
            
    # Explorer les choix et faire quelques traitements
    poll_total = 0
    for choice in choices:
        poll_total += choice.votes
            
    for choice in choices:
        if poll_total != 0:
            p = choice.votes * 100 / poll_total
            if p > 100:
                choice.percent = 100
            elif p < 0:
                choice.percent = 0
            else:
                choice.percent = p
        else:
            choice.percent = 0
        
    # Savoir si on peut voter
    if request.user.is_anonymous():
        poll_can_vote = False
    else:
        user_choices = UserChoice.objects \
                        .filter(user=request.user.get_profile(), choice__poll=poll)
                        
        poll_can_vote = (user_choices.count() == 0)
    
    # Construire le résultat
    rs['choices'] = choices
    rs['question'] = poll.question
    rs['id'] = poll.id
    rs['can_vote'] = poll_can_vote
    rs['total'] = poll_total
    rs['object'] = poll
    
    return rs