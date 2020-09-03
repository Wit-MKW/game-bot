# libraries
import pycurl
import re
from io import BytesIO
import discord
from discord import *

def refresh(lang, from_cache):
    if (not from_cache):
        print('Refreshing for ' + lang + '!')
        body = ''
        if (lang == 'EN'):
            try:
                # download list
                bf = BytesIO()
                c = pycurl.Curl()
                c.setopt(c.URL, 'https://wiimmfi.de/stat?m=24')
                c.setopt(c.WRITEDATA, bf)
                c.perform()
                c.close()

                print('Downloaded Wiimmfi!')

                # convert to string
                body = bf.getvalue().decode('utf-8')
                
                # save to cache
                f = open('stat.html','w')
                f.write(body)
                f.close()
            except pycurl.error:
                # read from cache
                f = open('stat.html')
                body = f.read()
                f.close()
        else: # We're only able to get Wiimmfi's list in English, so no point querying it multiple times.
            f = open('stat.html')
            body = f.read()
            f.close()

        # convert to list
        body = body[body.index('<tr class="tr0">'):body.index('<tr class=total2>')]
        body = body.replace('</tr>','')
        body = body.replace('\n','')
        body = body.replace('<tr class="tr1">','<tr class="tr0">')
        body = body.split('<tr class="tr0">')[1:]

        # convert to list of lists
        # (what a mess)
        for i in range(len(body)):
            body[i] = body[i].replace('</td>','')
            body[i] = re.sub(r'<td title="@?[0-9a-z]+">','<td>',body[i])
            body[i] = re.sub(r'<td class="block">','<td>',body[i])
            body[i] = re.sub(
                r'<a href="/game-history/@?[0-9a-z]+" style="text-decoration:none"><span class="gmode-[0-9]">',
                '**',body[i])
            body[i] = body[i].replace('</span></a>','**')
            body[i] = body[i].replace('<br/>','\n')
            body[i] = re.sub(
                r'<img class="text-img" src="/images/[A-Za-z]+-34x16\.png"> ',
                '',body[i])
            body[i] = re.sub(
                r'<a href="[^"]+"><img class=text-img src=/images/game-info.svg width=18> ',
                '',body[i])
            body[i] = body[i].replace('</a>','')
            body[i] = body[i][:body[i].index('<td align=center>')]
            body[i] = body[i].split('<td>')[1:4]

        db = ''
        try:
            # download GameTDB's Wii(Ware) db
            bf = BytesIO()
            c = pycurl.Curl()
            c.setopt(c.URL, 'https://www.gametdb.com/wiitdb.txt?LANG=' + lang)
            c.setopt(c.WRITEDATA, bf)
            c.perform()
            c.close()

            print('Downloaded Wii!')

            # convert to string
            db = bf.getvalue().decode('utf-8')

            # download GameTDB's DS(iWare) db
            bf = BytesIO()
            c = pycurl.Curl()
            c.setopt(c.URL, 'https://www.gametdb.com/dstdb.txt?LANG=' + lang)
            c.setopt(c.WRITEDATA, bf)
            c.perform()
            c.close()

            print('Downloaded DS!')

            # convert to string
            db += bf.getvalue().decode('utf-8')

            # save to cache
            f = open('db_' + lang + '.txt','w')
            f.write(db)
            f.close()
        except pycurl.error:
            # read from cache
            f = open('db_' + lang + '.txt')
            db = f.read()
            f.close()

        # convert to list
        db = db.split('\n')[1:] # The first element isn't a real game.
        # Technically, that first element also appears for the DS db, but you try deleting that, or justifying the extra time it would take when it's not affecting anything, as Wiimmfi does not support a game with the ID TITL. In fact, T isn't even a valid first letter!

        # split IDs from titles
        for i in range(len(db)):
            db[i] = db[i].split(' = ')

        # add entry for this language
        games.append([])

        # create list of games
        for i in range(len(body)):
            print(body[i])
            print('Wrote ' + str(i) + ' games...', end='\r')
            forbidden = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            if ('USA' in body[i][1]):
                forbidden = forbidden.replace('E','') # NTSC, not Japan
                forbidden = forbidden.replace('M','') # American VC for Europe
            if ('PAL' in body[i][1]):
                forbidden = forbidden.replace('D','') # Germany
                forbidden = forbidden.replace('F','') # France
                forbidden = forbidden.replace('I','') # Italy
                forbidden = forbidden.replace('P','') # PAL
                forbidden = forbidden.replace('S','') # Spain
            if ('Japan' in body[i][1]):
                forbidden = forbidden.replace('J','') # Japan
                forbidden = forbidden.replace('L','') # Japanese VC for Europe
                forbidden = forbidden.replace('N','') # Japanese VC for USA
            if ('Korea' in body[i][1]):
                forbidden = forbidden.replace('K','') # Korea
                forbidden = forbidden.replace('Q','') # Korea, Japanese lang.
                forbidden = forbidden.replace('T','') # Korea, English lang.
            if (len(forbidden) == 26):
                forbidden = ' '
                for j in range(max(0,i-3),min(len(body),i+4)):
                    if (j == i):
                        continue
                    if (body[j][0].startswith(body[i][0][:3])):
                        if ('USA' in body[j][1]):
                            forbidden += 'EM'
                        if ('PAL' in body[j][1]):
                            forbidden += 'DFIPS'
                        if ('Japan' in body[j][1]):
                            forbidden += 'JLN'
                        if ('Korea' in body[j][1]):
                            forbidden += 'KQT'
            pt = body[i][0][:3] + '[^' + forbidden + ']([0-9A-Z]{2})?' # RMC[^ ]([0-9A-Z]{2})?
            start = len(games[-1])
            for game in db:
                if (re.fullmatch(pt,game[0]) != None):
                    if (start == len(games[-1])):
                        games[-1].append([game[0][:3] + '[^' + forbidden + ']' + game[0][4:],
                            body[i][2]]) # ['RMC[^ ]01', 'Mario Kart Wii', '**Full support**']
                    for j in range(start,len(games[-1])):
                        if (re.fullmatch(games[-1][j][0],game[0]) != None):
                            break
                        if (j == len(games[-1]) - 1):
                            games[-1].append([game[0][:3] + '[^' + forbidden + ']' + game[0][4:],
                                body[i][2]]) # ['RMC[^ ]01', 'Mario Kart Wii', '**Full support**']
        print('')
        for i in range(len(games[-1])):
            print(games[-1][i])
            print('Resolved ' + str(i) + ' games...', end='\r')
            pt = games[-1][i][0]
            del games[-1][i][0]
            for game in db:
                if (re.fullmatch(pt,game[0]) != None):
                    games[-1][i].append((game[0], game[1][:-1]))
        print('')
        write = ''
        for game in games[-1]:
            write += game[0].replace('\n','\\n')
            for tid in game[1:]:
                write += '\t' + tid[0] + '\t' + tid[1]
            write += '\n'
        f = open('games_' + lang + '.txt','w')
        f.write(write[:-1])
        f.close()
        print('Done!')
    else:
        f = open('games_' + lang + '.txt')
        read = f.read()
        f.close()
        games.append([])
        read = read.split('\n')
        for game in read:
            line = game.split('\t')
            games[-1].append([line[0].replace('\\n','\n')])
            for i in range(1,len(line),2):
                games[-1][-1].append((line[i],line[i+1]))

