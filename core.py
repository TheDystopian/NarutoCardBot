from yaml import safe_load
from os.path import dirname,join
from itertools import chain,islice
from time import time
from random import choice

class core:
    def __init__(self,file):
        with open(join(dirname(__file__),file),"r",encoding= "utf-8") as conf:
            self.__config = safe_load(conf)

        self.__allPhrases = list(chain.from_iterable([i['activateOn'] for i in list(self.__config['commands'].values())])) 

    def core(self,data,vk,dialogs,card,db,isChat):
        def dailyEvent():
            if time() // 86400 < data['db']['day'] or time() % 86400 // 3600 < 9: return

            data['db']['battles'] = self.__config['userLevels'][data['db']['status']]['battles']
            data['db']['loses'] = 0
            data['db']['wins'] = 0
            data['db']['judge'] = 0

            data['db']['day'] = int(time() // 86400 + 1)

        def textRecognition(message):
            if len(message) < 2 or message[0] not in self.__config['commandCall'] or message[1:].upper().split()[0] not in self.__allPhrases: return None

            message = message[1:].upper().split()

            foundKey = [k for k, v in self.__config['commands'].items() if message[0] in v['activateOn']][0]

            if (isChat and 'chat' not in self.__config['commands'][foundKey]['permittedIn']) or \
                (not isChat and 'bot' not in self.__config['commands'][foundKey]['permittedIn']):
                    vk.send({'peer_id': data['vk']['peer_id'], 'message': self.__config['notPermittedHere']})
                    return None
            
            if 'admins' in self.__config['commands'][foundKey]['permittedIn'] and not vk.isAdmin(data['vk']['peer_id']):
                vk.send({'peer_id': data['vk']['peer_id'], 'message': self.__config['notPermittedAdmin']})
                return None

            return {foundKey:message[1:]}

        def payloadHandle(payload):
            def dialog(dialog):
                if isChat: data['vk'].pop('user')
                vk.send(dialogs.getDialog(data, dialog, card))
            
            def win(_=None, toWho = None):
                if toWho is None:
                    if not data['db']['battles']:
                        vk.send({'id': data['vk']['user'], 'message': f'Нет боев'})
                        return False

                    data['db']['balance'] += self.__config['userLevels'][data['db']['status']]['winBalance']
                    data['db']['scraps'] += self.__config['userLevels'][data['db']['status']]['winScraps']
                    data['db']['battles'] -= 1
                    vk.send({'id': data['vk']['user'], 'message': f'Вы победили. Вы получаете {self.__config["userLevels"][data["db"]["status"]]["winBalance"]} монет и {self.__config["userLevels"][data["db"]["status"]]["winScraps"]} обрывка'})
                    return True
                else:
                    thatUser = db.getDataFromDB(toWho)
                    if thatUser is None: return False
                    thatUser['balance'] += self.__config['userLevels'][thatUser['status']]['winBalance']
                    thatUser['scraps'] += self.__config['userLevels'][thatUser['status']]['winScraps']
                    db.editDB(thatUser)

            def lose(_=None, toWho = None):
                if toWho is None:
                    if not data['db']['battles']:
                        vk.send({'id': data['vk']['user'], 'message': f'Нет боев'})
                        return False

                    data['db']['balance'] += self.__config['userLevels'][data['db']['status']]['loseBalance']
                    data['db']['battles'] -= 1
                    vk.send({'id': data['vk']['user'], 'message': f'Вы проиграли. Вы получаете {self.__config["userLevels"][data["db"]["status"]]["loseBalance"]} монет'})
                    return True
                else:
                    thatUser = db.getDataFromDB(toWho)
                    if thatUser is None: return False
                    thatUser['balance'] += self.__config['userLevels'][thatUser['status']]['loseBalance']
                    db.editDB(thatUser)

                return True

            def upgrade(what):
                if not len(what): return False
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
                        vk.send(dialogs.getDialog(data,'notenough',card))
                        return False
                    
                    upgradeable = [i for i, v in enumerate(whichCards) if v['rarity'] == int(what[0]) and data['db']['cards'][i]['level'] < self.__config['maxLevel']]

                    if not len(upgradeable):
                        vk.send(dialogs.getDialog(data,'upgrade_fail',card))
                        return False

                    selectedCard = choice(upgradeable)
                    upgradedCards.append(selectedCard)

                    data['db']['scraps'] -= self.__config['scrapCosts'][int(what[0]) - 1]
                    data['db']['cards'][selectedCard]['level'] += 1

                else:
                    for i,n in enumerate(whichCards):
                        if n['name'].upper().split()[0] != what[0] or data['db']['cards'][i]['level'] >= self.__config['maxLevel']: continue

                        if data['db']['scraps'] < self.__config['scrapCosts'][n['rarity'] - 1]: 
                            vk.send(dialogs.getDialog(data,'notenough',card))
                            return False

                        upgradedCards.append(i)

                        data['db']['scraps'] -= self.__config['scrapCosts'][n['rarity'] - 1]                            
                        data['db']['cards'][i]['level'] += 1 
                        break
                
                vk.send(dialogs.getDialog(data,'upgrade_fail' if not len(upgradedCards) else'upgraded' if len(upgradedCards) == 1 else 'upgraded_multi', card, upgradedCards))
                return True

            def addCardsPool(pool):
                data['db']['cards'].extend(card.getCardByPool(pool))
                vk.send(dialogs.getDialog(data,'poolcards',card,selectCard=list(islice(reversed(range(len(data['db']['cards']))), 0, 3))))
                return True

            def getPack(pack):
                if self.__config['packSettings'][pack]['price'] > data['db']['balance']:
                    vk.send(dialogs.getDialog(data,'notenough',card))
                    return False
                
                data['db']['cards'].append(card.getCardByRarity(chances = self.__config['packSettings'][pack]['rarities']))
                data['db']['balance'] -= self.__config['packSettings'][pack]['price']

                vk.send(dialogs.getDialog(data,'purchase',card))
                return True

            def showCards(which):
                if not len(data['db']['cards']):
                    vk.send(dialogs.getDialog(data,'nocards', card))
                    return False

                cardData = card.getOwnedCards(data['db']['cards'])


                if len(which) < 2:
                    for c in [i for n, i in enumerate(cardData) if i not in cardData[n + 1:]]:
                        vk.send({'peer_id': data['vk'].get('peer_id'),'message':f'x{cardData.count(c)}' if cardData.count(c) > 1 else None}, attachments=[c['attachment']])

                elif which[0] in self.__config['subOptions']['level']['activateOn'] or which[0] in self.__config['subOptions']['rarity']['activateOn']:
                    cardBuff = [c for r,c in zip(data['db']['cards'], cardData) if r['level'] == int(which[1])]\
                         if which[0] in self.__config['subOptions']['level']['activateOn'] else\
                         [c for c in cardData if c['rarity'] == int(which[1])]

                    if not len(cardBuff):
                        vk.send(dialogs.getDialog(data,'nocards', card))

                    for c in cardBuff:
                        vk.send({'peer_id': data['vk'].get('peer_id'),'message':f'x{cardData.count(c)}' if cardData.count(c) > 1 else None}, attachments=[c['attachment']])

            def give(what):
                if not len(what) or data['vk']['reply_id'] is None:
                    vk.send({'peer_id': data['vk']['peer_id'], 'message':'Что?'})
                    return False

                if what[0] in self.__config['commands']['win']['activateOn']:
                    win(toWho=data['vk']['reply_id'])
                
                if what[0] in self.__config['commands']['lose']['activateOn']:
                    lose(toWho=data['vk']['reply_id'])
                return False

            def remove(what):
                if not len(what) or data['vk']['reply_id'] is None:
                    vk.send({'peer_id': data['vk']['peer_id'], 'message':'Что?'})
                    return False

                if what[0] in self.__config['commands']['win']['activateOn']:
                    thatUser = db.getDataFromDB(data['vk']['reply_id'])
                    thatUser['balance'] -= self.__config['userLevels'][thatUser['status']]['winBalance']
                    thatUser['scraps'] -= self.__config['userLevels'][thatUser['status']]['winScraps']
                    thatUser['battles'] += 1
                    db.editDB(thatUser)
                
                if what[0] in self.__config['commands']['lose']['activateOn']:
                    thatUser = db.getDataFromDB(data['vk']['reply_id'])
                    thatUser['balance'] -= self.__config['userLevels'][thatUser['status']]['loseBalance']
                    thatUser['battles'] += 1
                    db.editDB(thatUser)    
                return False           

            def flip(_):
                vk.send(dialogs.getDialog(data,choice(['firstPlayer','secondPlayer']),card))


            PAYLOADCONVERT = {
                'tutorial': {'dialog':'tutorial'},
                'profile': {'dialog':'profile_inline'},
                'shop': {'dialog':'shop_inline'}
            }

            for key in payload:
                if key in PAYLOADCONVERT:
                    payload = PAYLOADCONVERT[list(payload.keys())[0]]

            for func, args in payload.items():
                if not locals()[func](args): return False

            return True
            
        dailyEvent()
        payload = textRecognition(data['vk']['text'])
        if payload is None:
            payload = data['vk']['payload']
            if payload is None: return False

        return payloadHandle(payload)