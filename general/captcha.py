# -*- coding: utf-8 -*-
#
# views.py
# This file is part of Logram Website
#
# Copyright (C) 2010 - Fabien Vicente <h4o@ouverta.fr>
# Copyright (C) 2010 - Denis Steckelmacher <steckdenis@logram-project.org>
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

import time
import random
import hashlib
import Image,ImageFont, ImageDraw
import os

from django.http import HttpResponse

#function random_rgb()
#return  : string with a random color, but *never* red
def random_rgb():
     return 'rgb(' + \
        str(random.randint(64,192)) + ',' + \
        str(random.randint(64,192)) + ',' + \
        str(random.randint(64,192)) + ' )' 

#function captcha_image(str p, int letters, int index)
#p       : complete string to write, it must be 6 character long
#g_color : color of the good letters
#return  :  dictionary with the image captcha ('image'), the selected text ('selected' ;)  and the text color ('color')
def captcha_image(p, g_color):
    fonts = os.listdir('TTF')
    random.shuffle(fonts)
    image = Image.new("RGB", (220, 64), "White")
    draw = ImageDraw.Draw(image)
    
    i = 0
    font = []
    s = ''

    # Create one font per letter
    while i < len(fonts):
        if fonts[i].endswith('.ttf'):
            font.append(ImageFont.truetype('TTF/' + fonts[i], random.randint(40,43)))
        i += 1
        
    # Draw the colored lines on the image
    i = 0
    end = random.randint(8,12)
    
    while i < end:
        draw.line(
        (
            random.randint(0,220), 
            random.randint(0,64), 
            random.randint(0,220), 
            random.randint(0,64)
        ) ,fill=random_rgb())
        
        i+=1
        
    # Draw the letters
    randforce = random.randint(0,6)
    i = 0
    
    while i < len(p):
        if random.randint(0,3) <= 1 or i == randforce:
            color = g_color
            s += p[i]
        else:
            color = random_rgb()
            
        draw.text((i*30+25, 10), p[i], font=font[i],fill = color)
        i += 1
        
    del draw
    
    return {
        'image':image,
        'selected':s
    }

#function random_letters()
#return: the text rand
def random_letters():
    p = hashlib.sha224(time.ctime() + str(random.randint(0,1000))).hexdigest()
    p = p[0:6] # 6 letters only
    p = p.upper()
    i = 0
    
    while i < len(p):
        # we don't want 0, it can be confunded with o, and we save the "selected" characteres 
        if(p[i] == '0'):
            p = p[0:i] + random.choice('ABCDEFGHIJKLMOPQRSTUVXYZ123456789') + p[i+1:6] #I can't use the strings as array

        i += 1
        
    return p
    
def captcha(request):
    # 1. Find random letters
    letters = random_letters()
    
    # 2. Read in the session the color of the good letters
    colour = request.session.get('captcha_good_color_rgb', 'rgb(255, 0, 0)')
    
    # 2. Create a nice image with them
    infos = captcha_image(letters, colour)
    image = infos['image']
    
    # 3. Save in the session the good result
    request.session['captcha_good_letters'] = infos['selected']
    
    # 4. Display the image
    response = HttpResponse(mimetype='image/png')
    response['cache-control'] = 'no-store, no-cache, must-revalidate'
    image.save(response, 'PNG')
    
    return response
