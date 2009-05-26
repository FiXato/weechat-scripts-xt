''' Hotlist replacement. 

Usage: first, put [chanact] in your status bar items. 
" weechat.bar.status.items".

Then you can bind keys to buffers with
/key bind meta-w /buffer #weechat

And then it will show as [Act: w] on your status bar.
'''
# -*- coding: utf-8 -*-
# (this script requires WeeChat 0.3.0 or newer)
#
# History:
#
# 2009-05-16, xt <tor@bash.no>
#   version 0.2: added support for using keybindigs instead of names.   
# 2009-05-10, xt <tor@bash.no>
#   version 0.1: initial release.
#
# Copyright (c) 2009 by xt <tor@bash.no>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#

import weechat as w

SCRIPT_NAME    = "chanact"
SCRIPT_AUTHOR  = "xt <tor@bash.no>"
SCRIPT_VERSION = "0.2"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC    = "Hotlist replacement, use names and keybindings instead of numbers"

# script options
settings = {
    "lowest_priority"       : '0',
    'message'               : 'Act: ',
    'item_length'           : '8',
    'color_default'         : 'default',
    'color_1'               : 'white',
    'color_2'               : 'cyan',
    'color_3'               : 'lightcyan',
    'color_4'               : 'yellow',
    'color_8'               : 'cyan',
    'use_keybindings'       : '1',
    'delimiter'             : ','
}

hooks = (
    ('hotlist_*', 'chanact_update'),
    ('key_bind', 'chanact_update'),
    ('key_unbind', 'chanact_update'),
)

keydict = {}

if w.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                    SCRIPT_DESC, '', ''):
    for option, default_value in settings.iteritems():
        if not w.config_is_set_plugin(option):
            w.config_set_plugin(option, default_value)

    for hook, cb in hooks:
        w.hook_signal(hook, cb, '')

    keylist = w.infolist_get('key', '', '')
    # TODO: only build keydict on key changes
    if w.config_get_plugin('use_keybindings') == '1':
        while w.infolist_next(keylist):
            key = w.infolist_string(keylist, 'key')
# we dont want jump sequences
            if 'j' in key:
                continue
            key = key.replace('meta-', '')
# skip entries where buffer number = key, typically entries below 11
            if key.isdigit():
                continue
            command = w.infolist_string(keylist, 'command')
# we only care about commands that leads to buffers
            if command.startswith('/buffer'):
                command = command.replace('/buffer ', '')
                buffer = command.lstrip('*')
                keydict[buffer] = key
    w.infolist_free(keylist)

    w.bar_item_new('chanact', 'chanact_cb', '')

def chanact_cb(*kwargs):
    ''' Callback ran on hotlist changes '''
    global keydict


    result = w.config_get_plugin('message')
    hotlist = w.infolist_get('hotlist', '', '')
    while w.infolist_next(hotlist):
        priority = w.infolist_integer(hotlist, 'priority')

        if priority < int(w.config_get_plugin('lowest_priority')):
            continue

        number = str(w.infolist_integer(hotlist, 'buffer_number'))
        thebuffer = w.infolist_pointer(hotlist, 'buffer_pointer')
        name = w.buffer_get_string(thebuffer, 'short_name')

        color = w.config_get_plugin('color_default')
        if priority > 0:
            color = w.config_get_plugin('color_%s' %priority)

        if number in keydict:
            number = keydict[number]
            result += '%s%s%s' % (w.color(color), number, w.color('reset'))
        elif name in keydict:
            name = keydict[name]
            result += '%s%s%s' % (w.color(color), name, w.color('reset'))
        elif name:
            result += '%s%s%s:%s%s%s' % (
                    w.color('default'),
                    number,
                    w.color('reset'),
                    w.color(color),
                    name[:int(w.config_get_plugin('item_length'))],
                    w.color('reset'))
        else:
            result += '%s%s%s' % (
                    w.color(color),
                    number,
                    w.color(reset))
        result += w.config_get_plugin('delimiter')

    result = result.rstrip(w.config_get_plugin('delimiter'))
    w.infolist_free(hotlist)
    if result == w.config_get_plugin('message'):
        return ''
    return result

def chanact_update(*kwargs):
    ''' Hooked to hotlist changes '''

    w.bar_item_update('chanact')

    return w.WEECHAT_RC_OK
