# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 by xt <xt@bash.no>
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

# This script colors nicks in IRC channels in the actual message
# not just in the prefix section.
# 
#
# History:
# 2010-03-24, xt
#   version 0.2: use ignore_channels when populating to increase performance.
# 2010-02-03, xt
#   version 0.1: initial

import weechat
import re
from time import time as now
w = weechat

SCRIPT_NAME    = "colorize_nicks"
SCRIPT_AUTHOR  = "xt <xt@bash.no>"
SCRIPT_VERSION = "0.2"
SCRIPT_LICENSE = "GPL"
SCRIPT_DESC    = "Use the weechat nick colors in the chat area"

settings = {
    "blacklist_channels"        : '',     # comma separated list of channels (use short_name)
    "blacklist_nicks"           : 'so,root',  # comma separated list of nicks
    "min_nick_length"           : '2',    # length
}


VALID_NICK = r'([@~&!%+])?([-a-zA-Z0-9\[\]\\`_^\{|\}]+)'
PREFIX_COLORS = {
        '@' : 'nicklist_prefix1',
        '~' : 'nicklist_prefix1',
        '&' : 'nicklist_prefix1',
        '!' : 'nicklist_prefix1',
        '%' : 'nicklist_prefix2',
        '+' : 'nicklist_prefix3',
}
ignore_channels = []
ignore_nicks = []

# Time of last run
LAST_RUN = 0

# Dict with every nick on every channel with its color as lookup value
colored_nicks = {}

def colorize_cb(data, modifier, modifier_data, line):
    ''' Callback that does the colorizing, and returns new line if changed '''

    global ignore_nicks, ignore_channels, colored_nicks
    if not 'irc_privmsg' in modifier_data:
        return line

    full_name = modifier_data.split(';')[1]
    server = full_name.split('.')[0]
    channel = '.'.join(full_name.split('.')[1:])
    # Check that privmsg is in a channel and that that channel is not ignored
    if not w.info_get('irc_is_channel', channel) or channel in ignore_channels:
        return line

    min_length = int(w.config_get_plugin('min_nick_length'))
    reset = w.color('reset')

    try:
        for words in re.findall(VALID_NICK, line):
            prefix, nick = words[0], words[1]
            # Check that nick is not ignored and longer than minimum length
            if len(nick) < min_length or nick in ignore_nicks:
                continue
            if nick in colored_nicks[server][channel]:
                nick_color = colored_nicks[server][channel][nick]
                line = line.replace(nick, '%s%s%s' %(nick_color, nick, reset))
    except KeyError, e:
        print '%s%s' %(e, colored_nicks)

    return line


def populate_nicks(*kwargs):
    ''' Fills entire dict with all nicks weechat can see and what color it has
    assigned to it. '''
    global colored_nicks, LAST_RUN


    # Only run max once per second
    if (now() - LAST_RUN) < 1:
        return w.WEECHAT_RC_OK

    colored_nicks = {}

    servers = w.infolist_get('irc_server', '', '')
    while w.infolist_next(servers):
        servername = w.infolist_string(servers, 'name')
        colored_nicks[servername] = {}
        my_nick = w.info_get('irc_nick', servername)
        channels = w.infolist_get('irc_channel', '', servername)
        while w.infolist_next(channels):
            nicklist = w.infolist_get('nicklist', w.infolist_pointer(channels, 'buffer'), '')
            channelname = w.infolist_string(channels, 'name')

            if channelname in ignore_channels:
                continue

            colored_nicks[servername][channelname] = {}
            while w.infolist_next(nicklist):
                nick = w.infolist_string(nicklist, 'name')
                if nick == my_nick:
                    nick_color = w.color(\
                            w.config_string(\
                            w.config_get('weechat.color.chat_nick_self')))
                else:
                    nick_color = w.info_get('irc_nick_color', nick)

                colored_nicks[servername][channelname][nick] = nick_color

            w.infolist_free(nicklist)

        w.infolist_free(channels)

    w.infolist_free(servers)

    # Update last run
    LAST_RUN = now()

    return w.WEECHAT_RC_OK

if __name__ == "__main__":
    if w.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                        SCRIPT_DESC, "", ""):
        # Set default settings
        for option, default_value in settings.iteritems():
            if not w.config_is_set_plugin(option):
                w.config_set_plugin(option, default_value)

        for key, value in PREFIX_COLORS.iteritems():
            PREFIX_COLORS[key] = w.color(w.config_string(w.config_get('weechat.look.%s'%value)))
        ignore_channels = w.config_get_plugin('blacklist_channels').split(',')
        ignore_nicks = w.config_get_plugin('blacklist_nicks').split(',')

        populate_nicks() # Run it once to get data ready until nicklist_change triggers
        w.hook_modifier('weechat_print', 'colorize_cb', '')
        w.hook_signal('nicklist_changed', 'populate_nicks', '')

