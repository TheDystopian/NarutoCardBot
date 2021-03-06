from yaml import safe_load
from os.path import dirname,join
from itertools import chain,islice
from time import time
from random import choice, randrange

class core:
    def __init__(self,file):
        with open(join(dirname(__file__),file),"r",encoding= "utf-8") as conf:
            self.__config = safe_load(conf)

        self.__allPhrases = set(chain.from_iterable([i['activateOn'] for i in list(self.__config['commands'].values())]))
        self.__allSubPhrases = set(chain.from_iterable([i['activateOn'] for i in list(self.__config['subOptions'].values())]))

    def core(self,data,vk,dialogs,card,db,isChat):
        def dailyEvent():
            if time() // 86400 < data['db']['day'] or (time() // 86400 == data['db']['day'] and time() % 86400 // 3600 < 9): return False

            data['db']['battles'] = self.__config['userLevels'][data['db']['status']]['battles']
            data['db']['loses'] = data['db']['wins'] = data['db']['judge'] = 0

            data['db']['day'] = int(time() // 86400 + 1)

            return True

        def textRecognition(message):
            if len(message) < 2 or not message[0] in self.__config['commandCall']: return None

            payload = {}

            for wordNum,command in enumerate(message[1:].upper().split()):
                if not wordNum and not command in self.__allPhrases: return None

                if not wordNum:
                    foundKey = next((k for k, v in self.__config['commands'].items() if command in v['activateOn']))

                    if (isChat and 'chat' not in self.__config['commands'][foundKey]['permittedIn']) or \
                        (not isChat and 'bot' not in self.__config['commands'][foundKey]['permittedIn']):
                            vk.send({'peer_id': data['vk']['peer_id'], 'message': self.__config['notPermittedHere']})
                            return None

                    if 'admins' in self.__config['commands'][foundKey]['permittedIn'] and not vk.isAdmin(data['vk']['peer_id'], data['vk']['user']):
                        vk.send({'peer_id': data['vk']['peer_id'], 'message': self.__config['notPermittedAdmin']})
                        return None

                    payload[foundKey] = []
                elif command in self.__allSubPhrases:
                    if not payload: continue
                    foundKey = next((k for k, v in self.__config['subOptions'].items() if command in v['activateOn']))
                    payload[list(payload.keys())[-1]] = {foundKey: []}
                else:
                    if not payload: continue
                    if not isinstance(list(payload.values())[-1],dict):
                        payload[list(payload.keys())[-1]].append(command)
                    else:
                        items = list(payload.items())[-1]
                        payload[items[0]][list(items[1].keys())[-1]].append(command)

            return payload

        def payloadHandle(payload):
            def dialog(dialog):
                vk.send(dialogs.getDialog(data, dialog, card, toGroup=isChat))
                return True

            def win(_=None):
                if not data['db']['battles']:
                    vk.send({'id': data['vk']['user'], 'message': f'?????? ????????'})
                    return False

                data['db']['balance'] += self.__config['userLevels'][data['db']['status']]['winBalance']
                data['db']['scraps'] += self.__config['userLevels'][data['db']['status']]['winScraps']
                data['db']['battles'] -= 1
                data['db']['wins'] += 1


                vk.send({'id': data['vk']['user'], 'message': f'???? ????????????????. ???? ?????????????????? {self.__config["userLevels"][data["db"]["status"]]["winBalance"]} ?????????? ?? {self.__config["userLevels"][data["db"]["status"]]["winScraps"]} ??????????????'})
                if data['db']['wins'] == 5: 
                    data['db']['scraps'] += 5
                    vk.send({'id': data['vk']['user'], 'message': f'?? ?????? ???????????????? 5. ???? ?????????????????? 5 ????????????????'})


                return True

            def lose(_=None):
                if not data['db']['battles']:
                    vk.send({'id': data['vk']['user'], 'message': f'?????? ????????'})
                    return False

                data['db']['balance'] += self.__config['userLevels'][data['db']['status']]['loseBalance']
                data['db']['battles'] -= 1
                data['db']['loses'] += 1

                vk.send({'id': data['vk']['user'], 'message': f'???? ??????????????????. ???? ?????????????????? {self.__config["userLevels"][data["db"]["status"]]["loseBalance"]} ??????????'})
                if data['db']['loses'] == 5: 
                    data['db']['balance'] += 20
                    vk.send({'id': data['vk']['user'], 'message': f'?? ?????? ???????????????? 5. ???? ?????????????????? 20 ??????????'})

                return True

            def upgrade(what):
                whichCards = card.getOwnedCards(data['db']['cards'])

                upgradedCards = []

                if not what:
                    for i, c in zip(whichCards, data['db']['cards']):
                        if data['db']['cards'].count(c) < self.__config['repeatsNeeded'][str(i['rarity'])] or c['level'] >= i['maxlevel']: continue

                        duplicates = [j for j, v in enumerate(data['db']['cards']) if v == c][:self.__config['repeatsNeeded'][str(i['rarity'])]]
                        if not duplicates: continue

                        upgradedCards.append(duplicates[0])
                        [data['db']['cards'].pop(i) and whichCards.pop(i) for i in reversed(duplicates[1:])]
                        data['db']['cards'][duplicates[0]]['level'] += 1                     
                
                elif not isinstance(what,list): return

                elif what[0].isdigit():
                    if data['db']['scraps'] < self.__config['scrapCosts'][what[0]]: 
                        vk.send(dialogs.getDialog(data,'notenough', toGroup = True))
                        return False
                    
                    upgradeable = [(i, v) for i, v in enumerate(whichCards) if v['rarity'] == int(what[0]) and data['db']['cards'][i]['level'] < v['maxlevel']]

                    if not upgradeable:
                        vk.send(dialogs.getDialog(data,'upgrade_fail', toGroup = True))
                        return False

                    selectedCard = choice(upgradeable)
                    upgradedCards.append(selectedCard[0])

                    data['db']['scraps'] -= self.__config['scrapCosts'][str(selectedCard[1]['rarity'])]
                    data['db']['cards'][selectedCard[0]]['level'] += 1

                else:
                    i,n = next( ( (i,n) for i,n in enumerate(whichCards) if n['name'].upper().find(" ".join(what)) != -1 and data['db']['cards'][i]['level'] < n['maxlevel']), (None, None))

                    if i is None:
                        vk.send(dialogs.getDialog(data,'nocards'))
                        return False

                    if data['db']['scraps'] < self.__config['scrapCosts'][str(n['rarity'])]:
                        vk.send(dialogs.getDialog(data,'notenough'))
                        return False

                    upgradedCards.append(i)

                    data['db']['scraps'] -= self.__config['scrapCosts'][str(n['rarity'])]
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
                
                data['db']['balance'] -= self.__config['packSettings'][pack]['price']
                data['db']['packs'][pack] += 1

                vk.send(dialogs.getDialog(data,'gotPack'))

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

                elif "level" in which:
                    cardOwn = {frozenset(i.items()):i for i in data['db']['cards']}.values()
                    filteredCards = [n for cod, n in zip(cardOwn, cds) if cod['level'] == int(which['level'][0])]

                elif "rarity" in which:
                    filteredCards = [(c,k) for c,k in cds if k['rarity'] == int(which['rarity'][0])]

                elif isinstance(which,list):
                    filteredCards = [n for n in cds if n[1]['name'].upper().find(" ".join(which)) != -1]

                else: return

                if not filteredCards:
                    vk.send(dialogs.getDialog(data,'nocards', toGroup = True))

                for c,k in filteredCards:
                    vk.send({'peer_id': data['vk'].get('peer_id'),'message':f'x{c}' if c > 1 else None}, attachments=k['attachment']) 

            def give(what):
                if not what or data['vk']['reply_id'] is None:
                    vk.send({'peer_id': data['vk']['peer_id'], 'message':'???????'})
                    return False

                thatUser = db.getDataFromDB(data['vk']['reply_id'])
                if thatUser is None: return False

                if "win" in what:
                    thatUser['wins'] +=1
                    thatUser['balance'] += self.__config['userLevels'][thatUser['status']]['winBalance']
                    thatUser['scraps'] += self.__config['userLevels'][thatUser['status']]['winScraps']
                    if thatUser['wins'] == 5: thatUser['scraps'] += 5
                
                elif "lose" in what:
                    thatUser['loses'] += 1
                    thatUser['balance'] += self.__config['userLevels'][thatUser['status']]['loseBalance']
                    if thatUser['loses'] == 5: thatUser['balance'] += 20

                elif "balance" in what:
                    thatUser['balance'] += int(what['balance'][0])             

                elif "scraps" in what:
                    thatUser['scraps'] += int(what['scraps'][0]) 

                elif "pack" in what and what['pack'][0].isdigit() and int(what['pack'][0]) < len(self.__config['packSettings']):
                    thatUser['packs'][int(what['pack'][0])] += int(what['pack'][1]) if len(what['pack']) > 1 and what['pack'][1].isdigit() else 1

                elif "cards" in what:
                    if not what: return


                    foundCardLevel = 1
                    if what['cards'][-1].isdigit():
                        foundCardLevel, what['cards'] = int(what['cards'][-1]), what['cards'][:-1]

                    foundCardID = next( ( cardID for cardID,cd in enumerate(card.allCards()) if foundCardLevel <= len(cd['photo']) and cd['name'].upper().find(" ".join(what['cards'])) != -1), None)

                    if foundCardID is None: 
                        vk.send({'peer_id':data['vk']['peer_id'], 'message': '?????????? ?????????? ??????'})
                        return

                    thatUser['cards'].append({'id':foundCardID, 'level': foundCardLevel})                
                else: return False


                db.editDB(thatUser)

                return False

            def remove(what):
                if not what or data['vk']['reply_id'] is None:
                    vk.send({'peer_id': data['vk']['peer_id'], 'message':'???????'})
                    return False

                thatUser = db.getDataFromDB(data['vk']['reply_id'])
                if thatUser is None: return False

                if "win" in what:
                    thatUser['balance'] -= self.__config['userLevels'][thatUser['status']]['winBalance']
                    thatUser['scraps'] -= self.__config['userLevels'][thatUser['status']]['winScraps']
                    thatUser['battles'] += 1
                    if thatUser['wins'] == 5: thatUser['scraps'] -= 5
                    thatUser['wins'] -= 1
                    
                
                elif "lose" in what:
                    thatUser['balance'] -= self.__config['userLevels'][thatUser['status']]['loseBalance']
                    thatUser['battles'] += 1
                    if thatUser['loses'] == 5: thatUser['balance'] -= 20
                    thatUser['loses'] -= 1

                elif "pack" in what and what['pack'][0].isdigit() and int(what['pack'][0]) < len(self.__config['packSettings']):
                    thatUser['packs'][int(what['pack'][0])] -= int(what['pack'][1]) if len(what['pack']) > 1 and what['pack'][1].isdigit() else 1

                elif "cards" in what:
                    if not what: return

                    selectedCardLevel = 1
                    if what['cards'][-1].isdigit():
                        selectedCardLevel, what['cards'] = int(what['cards'][-1]), what['cards'][:-1]


                    foundCardID = next( ( cardID for cardID,(cdDB, cdDT) in enumerate(zip(thatUser['cards'], card.getOwnedCards(thatUser['cards']))) if 
                        cdDB['level'] == selectedCardLevel and
                    cdDT['name'].upper().find(" ".join(what['cards'])) != -1), None)

                    if foundCardID is None: 
                        vk.send({'peer_id':data['vk']['peer_id'], 'message': '?? ???????? ?????? ?????????? ??????????'})
                        return

                    thatUser['cards'].pop(foundCardID)

                else: return False

                db.editDB(thatUser)

                return False

            def flip(_):
                vk.send(dialogs.getDialog(data,choice(['firstPlayer','secondPlayer']), toGroup=True))

            def judge(_):
                data['db']['balance'] += 1
                data['db']['judge'] += 1
                vk.send({'id': data['vk']['user'], 'message': f'???? ?????????????????? 1 ???????????? ???? ??????????????????'})
                if not data['db']['judge'] % 10: 
                    data['db']['balance'] +=10
                    vk.send({'id': data['vk']['user'], 'message': f'???? ?????????????????? 10 ?????????? ???? ???????????????? ??????????????????'})
                return True

            def profile(_):
                if not isChat:
                    vk.send(dialogs.getDialog(data, 'profile', toGroup=True))
                elif data['vk']['reply_id'] is None or data['vk']['reply_id'] < 1:
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
                    vk.send({'peer_id': data['vk'].get('peer_id'), 'message': '???????????????????????? ????????????????' })
                    return

                vk.send({'peer_id': data['vk'].get('peer_id'), 'message': '??????????????' if randrange(1,101) <= int(chance[0]) else '???? ??????????????' })

            def destroy(what):
                if not data['db']['cards']:
                    vk.send(dialogs.getDialog(data,'nocards', toGroup = True))
                    return

                cds = card.getOwnedCards(data['db']['cards'])
                
                if isinstance(what, list):
                    i, n = next(((i,n) for i, (c,n) in enumerate(zip(data['db']['cards'], cds)) if n['name'].upper().find(" ".join(what)) != -1 and c['level'] == 1), (None, None))

                elif "rarity" in what and what['rarity'][0].lstrip('-').isdecimal():
                    i, n = next(((i,n) for i,(c,n) in enumerate(zip(data['db']['cards'], cds)) if n['rarity'] == int(what['rarity'][0]) and c['level'] == 1), (None, None))

                if i is None:
                    vk.send(dialogs.getDialog(data,'nocards', toGroup = True))
                    return

                data['db']['cards'].pop(i)
                data['db']['scraps'] += self.__config['breakPrice'][str(n['rarity'])]

                vk.send({'peer_id': data['vk']['peer_id'], 'message': f'?????????????????? ?????????? {n["name"]}. ???? ?????????????????? {self.__config["breakPrice"][str(n["rarity"])]} ????????????????'})
                    
                return True

            def openPack(which):
                if data['db']['packs'][which] < 1:
                    vk.send(dialogs.getDialog(data,'nopack', toGroup=True))
                    return

                data['db']['packs'][which] -= 1

                data['db']['cards'].append(card.getCardByRarity(chances = self.__config['packSettings'][which]['rarities']))

                vk.send(dialogs.getDialog(data,'purchase',card, toGroup = True))

                return True

            PAYLOADCONVERT = {
                'tutorial': {'dialog':'tutorial'},
                'shop': {'dialog':'shop_inline'},
                'varenik': {'dialog': 'varenik'},
                'leha': {'dialog': 'leha'},
                'gerych': {'dialog': 'gerych'},
                'pack_dialog': {'dialog':'packs_inline'},
                'removeKB':{'dialog':'kb_placeholder'}
            }

            for key in payload:
                if key in PAYLOADCONVERT:
                    payload = PAYLOADCONVERT[list(payload.keys())[0]]

            for func, args in payload.items():
                if not func in locals(): continue
                if not locals()[func](args): return False

            return True

        daily = dailyEvent()
        payload = data['vk']['payload']
        if payload is None:
            payload = textRecognition(data['vk']['text'])
            if not payload: return daily

        return payloadHandle(payload)

