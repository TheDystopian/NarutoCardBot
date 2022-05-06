from yaml import safe_load
from os.path import dirname,join
from itertools import chain,islice
from time import time
from random import choice, randrange
from collections import defaultdict

class core:
    def __init__(self,file):
        with open(join(dirname(__file__),file),"r",encoding= "utf-8") as conf:
            self.__config = safe_load(conf)

        self.__allPhrases = list(chain.from_iterable([i['activateOn'] for i in list(self.__config['commands'].values())])) 

    def core(self,data,vk,dialogs,card,db,isChat):
        def dailyEvent():
            if time() // 86400 < data['db']['day'] or time() % 86400 // 3600 < 9: return

            data['db']['battles'] = self.__config['userLevels'][data['db']['status']]['battles']
            data['db']['loses'] = data['db']['wins'] = data['db']['judge'] = 0

            data['db']['day'] = int(time() // 86400 + 1)

        def textRecognition(message):
            if len(message) < 2 or message[0] not in self.__config['commandCall'] or message[1:].upper().split()[0] not in self.__allPhrases: return None

            message = message[1:].upper().split()

            foundKey = next((k for k, v in self.__config['commands'].items() if message[0] in v['activateOn']), None)

            if (isChat and 'chat' not in self.__config['commands'][foundKey]['permittedIn']) or \
                (not isChat and 'bot' not in self.__config['commands'][foundKey]['permittedIn']):
                    vk.send({'peer_id': data['vk']['peer_id'], 'message': self.__config['notPermittedHere']})
                    return None

            if 'admins' in self.__config['commands'][foundKey]['permittedIn'] and not vk.isAdmin(data['vk']['peer_id'], data['vk']['user']):
                vk.send({'peer_id': data['vk']['peer_id'], 'message': self.__config['notPermittedAdmin']})
                return None

            return {foundKey:message[1:]}

        def payloadHandle(payload):
            def dialog(dialog):
                vk.send(dialogs.getDialog(data, dialog, card, toGroup=isChat))
                return True

            def win(_=None):
                if not data['db']['battles']:
                    vk.send({'id': data['vk']['user'], 'message': f'Нет боев'})
                    return False

                data['db']['balance'] += self.__config['userLevels'][data['db']['status']]['winBalance']
                data['db']['scraps'] += self.__config['userLevels'][data['db']['status']]['winScraps']
                data['db']['battles'] -= 1
                data['db']['wins'] += 1


                vk.send({'id': data['vk']['user'], 'message': f'Вы победили. Вы получаете {self.__config["userLevels"][data["db"]["status"]]["winBalance"]} монет и {self.__config["userLevels"][data["db"]["status"]]["winScraps"]} обрывка'})
                if data['db']['wins'] == 5: 
                    data['db']['scraps'] += 5
                    vk.send({'id': data['vk']['user'], 'message': f'У вас винстрик 5. Вы получаете 5 обрывков'})


                return True

            def lose(_=None):
                if not data['db']['battles']:
                    vk.send({'id': data['vk']['user'], 'message': f'Нет боев'})
                    return False

                data['db']['balance'] += self.__config['userLevels'][data['db']['status']]['loseBalance']
                data['db']['battles'] -= 1
                data['db']['loses'] += 1

                vk.send({'id': data['vk']['user'], 'message': f'Вы проиграли. Вы получаете {self.__config["userLevels"][data["db"]["status"]]["loseBalance"]} монет'})
                if data['db']['loses'] == 5: 
                    data['db']['balance'] += 20
                    vk.send({'id': data['vk']['user'], 'message': f'У вас лузстрик 5. Вы получаете 20 монет'})

                return True

            def upgrade(what):
                if not what: return False
                whichCards = card.getOwnedCards(data['db']['cards'])

                upgradedCards = []

                if what[0] in self.__config['subOptions']['repeats']['activateOn']:
                    for i, c in zip(whichCards, data['db']['cards']):
                        if data['db']['cards'].count(c) < self.__config['repeatsNeeded'][i['rarity'] - 1] or c['level'] >= self.__config['maxLevel']: continue

                        duplicates = [j for j, v in enumerate(data['db']['cards']) if v == c][:self.__config['repeatsNeeded'][i['rarity'] - 1]]
                        if not len(duplicates): continue

                        upgradedCards.append(duplicates[0])
                        [data['db']['cards'].pop(i) and whichCards.pop(i) for i in duplicates[1:]]
                        data['db']['cards'][duplicates[0]]['level'] += 1                     
                
                elif what[0].isdigit() and int(what[0]) in range(1, len(self.__config['scrapCosts']) + 1):
                    if data['db']['scraps'] < self.__config['scrapCosts'][int(what[0]) - 1]: 
                        vk.send(dialogs.getDialog(data,'notenough', toGroup = True))
                        return False
                    
                    upgradeable = [i for i, v in enumerate(whichCards) if v['rarity'] == int(what[0]) and data['db']['cards'][i]['level'] < self.__config['maxLevel']]

                    if not len(upgradeable):
                        vk.send(dialogs.getDialog(data,'upgrade_fail', toGroup = True))
                        return False

                    selectedCard = choice(upgradeable)
                    upgradedCards.append(selectedCard)

                    data['db']['scraps'] -= self.__config['scrapCosts'][int(what[0]) - 1]
                    data['db']['cards'][selectedCard]['level'] += 1

                else:
                    i,n = next( ( (i,n) for i,n in enumerate(whichCards) if n['name'].upper().find(" ".join(what)) != -1 and data['db']['cards'][i]['level'] < self.__config['maxLevel']), (None, None))

                    if i is None:
                        vk.send(dialogs.getDialog(data,'nocards'))
                        return False

                    if data['db']['scraps'] < self.__config['scrapCosts'][n['rarity'] - 1]: 
                        vk.send(dialogs.getDialog(data,'notenough'))
                        return False

                    upgradedCards.append(i)

                    data['db']['scraps'] -= self.__config['scrapCosts'][n['rarity'] - 1]                            
                    data['db']['cards'][i]['level'] += 1 
                
                vk.send(dialogs.getDialog(data,'upgrade_fail' if not len(upgradedCards) else'upgraded' if len(upgradedCards) == 1 else 'upgraded_multi', card, upgradedCards, toGroup = True))
                return True

            def addCardsPool(pool):
                data['db']['cards'].extend(card.getCardByPool(pool))
                vk.send(dialogs.getDialog(data,'poolcards',card,selectCard=list(islice(reversed(range(len(data['db']['cards']))), 0, 3))))
                return True

            def getPack(pack):
                if self.__config['packSettings'][pack]['price'] > data['db']['balance']:
                    vk.send(dialogs.getDialog(data,'notenough', toGroup = True))
                    return False
                
                data['db']['cards'].append(card.getCardByRarity(chances = self.__config['packSettings'][pack]['rarities']))
                data['db']['balance'] -= self.__config['packSettings'][pack]['price']

                vk.send(dialogs.getDialog(data,'purchase',card, toGroup = True))
                return True

            def showCards(which):
                if not data['db']['cards']:
                    vk.send(dialogs.getDialog(data,'nocards', toGroup = True))
                    return False
           
                cds = card.getOwnedCards(data['db']['cards'])
                cds = [(cds.count(n), n) for i, n in enumerate(cds) if n not in cds[i+1:]]

                if not which:
                    for c, k in cds:
                        vk.send({'peer_id': data['vk'].get('peer_id'),'message':f'x{c}' if c > 1 else None}, attachments=k['attachment'])
                    return 

                if len(which) == 1:
                    found = [n for n in cds if n[1]['name'].upper().find(" ".join(which)) != -1]

                    if not found: 
                        vk.send(dialogs.getDialog(data,'nocards', toGroup = True))

                    for c,f in found:
                        vk.send({'peer_id': data['vk'].get('peer_id'),'message':f'x{c}' if c > 1 else None}, attachments=f['attachment'])
                    return

                if which[1].isdigit(): 
                    if which[0] in self.__config['subOptions']['rarity']['activateOn']:
                        filteredCards = [(c,k) for c,k in cds if k['rarity'] == int(which[1])]
                    elif which[0] in self.__config['subOptions']['level']['activateOn']:
                        cardOwn = {frozenset(i.items()):i for i in data['db']['cards']}.values()
                        filteredCards = [n for cod, n in zip(cardOwn, cds) if cod['level'] == int(which[1])]

                    if not filteredCards:
                        vk.send(dialogs.getDialog(data,'nocards', toGroup = True))
                    for c,k in filteredCards:
                        vk.send({'peer_id': data['vk'].get('peer_id'),'message':f'x{c}' if c > 1 else None}, attachments=k['attachment']) 

            def give(what):
                if not what or data['vk']['reply_id'] is None:
                    vk.send({'peer_id': data['vk']['peer_id'], 'message':'Что?'})
                    return False

                thatUser = db.getDataFromDB(data['vk']['reply_id'])
                if thatUser is None: return False

                if what[0] in self.__config['commands']['win']['activateOn']:
                    thatUser['wins'] +=1
                    thatUser['balance'] += self.__config['userLevels'][thatUser['status']]['winBalance']
                    thatUser['scraps'] += self.__config['userLevels'][thatUser['status']]['winScraps']
                    if thatUser['wins'] == 5: thatUser['scraps'] += 5
                
                elif what[0] in self.__config['commands']['lose']['activateOn']:
                    thatUser['loses'] += 1
                    thatUser['balance'] += self.__config['userLevels'][thatUser['status']]['loseBalance']
                    if thatUser['loses'] == 5: thatUser['balance'] += 20

                elif len(what) < 2 or not what[1].isdigit(): return False

                elif what[0] in self.__config['subOptions']['balance']['activateOn']:
                    thatUser['balance'] += int(what[1])             

                elif what[0] in self.__config['subOptions']['scraps']['activateOn']:
                    thatUser['scraps'] += int(what[1]) 

                db.editDB(thatUser)

                return False

            def remove(what):
                if not what or data['vk']['reply_id'] is None:
                    vk.send({'peer_id': data['vk']['peer_id'], 'message':'Что?'})
                    return False

                thatUser = db.getDataFromDB(data['vk']['reply_id'])
                if thatUser is None: return False

                if what[0] in self.__config['commands']['win']['activateOn']:
                    thatUser['balance'] -= self.__config['userLevels'][thatUser['status']]['winBalance']
                    thatUser['scraps'] -= self.__config['userLevels'][thatUser['status']]['winScraps']
                    thatUser['battles'] += 1
                    if thatUser['wins'] == 5: thatUser['scraps'] -= 5
                    thatUser['wins'] -= 1
                    
                
                elif what[0] in self.__config['commands']['lose']['activateOn']:
                    thatUser['balance'] -= self.__config['userLevels'][thatUser['status']]['loseBalance']
                    thatUser['battles'] += 1
                    if thatUser['loses'] == 5: thatUser['balance'] -= 20
                    thatUser['loses'] -= 1

                elif len(what) < 2 or not what[1].isdigit(): return False

                elif what[0] in self.__config['subOptions']['balance']['activateOn']:
                    thatUser['balance'] -= int(what[1])             

                elif what[0] in self.__config['subOptions']['scraps']['activateOn']:
                    thatUser['scraps'] -= int(what[1]) 

                db.editDB(thatUser)

                return False

            def flip(_):
                vk.send(dialogs.getDialog(data,choice(['firstPlayer','secondPlayer']), toGroup=True))

            def judge(_):
               data['db']['balance'] += 1
               if data['db']['judge'] == 10: data['db']['balance'] +=10
               return True

            def profile(_):
                if data['vk']['reply_id'] is None or data['vk']['reply_id'] < 1:
                    vk.send(dialogs.getDialog(data, 'profile_inline', toGroup=True))
                else:
                    dbUser = db.getDataFromDB(data['vk']['reply_id'])
                    if dbUser is None: return 

                    if not vk.isAdmin(data['vk']['peer_id'], data['vk']['user']):
                        vk.send(dialogs.getDialog({'vk':data['vk'],'db':dbUser},'profile_inline_otheruser', toGroup = True))
                    else:
                        vk.send(dialogs.getDialog({'vk':data['vk'],'db':dbUser},'profile_inline'))

                return

            def chance(chance):
                if not chance or not chance[0].isdigit() or int(chance[0]) not in range(1, 101):
                    vk.send({'peer_id': data['vk'].get('peer_id'), 'message': 'Недопустимое значение' })
                    return

                vk.send({'peer_id': data['vk'].get('peer_id'), 'message': 'Вы попали в шанс' if randrange(1,101) < int(chance[0]) else 'Вы не попали в шанс' })

                


            PAYLOADCONVERT = {
                'tutorial': {'dialog':'tutorial'},
                'shop': {'dialog':'shop_inline'}
            }

            for key in payload:
                if key in PAYLOADCONVERT:
                    payload = PAYLOADCONVERT[list(payload.keys())[0]]

            for func, args in payload.items():
                if not func in locals(): continue
                if not locals()[func](args): return False

            return True

        dailyEvent()
        payload = textRecognition(data['vk']['text'])
        if payload is None:
            payload = data['vk']['payload']
            if payload is None: return False

        return payloadHandle(payload)
