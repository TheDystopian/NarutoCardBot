from os.path import join, dirname
from dataclasses import dataclass
from termios import CIBAUD
from time import time
from yaml import safe_load
from assets.cards import cards
from assets.dialog import dialog
from random import choice, randrange
from itertools import islice
from backend.db import DB

from backend.vk import VK
from card_utils import botUtils
import errors
from game.rank import rank

@dataclass
class functionData:
    _vk: VK = None
    _dialogs: dialog = None
    _cards: cards = None
    _DB: DB = None
    _rank: rank = None
    __file: str = 'functions.yaml'
    
    def __init__(self, parent):
        with open(
            join(dirname(__file__), "configs", self.__file), "r", encoding="utf-8"
        ) as conf:
            self._config = safe_load(conf)
            
        self._vk = parent._vk
        self._dialogs = parent._dialogs
        self._cards = parent._card
        self._DB = parent._db


class generalFunctions:
    def dialog(self, dialog, data):
        self.funcData._vk.send(
                self.funcData._dialogs.getDialogParsed(data['vk']['peer_id'], dialog, userdata = data['db'])
            )
    
    def flip(self, _, data):
        self.funcData._vk.send(
            self.funcData._dialogs.getDialogPlain(
                data['vk']['peer_id'], 
                preset = choice(["firstPlayer", "secondPlayer"])
            )
        )
    
    def openPack(self, pack, data):
        if not data["db"]["packs"][pack]:
            raise errors.NoPack('noPack')

        self.editDB = True
        data["db"]["packs"][pack] -= 1
        data["db"]["cards"].append(
            self.funcData._cards.getCardByRarity(
                chances=self.funcData._config["packSettings"][pack]["rarities"]
            )
        )

        self.funcData._vk.send(
            self.funcData._dialogs.getDialogParsed(
                data['vk']['peer_id'],
                'purchase',
                userdata = data['db'],
                selectCard= -1
            )
        )
    
    def getPack(self, pack, data):    
        if self.funcData._config["packSettings"][pack]["price"] > data["db"]["balance"]:
            raise errors.NotEnough('notEnoughMoney')

        self.editDB = True
        data["db"]["balance"] -= self.funcData._config["packSettings"][pack]["price"]
        data["db"]["packs"][pack] += 1

        self.funcData._vk.send(
            self.funcData._dialogs.getDialogPlain(
                data['vk']['user'],
                preset = "gotPack"
            )    
        )    
    
    def addCardsPool(self, pool, data):
        self.editDB = True
        data["db"]["cards"].extend(self.funcData._cards.getCardByPool(pool))
        self.funcData._vk.send(
            self.funcData._dialogs.getDialogParsed(
                data['vk']['peer_id'],
                preset = 'poolcards',
                userdata = data['db'],
                selectCard = list(range(-len(pool),0) )
            )
        )
    
    def showCards(self, cards, data):
        if not data["db"]["cards"]:
            raise errors.NoCards('noCards')
        
        isChat = data['vk']['user'] != data['vk']['peer_id']
        showPict = False
        
        cardData = self.funcData._cards.getOwnedCards(data['db']['cards'])
        
        cardData = [
            (cd, cardData.count(cd))
            for cidx, cd in enumerate(cardData)
            if cd not in cardData[cidx+1:]
        ]
        
        if not cards: 
            pass
        
        elif isinstance(cards, list):
            cardData = [
                card
                for card in cardData
                if card[0]['name'].upper().find(' '.join(cards)) != -1
            ]
            showPict = len(cardData) == 1
        
        elif cards.get("level"):
            cardData = [
                card 
                for card in cardData if
                str(card[0]['level']) == cards['level'][-1]
            ]
        
        elif cards.get("rarity"):
            cardData = [
                card 
                for card in cardData if
                str(card[0]['rarity']) == cards['rarity'][-1]
            ]

        if not cardData:
            raise errors.NoCards('noCards')
        
        if not isChat or showPict:
            [self.funcData._vk.send(
                self.funcData._dialogs.getDialogPlain(
                    data['vk']['peer_id'],
                    text = f'x{cardCount}' if cardCount > 1 else '' 
                ),
                attachments= cardData['attachment']
            )
             for cardData, cardCount in cardData
            ]
            
        else:
            self.funcData._vk.send(
                self.funcData._dialogs.getDialogPlain(
                    data['vk']['peer_id'],
                    text = f'''Ваши карты:\n\n{
                        chr(10).join([
                        botUtils.formatCards(cdt, ccnt)
                        for cdt, ccnt in cardData   
                    ])}''' 
                ),    
            )
            
    def give(self, thing, data):
        if not thing:
            raise NotImplementedError('cantError')
        
        if (
            data['vk']['reply_id'] is None 
            or data['vk']['reply_id'] == data['vk']['user']
        ):
            user = data['db']
            if self.editDB:
                self.funcData._DB.editDB(user)
            
            self.editDB = False
        else:
            user = self.funcData._DB.getDataFromDB(data["vk"]["reply_id"])

        if (
            isinstance(thing, list)
            and thing[0].upper() in {i.upper() for i in self.funcData._dialogs.getStatus()}   
        ):
            user['status'] = next(
                num
                for num, status in enumerate(self.funcData._dialogs.getStatus())
                if thing[0].upper() == status.upper()
            )
        
            statusDays = (
                int(thing[-1])
                if len(thing) > 1 and thing[-1].isdecimal()
                else self.funcData._config["defaultPremium"]
            )
            
            user['premium'] = int(time() // 86400 + statusDays + 1)
            
            self.funcData._vk.send(
                self.funcData._dialogs.getDialogPlain(
                    user['id'],
                    text = f'''
Вам был выдан статус {self.funcData._dialogs.getStatus()[user['status']]}\n
Истекает через {statusDays} {"день" if statusDays % 10 == 1 else "дня" if statusDays % 10 < 5 and statusDays % 10 >= 2 else "дней"}
                    '''
                )
            )

        if not isinstance(thing,dict):
            raise NotImplementedError('cantError')

        elif thing.get('win', False) != False:
            self.funcData._rank.win(user)
            
            botUtils.changeStats(
                user, 
                stats = {'wins': 1} | self.funcData._config["battle"]['win'][user["status"]]
            )
            
            if not user['battles'] % self.funcData._config["streak"]['count']['win'][user["status"]]:
                botUtils.changeStats(
                    user, 
                    stats = self.funcData._config["streak"]['reward']['win'][user["status"]]
                )
            
        elif thing.get('lose', False) != False:
            self.funcData._rank.lose(user)
            
            botUtils.changeStats(
                user, 
                stats = {'loses': 1} | self.funcData._config["battle"]['lose'][user["status"]]
            )
            
            if not user['battles'] % self.funcData._config["streak"]['count']['lose'][user["status"]]:
                botUtils.changeStats(
                    user, 
                    stats = self.funcData._config["streak"]['reward']['lose'][user["status"]]
                )
    
        elif (
            thing.get("balance")
            and thing['balance'][-1].lstrip('-').isdecimal()  
        ):
            user['balance'] += int(thing['balance'][-1])
    
        elif (
            thing.get("scraps")
            and thing['scraps'][-1].lstrip('-').isdecimal()  
        ):
            user['scraps'] += int(thing['scraps'][-1])    

        elif (
            thing.get("pack")
            and thing['pack'][0] in map(str, range(len(self.funcData._config["packSettings"])))
        ):
            user['packs'][int(thing['pack'][0])] += (
                int(thing['pack'][1])
                if len(thing['pack']) > 1 and thing['pack'][-1].lstrip("-").isdecimal()
                else 1
            )

        elif thing.get("cards", False) != False:
            cardData = thing.get("cards")

            if cardData[-1].lstrip('-').isdecimal(): 
                foundCardLevel, thing['cards'] = (
                    int(cardData[-1]),
                    thing['cards'][:-1]
                ) 
            else:
                foundCardLevel = 1

            foundCardID = next((
                cid
                for cid, cdt in enumerate(self.funcData._cards.allCards())
                if foundCardLevel in range(len('photo'))
                and cdt['name'].upper().find(" ".join(thing['cards'])) != -1
            ),
            None    
            )
            
            if foundCardID is None:
                raise errors.CardDoNotExist('cardDoesNotExist')
            
            user['cards'].append({
                "id": foundCardID,
                'level': foundCardLevel
            })    
                
        else: return
        
        self.funcData._DB.editDB(user)
    
    def remove(self, thing, data):
        if not thing:
            raise NotImplementedError('cantError')
        
        if (
            data['vk']['reply_id'] is not None 
            and data['vk']['reply_id'] != data['vk']['user']
        ):
            user = self.funcData._DB.getDataFromDB(data['vk']['reply_id'])
        
        else:
            user = data['db']
            if self.editDB:
                self.funcData._DB.editDB(user)
                
            self.editDB = False
        
        if not isinstance(thing,dict):
            raise NotImplementedError('cantError')
         
        if thing.get('win', False) != False:
            self.funcData._rank.rwin(user)
            
            if not user['battles'] % self.funcData._config["streak"]['count']['win'][user["status"]]:
                botUtils.changeStats(
                    user,
                    {key: -val
                    for key, val in self.funcData._config["streak"]['reward']['win'][user["status"]]
                    }
                )
            
            botUtils.changeStats(
                user,
                {'wins': -1} | {
                    key: -val
                    for key, val in self.funcData._config["battle"]['win'][user["status"]]
                }
            )
            

        elif thing.get('lose', False) != False:
            self.funcData._rank.rlose(user)
            
            if not user['battles'] % self.funcData._config["streak"]['count']['win'][user["status"]]:
                botUtils.changeStats(
                    user,
                    {key: -val
                    for key, val in self.funcData._config["streak"]['reward']['win'][user["status"]]
                    }
                )
            
            botUtils.changeStats(
                user,
                {'loses': -1} | {
                    key: -val
                    for key, val in self.funcData._config["battle"]['lose'][user["status"]]
                }
            )
    
        elif (
            thing.get("pack")
            and thing['pack'][0] in map(str, range(len(self.funcData._config["packSettings"])))
        ):
            user['packs'][int(thing['pack'][0])] -= (
                int(thing['pack'][1])
                if len(thing['pack']) > 1 and thing['pack'].lstrip("-").isdecimal()
                else 1
            )
    
        elif thing.get("cards"):
            cardLevel = 1
            if thing['cards'][-1].lstrip('-').isdecimal():
                cardLevel, thing['cards'] = (
                    int(thing["cards"][-1]),
                    thing["cards"][:-1],
                )
                
            foundCardID = next((
                    cardID
                    for cardID, cdDT in enumerate(
                            self.funcData._cards.getOwnedCards(user["cards"]),
                        )
                    if cdDT['level'] == cardLevel
                    and cdDT["name"].upper().find(" ".join(thing["cards"])) != -1
                
            ), None
            )
            
            if foundCardID is None:
                raise errors.NoCards('noСardsЗдк')
            
            user['cards'].pop(foundCardID)
    
        else: return
        
        self.funcData._DB.editDB(user)
        
    def profile(self, _, data):
        isChat = data['vk']['peer_id'] != data['vk']['user']
        
        if (
            data['vk']['reply_id'] is None 
            or data['vk']['reply_id'] == data['vk']['user'] 
        ):
            self.funcData._vk.send(
                self.funcData._dialogs.getDialogParsed(data['vk']['peer_id'], 'profile', userdata = data['db']) 
                | ({'keyboard': None} if isChat else {}) 
            )
    
        else:
            isAdmin = self.funcData._vk.isAdmin(data["vk"]["peer_id"], data["vk"]["user"])
            userData = self.funcData._DB.getDataFromDB(data['vk']['reply_id'])
            
            self.funcData._vk.send(
                self.funcData._dialogs.getDialogParsed(
                    data['vk']['user'] if isAdmin 
                        else data['vk']['peer_id'], 
                        
                    'profile' if isAdmin
                        else "profile_inline_otheruser",
                         
                    userdata = userData
                    ) 
            | {'keyboard': None}
            ) 
                
    def chance(self, chance, data):
        if not chance: 
            raise NotImplementedError('cantError')
        
        if chance[-1] not in map(str, range(0, 101)):
            raise IndexError('wrongNumber')
        
        self.funcData._vk.send(
            self.funcData._dialogs.getDialogPlain(
                data['vk']['peer_id'],
                text = 'Успешно' 
                    if randrange(1, 101) <= int(chance[0])
                    else 'Не успешно'
            )
        )
        
    def destroy(self, card, data):
        if len(data['db']['cards']) <= self.funcData._config.get("minimumCards", 0):
            raise errors.NoCardsToDestroy('noDestoyableCards')
        
        cardDataAll = self.funcData._cards.getOwnedCards(data['db']['cards'])
        
        if isinstance(card, list):
            cardIndex, cardData = next(
                (
                (cidx, cdt)
                for cidx, cdt in enumerate(cardDataAll)
                if cdt['name'].upper().find(" ".join(card)) != -1
                and cdt['level'] == 1
                ),
                (None, None)
            )
    
        elif card.get('rarity') and card['rarity'][0].lstrip('-').isdecimal():
            cardIndex, cardData = next(
                (
                (cidx, cdt)
                for cidx, cdt in enumerate(cardDataAll)
                if str(cdt['rarity']) == card['rarity'][0]
                and cdt['level'] == 1
                ),
                (None, None)
            )
            
        else:
            raise NotImplementedError('cantError')
        
        if cardIndex is None:
            raise errors.NoCardsToDestroy('noDestoyableCards')
        
        self.editDB = True
        data['db']['cards'].pop(cardIndex)
        data['db']['scraps'] += self.funcData._config["breakPrice"][str(cardData["rarity"])]

        self.funcData._vk.send(
            self.funcData._dialogs.getDialogPlain(
                data['vk']['peer_id'],
                text = f'Разорвана карта {cardData["name"]}. Вы получаете {self.funcData._config["breakPrice"][str(cardData["rarity"])]} обрывков',
            )
        )    
    
    def upgrade(self, card, data):
        cardData = self.funcData._cards.getOwnedCards(data['db']['cards'])
        
        upgradeableCards = [
            cardData[cd['index']] | cd
            for cd in botUtils.findUpgradeableCards(
            cardData,
            self.funcData._config['upgrade'],
            data['db']['scraps']        
        )]
        
        if not card:
            if not upgradeableCards:
                raise errors.NoCardsUpgrade('upgradeFail')

            self.funcData._vk.send(
                self.funcData._dialogs.getDialogPlain(
                    data['vk']['peer_id'],
                    text = f"""
Список карт, доступных для улучшения:\n\n
{
    chr(10).join([
        botUtils.formatCards(cd)
        for cd in upgradeableCards
    ])
}

Стобы улучшить карту, напишите .ап <карта>
                    """
                )
            )
            
        else:
            if not isinstance(card, list): return
            
            card = next((
                cardd
                for cardd in upgradeableCards
                if cardd['name'].upper().find(' '.join(card)) != -1
            ), None)
            
            if card is None:
                raise errors.NoCardsUpgrade('upgradeFail')
            
            self.funcData._vk.send(
                self.funcData._dialogs.getDialogParsed(
                    data['vk']['peer_id'],
                    "upgraded",
                    userdata = data['db'],
                    selectCard = card['index']
                )
            )
            
            self.editDB = True
            if card.get('repeat'):
                cardIndex = card['index']
                  
                for _ in range(card.get('repeat') - 1):
                    data['db']['cards'].pop(
                        data['db']['cards'].index(
                            data['db']['cards'][cardIndex]
                        )
                    )
                    cardIndex -= 1
                    
                data['db']['cards'][cardIndex]['level'] += 1  
                
            elif card.get('scrapCost'):
                data['db']['cards'][card['index']]['level'] += 1
                data['db']['scraps'] -= card['scrapCost'] 

    def __launcher(self, data, payload):
        for func in payload:
            for key, val in func.items():
                method = getattr(self, key, None)
                if method is None: continue
                
                
                try:
                    method(val, data)
                except Exception as e:
                    self.funcData._vk.send(
                        self.funcData._dialogs.getDialogPlain(
                            data['vk']['peer_id'],
                            preset=e.args
                        )
                    )
    
    def __init__(self, funcData:functionData , data = None, payload = None, *, launch:bool = True):
        self.funcData = funcData
        
        self.editDB = False
        
        if launch:
            self.__launcher(data, payload)