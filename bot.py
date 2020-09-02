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

def read_translate(lang):
    f = open('translate_' + lang + '.txt')
    read = f.read()
    f.close()
    translate.append([])
    read = read.split('\n')
    for msg in read:
        translate[-1].append(msg.replace('\\n', '\n'))

games = []
pings = []
translate = []
# langs = ('EN', 'JA', 'FR', 'DE', 'ES', 'IT', 'NL', 'PT', 'RU', 'KO', 'ZHCN', 'ZHTW')
langs = ('EN',)

class Bot(discord.Client):
    async def on_ready(self):
        await self.change_presence(activity=CustomActivity('Refreshing... Please wait!'), status=Status.idle)
        for lang in langs:
            refresh(lang, True)
            read_translate(lang)
        read_pings()
        print('Profile: {0}'.format(self.user))
        await self.change_presence(status=Status.online)

    async def on_message(self, message):
        if (not message.content.startswith('^^')):
            return

        cmd = message.content[2:].split(' ')

        if (message.author.id == 291286384189374464 and cmd[0] == 'refresh'):
            await self.change_presence(activity=CustomActivity('Refreshing... Please wait!'), status=Status.idle)
            del games[:]
            for lang in langs:
                refresh(lang, False)
            await self.change_presence(status=Status.online)
            return

        if (message.author.id == 291286384189374464 and cmd[0] == 'stop'):
            await self.change_presence(activity=CustomActivity('Refreshing... Please wait!'), status=Status.invisible)
            await self.close()
            return

        if (cmd[0] == 'addping' and len(cmd) > 1):
            lang = 'EN'
            index_games = langs.index(lang)
            for ping in pings:
                if (ping[0] == message.author.id):
                    if (cmd[1] in ping[1]):
                        await message.channel.send(translate[index_games][0]) # EN: You already have a ping for that game!
                        return
                    break
            for game in games[index_games]:
                for tid in game[1:]:
                    if (tid[0] == cmd[1]):
                        if (pings == []):
                            pings.append((message.author.id, [cmd[1]]))
                            write_pings()
                            await message.channel.send(translate[index_games][1].format(tid[1])) # EN: Added a ping for _{0}_.
                            return
                        for i in range(len(pings)):
                            if (pings[i][0] != message.author.id):
                                if (i == len(pings) - 1):
                                    pings.append((message.author.id, [cmd[1]]))
                                    write_pings()
                                    await message.channel.send(translate[index_games][1].format(tid[1])) # EN: Added a ping for _{0}_.
                                    return
                                continue
                            pings[i][1].append(cmd[1])
                            write_pings()
                            await message.channel.send(translate[index_games][1].format(tid[1])) # EN: Added a ping for _{0}_.
                            break
                        return
            await message.channel.send(translate[index_games][2].format(cmd[1])) # EN: Invalid title ID: {0}.
            return

        if (cmd[0] == 'delping' and len(cmd) > 1):
            lang = 'EN'
            index_games = langs.index(lang)
            if (len(pings) == 0):
                await message.channel.send(translate[index_games][3]) # EN: You do not have a ping for that game!
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
                                    await message.channel.send(translate[index_games][4].format(tid[1])) # EN: Deleted ping for _{0}_.
                                    return
                    else:
                        await message.channel.send(translate[index_games][3]) # EN: You do not have a ping for that game!
                        return
                if (i == len(pings) - 1):
                    await message.channel.send(translate[index_games][3]) # EN: You do not have a ping for that game!

        if (cmd[0] == 'listpings'):
            lang = 'EN'
            index_games = langs.index(lang)
            if (len(pings) == 0):
                await message.channel.send(translate[index_games][5]) # EN: You have no pings.
                return
            for i in range(len(pings)):
                if (pings[i][0] == message.author.id):
                    msg = translate[index_games][6] # EN: You have pings for:
                    for game in games[index_games]:
                        for tid in game[1:]:
                            if (tid[0] in pings[i][1]):
                                msg += '\n(' + tid[0] + ') _' + tid[1] + '_'
                    await message.channel.send(msg)
                    return
                if (i == len(pings) - 1):
                    await message.channel.send(translate[index_games][5]) # EN: You have no pings.

        if (cmd[0] == 'ping' and len(cmd) > 2):
            lang = 'EN'
            index_games = langs.index(lang)
            guild = None
            members = []
            try:
                guild = message.guild
                members = guild.members
            except:
                await message.channel.send(translate[index_games][7]) # Warn about error
                return
            tids = -1
            for i in range(len(games[index_games])):
                for tid in games[index_games][i][1:]:
                    if (cmd[1] == tid[0]):
                        tids = i
                        break
                if (len(tids) > -1):
                    break
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
                index_member = langs.index(member_lang)
                for ping in pings:
                    if (ping[0] != member.id):
                        continue
                    for tid in tids:
                        if (tid[0] in ping[1]):
                            try:
                                await member.send(translate[index_member][8].format(message, str(games[index_member][tids][1:])[1:-1].replace('(\'','(').replace('\', \'',') _').replace('\')','_')))
                            except:
                                extra_pings += '<@' + str(member.id) + '>'
                            break
            if (len(extra_pings) > 0):
                await message.channel.send('||' + extra_pings + '||' + str(games[index_games][tids][1:])[1:-1].replace('(\'','(').replace('\', \'',') _').replace('\')','_'))
            await message.channel.send(translate[index_games][9]) # EN: Your message was sent.

        if (cmd[0] == 'query'):
            lang = 'EN'
            index_games = langs.index(lang)
            if (len(cmd) > 1):
                for game in games[index_games]:
                    for tid in game[1:]:
                        if (cmd[1] == tid[0]):
                            await message.channel.send(translate[index_games][10].format(tid[1], game[0]))
                            return
            else:
                await message.channel.send(translate[index_games][11].format(lang))

        if (cmd[0] == 'translate'):
            lang = 'EN'
            index_games = langs.index(lang)
            await message.channel.send(translate[index_games][13])

        if (cmd[0] == 'help'):
            lang = 'EN'
            index_games = langs.index(lang)
            await message.channel.send(translate[index_games][12])

bot = Bot()
bot.run('ABCDEFGHIJKLMNOPQRSTUVXY.Zabcde.fghijklmnopqrstuvwxyz123456')