def write_pings():
    write = ''
    for ping in pings:
        write += str(ping[0])
        for game in ping[1]:
            write += '\t' + game
        write += '\n'
    f = open('pings.txt','w')
    f.write(write[:-1])
    f.close()

def read_pings():
    del pings[:]
    f = open('pings.txt')
    read = f.read()
    f.close()
    read = read.split('\n')
    for user in read:
        line = user.split('\t')
        pings.append((int(line[0]), []))
        for game in line[1:]:
            pings[-1][1].append(game)

def write_langs():
    write = ''
    for langset in langs:
        write += str(langset[0])
        for lang in langset[1]:
            write += '\t' + lang
        write += '\n'
    f = open('langs.txt','w')
    f.write(write[:-1])
    f.close()

def read_langs():
    del langs[:]
    f = open('langs.txt')
    read = f.read()
    f.close()
    read = read.split('\n')
    for user in read:
        langs.append([user[:user.index('\t')], user.split('\t')[1:]])

def read_translate(lang):
    f = open('translate_' + lang + '.txt')
    read = f.read()
    f.close()
    translate.append([])
    read = read.split('\n')
    for msg in read:
        translate[-1].append(msg.replace('\\n', '\n').replace('\\\\', '\\'))

games = []
pings = []
langs = []
translate = []

langs_p = ('EN', 'JA', 'FR', 'DE', 'ES', 'IT', 'NL', 'PT', 'RU', 'KO', 'ZHCN', 'ZHTW') # Changes when someone submits a translated db
flags_p = ('🇬🇧', '🇯🇵', '🇫🇷', '🇩🇪', '🇪🇸', '🇮🇹', '🇳🇱', '🇵🇹', '🇷🇺', '🇰🇷', '🇨🇳', '🇹🇼')
langs_s = ('EN', 'JA', 'FR', 'DE', 'ES', 'IT', 'NL',             'KO'                ) # Never changes
flags_s = ('🇬🇧', '🇯🇵', '🇫🇷', '🇩🇪', '🇪🇸', '🇮🇹', '🇳🇱', '🇰🇷', '❌')
langs_m = ('EN',                                                                     ) # Changes when someone submits translated messages
flags_m = ('🇬🇧',)

class Bot(discord.Client):
    async def on_ready(self):
        for lang in langs_p:
            refresh(lang, True)
        for lang in langs_m:
            read_translate(lang)
        read_pings()
        print('Profile: {0}'.format(self.user))
        await self.change_presence(status=Status.online)

    async def on_message(self, message):
        if (not message.content.startswith('^^')):
            return

        cmd = message.content[2:].split(' ')

        if (message.author.id == 291286384189374464 and cmd[0] == 'refresh'):
            guilds = self.guilds
            members = []
            for guild in guilds:
                lang_m = 'EN'
                for lang in langs:
                    if (lang[0] == guild.id):
                        lang_m = lang[1][2]
                        break
                index_m = langs_m.index(lang_m)
                for member in guild.members:
                    if (member in members):
                        continue
                    members.append(member)
                    member_m = 'EN'
                    for lang in langs:
                        if (lang[0] == member.id):
                            member_m = lang[1][2]
                            break
                    index_member = langs_m.index(member_m)
                    try:
                        await member.send(translate[index_member][19])
                    except:
                        print('Couldn\'t send to {0}'.format(member.user))
                for channel in guild.text_channels:
                    if (not guild.me.permissions_in(channel).send_messages):
                        continue
                    await channel.send(translate[index_m][19])
            await self.change_presence(status=Status.idle)
            del games[:]
            for lang in langs_p:
                refresh(lang, False)
            await self.change_presence(status=Status.online)
            return

        if (message.author.id == 291286384189374464 and cmd[0] == 'stop'):
            await self.change_presence(status=Status.invisible)
            await self.close()
            return

        if (cmd[0] == 'addping' and len(cmd) > 1):
            lang_p = 'EN'
            lang_s = 'EN'
            lang_m = 'EN'
            for lang in langs:
                if (lang[0] == message.author.id):
                    lang_p = lang[1][0]
                    lang_s = lang[1][1]
                    lang_m = lang[1][2]
                    break
            index_games = langs_p.index(lang_p)
            index_second = langs_p.index(lang_s)
            index_msg = langs_m.index(lang_m)
            for ping in pings:
                if (ping[0] == message.author.id):
                    if (cmd[1] in ping[1]):
                        await message.channel.send(translate[index_msg][0]) # EN: You already have a ping for that game!
                        return
                    break
            for i in range(len(games[index_games])):
                for j in range(1,len(games[index_games][i])):
                    if (games[index_games][i][j][0] == cmd[1]):
                        if (len(pings) == 0):
                            pings.append((message.author.id, [cmd[1]]))
                            write_pings()
                            if (lang_p == lang_s):
                                await message.channel.send(translate[index_msg][1].format(games[index_games][i][j][1])) # EN: Added a ping for _{0}_.
                            else:
                                await message.channel.send(translate[index_msg][14].format(games[index_games][i][j][1], games[index_second][i][j][1])) # EN: Added a ping for _{0}_ (_{1}_).
                            return
                        for k in range(len(pings)):
                            if (pings[k][0] != message.author.id):
                                if (k == len(pings) - 1):
                                    pings.append((message.author.id, [cmd[1]]))
                                    write_pings()
                                    if (lang_p == lang_s):
                                        await message.channel.send(translate[index_msg][1].format(games[index_games][i][j][1])) # EN: Added a ping for _{0}_.
                                    else:
                                        await message.channel.send(translate[index_msg][14].format(games[index_games][i][j][1], games[index_second][i][j][1])) # EN: Added a ping for _{0}_ (_{1}_).
                                    return
                                continue
                            pings[k][1].append(cmd[1])
                            write_pings()
                            if (lang_p == lang_s):
                                await message.channel.send(translate[index_msg][1].format(games[index_games][i][j][1])) # EN: Added a ping for _{0}_.
                            else:
                                await message.channel.send(translate[index_msg][14].format(games[index_games][i][j][1], games[index_second][i][j][1])) # EN: Added a ping for _{0}_ (_{1}_).
                            break
                        return
            await message.channel.send(translate[index_msg][2].format(cmd[1])) # EN: Invalid title ID: {0}.
            return

        if (cmd[0] == 'delping' and len(cmd) > 1):
            lang_p = 'EN'
            lang_s = 'EN'
            lang_m = 'EN'
            for lang in langs:
                if (lang[0] == message.author.id):
                    lang_p = lang[1][0]
                    lang_s = lang[1][1]
                    lang_m = lang[1][2]
                    break
            index_games = langs_p.index(lang_p)
            index_second = langs_p.index(lang_s)
            index_msg = langs_m.index(lang_m)
            if (len(pings) == 0):
                await message.channel.send(translate[index_msg][3]) # EN: You do not have a ping for that game!
                return
            for i in range(len(pings)):
                if (pings[i][0] == message.author.id):
                    if (cmd[1] in pings[i][1]):
                        pings[i][1].remove(cmd[1])
                        if (len(pings[i][1]) == 0):
                            del pings[i]
                        write_pings()
                        for game in games[index_games]:
                            for tid in game[1:]:
                                if (tid[0] == cmd[1]):
                                    await message.channel.send(translate[index_msg][4].format(tid[1])) # EN: Deleted ping for _{0}_.
                                    return
                    else:
                        await message.channel.send(translate[index_msg][3]) # EN: You do not have a ping for that game!
                        return
                if (i == len(pings) - 1):
                    await message.channel.send(translate[index_msg][3]) # EN: You do not have a ping for that game!

        if (cmd[0] == 'listpings'):
            lang_p = 'EN'
            lang_s = 'EN'
            lang_m = 'EN'
            for lang in langs:
                if (lang[0] == message.author.id):
                    lang_p = lang[1][0]
                    lang_s = lang[1][1]
                    lang_m = lang[1][2]
                    break
            index_games = langs_p.index(lang_p)
            index_second = langs_p.index(lang_s)
            index_msg = langs_m.index(lang_m)
            if (len(pings) == 0):
                await message.channel.send(translate[index_msg][5]) # EN: You have no pings.
                return
            for i in range(len(pings)):
                if (pings[i][0] == message.author.id):
                    msg = translate[index_msg][6] # EN: You have pings for:
                    for j in range(len(games[index_games])):
                        for k in range(1,len(games[index_games][j])):
                            if (games[index_games][j][k][0] in pings[i][1]):
                                if (lang_p == lang_s):
                                    msg += translate[index_msg][16].format(games[index_games][j][k][1], games[index_games][j][k][0])
                                else:
                                    msg += translate[index_msg][17].format(games[index_games][j][k][1], games[index_second][j][k][1], games[index_games][j][k][0])
                    await message.channel.send(msg)
                    return
                if (i == len(pings) - 1):
                    await message.channel.send(translate[index_msg][5]) # EN: You have no pings.

        if (cmd[0] == 'ping' and len(cmd) > 2):
            lang_p = 'EN'
            lang_s = 'EN'
            lang_m = 'EN'
            for lang in langs:
                if (lang[0] == message.guild.id):
                    lang_p = lang[1][0]
                    lang_s = lang[1][1]
                    lang_m = lang[1][2]
                    break
            index_games = langs_p.index(lang_p)
            index_second = langs_p.index(lang_s)
            index_msg = langs_m.index(lang_m)
            guild = None
            members = []
            try:
                guild = message.guild
                members = guild.members
            except:
                await message.channel.send(translate[index_msg][7]) # Warn about error
                return
            tids = -1
            for i in range(len(games[index_games])):
                for tid in games[index_games][i][1:]:
                    if (cmd[1] == tid[0]):
                        tids = i
                        break
                if (tids > -1):
                    break
            msg = ''
            for arg in cmd[2:]:
                msg += ' ' + arg
            extra_pings = ''
            for member in members:
                if (member.id == message.author.id):
                    continue
                if (member == guild.me):
                    continue
                if (not (message.channel.permissions_for(member).read_messages
                    and message.channel.permissions_for(member).send_messages)):
                    continue
                member_lang = 'EN'
                member_s = 'EN'
                member_m = 'EN'
                for lang in langs:
                    if (lang[0] == message.author.id):
                        lang_p = lang[1][0]
                        lang_s = lang[1][1]
                        lang_m = lang[1][2]
                        break
                index_member = langs_p.index(member_lang)
                member_second = langs_p.index(member_s)
                member_msg = langs_m.index(member_m)
                for ping in pings:
                    if (ping[0] != member.id):
                        continue
                    for i in range(1,len(games[index_member][tids])):
                        if (games[index_member][tids][i][0] in ping[1]):
                            try:
                                games_to_play = ''
                                if (member_lang == member_s):
                                    for tid in games[index_member][tids][1:]:
                                        games_to_play += '_' + tid[1] + '_ (' + tid[0] + '), '
                                else:
                                    for j in range(1, len(games[index_member][tids])):
                                        games_to_play += '_' + games[index_member][tids][j][1] + '_ (_' + games[member_second][tids][j][1] + '_, ' + games[index_member][tids][j][0] + '), '
                                await member.send(translate[member_msg][8].format(message, games_to_play[:-2]))
                            except:
                                extra_pings += '<@' + str(member.id) + '> '
                            break
            if (len(extra_pings) > 0):
                games_to_play = ''
                if (lang_p == lang_s):
                    for tid in games[index_games][tids][1:]:
                        games_to_play += '_' + tid[1] + '_ (' + tid[0] + '), '
                else:
                    for j in range(1, len(games[index_games][tids])):
                        games_to_play += '_' + games[index_games][tids][j][1] + '_ (_' + games[index_second][tids][j][1] + '_, ' + games[index_games][tids][j][0] + '), '
                await message.channel.send('||' + extra_pings[:-1] + '|| ' + games_to_play[:-2])
            await message.channel.send(translate[index_msg][9]) # EN: Your message was sent.

        if (cmd[0] == 'query'):
            lang_p = 'EN'
            lang_s = 'EN'
            lang_m = 'EN'
            for lang in langs:
                if (lang[0] == message.author.id):
                    lang_p = lang[1][0]
                    lang_s = lang[1][1]
                    lang_m = lang[1][2]
                    break
            index_games = langs_p.index(lang_p)
            index_second = langs_p.index(lang_s)
            index_msg = langs_m.index(lang_m)
            if (len(cmd) > 1):
                if (lang_p == lang_s):
                    for game in games[index_games]:
                        for tid in game[1:]:
                            if (cmd[1] == tid[0]):
                                await message.channel.send(translate[index_msg][10].format(tid[1], game[0]))
                                return
                else:
                    for i in range(len(games[index_games])):
                        for j in range(1, len(games[index_games][i])):
                            if (cmd[1] == games[index_games][i][j][0]):
                                await message.channel.send(translate[index_msg][18].format(games[index_games][i][j][1], games[index_second][i][j][1], games[index_games][i][0]))
                                return
            else:
                await message.channel.send(translate[index_msg][11].format(lang))

        if (cmd[0] == 'translate'):
            lang = 'EN'
            for lang in langs:
                if (lang[0] == message.author.id):
                    lang = lang[1][2]
                    break
            index_games = langs_m.index(lang)
            await message.channel.send(translate[index_games][13])

        if (cmd[0] == 'setlang'):
            lang = 'EN'
            for lang in langs:
                if (lang[0] == message.author.id):
                    lang = lang[1][2]
                    break
            index_games = langs_m.index(lang)
            mod_id = message.author.id

            try:
                if (message.author.guild_permissions.manage_guild):
                    msg = await message.channel.send(translate[index_games][20])
                    await msg.add_reaction('👤') # :bust_in_silhouette:
                    await msg.add_reaction('👥') # :busts_in_silhouette:
                    def check_bust(reaction, user):
                        return (user == message.author and str(reaction.emoji) in '👤👥')
                    reaction, user = await self.wait_for('reaction_add', check=check_bust)
                    if (str(reaction.emoji) == '👥'):
                        mod_id = message.guild.id
            except:
                print('Exception occured; probably a DM.')

            index_langs = 0
            if (len(langs) == 0):
                langs.append([mod_id, ['EN', 'EN', 'EN']])
            for index_langs in range(len(langs)):
                if (langs[index_langs][0] == mod_id):
                    break
                if (index_langs == len(langs) - 1):
                    langs.append([mod_id, ['EN', 'EN', 'EN']])
                    index_langs = len(langs) - 1
                    break

            # request primary lang.
            msg = await message.channel.send(translate[index_games][21])
            for flag in flags_p:
                await msg.add_reaction(flag)
            def check_flag(reaction, user):
                return (user == message.author and str(reaction.emoji) in flags_p)
            reaction, user = await self.wait_for('reaction_add', check=check_flag)
            langs[index_langs][1][0] = langs_p[flags_p.index(str(reaction.emoji))]

            # set secondary lang.
            if (str(reaction.emoji) in flags_s):
                langs[index_langs][1][1] = langs[index_langs][1][0]
            else:
                msg = await message.channel.send(translate[index_games][22])
                for flag in flags_s:
                    await msg.add_reaction(flag)
                def check_flag(reaction, user):
                    return (user == message.author and str(reaction.emoji) in flags_s)
                reaction, user = await self.wait_for('reaction_add', check=check_flag)
                if (str(reaction.emoji) != '❌'):
                    langs[index_langs][1][1] = langs_s[flags_s.index(str(reaction.emoji))]
                else:
                    langs[index_langs][1][1] = langs[index_langs][1][0]

            # set message lang.
            if (str(reaction.emoji) in flags_m):
                langs[index_langs][1][2] = langs[index_langs][1][1]
            else:
                msg = await message.channel.send(translate[index_games][23])
                for flag in flags_m:
                    await msg.add_reaction(flag)
                def check_flag(reaction, user):
                    return (user == message.author and str(reaction.emoji) in flags_m)
                reaction, user = await self.wait_for('reaction_add', check=check_flag)
                langs[index_langs][1][2] = langs_m[flags_m.index(str(reaction.emoji))]

            write_langs()
            if (mod_id == message.author.id):
                await message.channel.send(translate[langs_m.index(langs[index_langs][1][2])][24])
            else:
                await message.channel.send(translate[index_games][24])

        if (cmd[0] == 'help'):
            lang = 'EN'
            for lang in langs:
                if (lang[0] == message.author.id):
                    lang = lang[1][2]
                    break
            index_games = langs_p.index(lang)
            await message.channel.send(translate[index_games][12])

bot = Bot()
bot.run('token')