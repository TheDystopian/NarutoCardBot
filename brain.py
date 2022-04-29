from time import time
from random import choice
from itertools import chain

# CONSTANTS
# FIELDS
DB = 'db'
VK = 'vk'
BATTLES = 'battles'
DAY = 'day'
STATUS = 'status'
BALANCE = 'balance'
CARDS = 'cards'
SCRAPS = 'scraps'
WINS = 'wins'
LOSES = 'loses'
JUDGE = 'judge'

# PAYLOADS
DIALOG = 'dialog'
PRICE = 'price'
SCRAP_PRICE = 'scraps'
ADD_CARDS_POOL = 'addCardsPool'
ADD_CARDS = 'addCards'
UPGRADE = 'upgrade'
REPEAT = 'repeat'
SENDCARDS = 'sendCards'

# PARAMS
MAXLEVEL = 2
USERLEVELS = [{'battles':5, 'win_award_scraps': 3, 'win_award_balance': 10, 'lose_award': 5}, {'battles':6, 'win_award_scraps': 3, 'win_award_balance': 10, 'lose_award': 10}, {'battles':7, 'win_award_scraps': 3, 'win_award_balance': 15, 'lose_award': 10}, {'battles':7, 'win_award_scraps': 3, 'win_award_balance': 15, 'lose_award': 10}, {'battles':32767, 'win_award_scraps': 5000, 'win_award_balance': 10000, 'lose_award': 10000}, {'battles':7, 'win_award_scraps': 3, 'win_award_balance': 15, 'lose_award': 10}]
COMMANDS = {'win': {'ПОБЕДА'}, 'lose': {'ПОРАЖЕНИЕ'}, 'judge': {'СУДЬЯ'}, 'flip': {'ФЛИП'}}
CALLCOMMAND = {'.','/','#','!'}
ALLPHRASES = set().union(*COMMANDS.values())


def dailyEvent(data):
    if time() // 86400 < data[DB][DAY] or time() % 86400 // 3600 < 9: return

    data[DB][BATTLES] = USERLEVELS[data[DB][STATUS]]['battles']
    data[DB][LOSES] = 0
    data[DB][WINS] = 0
    data[DB][JUDGE] = 0

    data[DB][DAY] = int(time() // 86400 + 1)

def brains_main_bot(data, vk, dialogs, cards):
    # Seems like YandereDev code
    # But each payload needs to be handled differently
    # So there is a lot of condition statements
    def payloadHandle(data, vk, dialogs, cards):
        # Payload is in data['vk']['payload']
        enoughBalance,enoughScraps,repeated,sendCard = True,True, None, -1

        # Dialog to list
        # May be useful for multi-dialogs
        if not DIALOG in data[VK]['payload']:
            data[VK]['payload'][DIALOG] = []
        elif not isinstance(data[VK]['payload'][DIALOG],list):
            data[VK]['payload'][DIALOG] = [data[VK]['payload'][DIALOG]]

        # Balance part
        # Price used in purchases 
        if PRICE in data[VK]['payload']:
            if data[DB][BALANCE] <data[VK]['payload'][PRICE]:
                data[VK]['payload'][DIALOG].append('notenough')
                enoughBalance = False
            else:
                data[DB][BALANCE] -= data[VK]['payload'][PRICE]
        
        # Scrap part
        # They used in upgrading cards
        # Their functionality is WIP
        if SCRAP_PRICE in data[VK]['payload']:
            if data[DB][SCRAP_PRICE] < data[VK]['payload'][SCRAP_PRICE]:
                data[VK]['payload'][DIALOG].append('notenough')
                enoughScraps = False
            else:
                data[DB][SCRAP_PRICE] -= data[VK]['payload'][SCRAP_PRICE] 

        # Add cards by pool
        # Useful for starting cards 
        if ADD_CARDS_POOL in data[VK]['payload'] and enoughBalance:
            data[DB][CARDS] += cards.getCardByPool(data[VK]['payload'][ADD_CARDS_POOL])
            sendCard = slice(0,3,1)
            data[VK]['payload'][DIALOG].insert(0,'poolcards')




        # Add cards by rarity
        if ADD_CARDS in data[VK]['payload'] and enoughBalance:
            data[DB][CARDS] += [cards.getCardByRarity(chances=data[VK]['payload'][ADD_CARDS])]
            data[VK]['payload'][DIALOG].append('purchase')

        if REPEAT in data[VK]['payload']:
            repeated = {id:cdDt for id,cdDt in enumerate(data[DB][CARDS]) if data[DB][CARDS].count(cdDt) >= data[VK]['payload'][REPEAT]}

        if UPGRADE in data[VK]['payload'] and enoughScraps:
            cardPool = data[DB][CARDS] if repeated is None else list(repeated.values())
            cardData = cards.getOwnedCards(cardPool)
            
            upgradeable = [id for id,cdDt in enumerate(cardData) if cardPool[id]['level'] < MAXLEVEL and cdDt['rarity'] == data[VK]['payload'][UPGRADE]]
            
            if upgradeable != []:
                if REPEAT in data[VK]['payload']:
                    upgradeThis = choice([list(repeated.keys())[i] for i in upgradeable])

                    # Choice will generate each comprehension, so we'll do it AFTER choice
                    upgradeThis = [id for id,cdDt in repeated.items() if repeated[upgradeThis] == cdDt]

                    upgradeCard = upgradeThis[0]
                    [data[DB][CARDS].pop(i) for i in upgradeThis[1:]]

                else:
                    upgradeCard = choice(upgradeable)

                data[VK]['payload'][DIALOG].append('upgraded')

                sendCard = upgradeCard

                data[DB][CARDS][upgradeCard]['level'] += 1

            else:
                if SCRAP_PRICE in data[VK]['payload']: 
                    data[DB][SCRAP_PRICE] += data[VK]['payload'][SCRAP_PRICE] 
                data[VK]['payload'][DIALOG].append('upgrade_fail')

        if SENDCARDS in data[VK]['payload']:
            levelFilter = [i for i in data[DB][CARDS] if i['level'] == data[VK]['payload'][SENDCARDS]]
            if levelFilter == []: data[VK]['payload'][DIALOG].append('nocards')
            else: vk.send(sendable = {'id':data[VK]['user']} ,attachments = chain.from_iterable([i['attachment'] for i in cards.getOwnedCards(levelFilter,sortByRarity = True)]))

        # Send message
        if data[VK]['payload'][DIALOG] != []:
            vk.send(dialogs.getDialog(data,cards, sendCard))

    if data[DB] is None: 
        vk.send(dialogs.getDialog(data,cards))
        return None

    dailyEvent(data)

    if data[VK]['payload'] is None: return False

    payloadHandle(data, vk, dialogs, cards)

    return True

def brains_chat_bot(data,vk):
    dailyEvent(data)

    if not len(data[VK]['text']) or data[VK]['text'][0] not in CALLCOMMAND: return False

    data[VK]['text'] = data[VK]['text'][1:].upper().strip()

    if not data[VK]['text'] in ALLPHRASES: return False

    if data[VK]['text'] in COMMANDS['win']:
        if not data[DB][BATTLES]: 
            vk.send({'id': data[VK]['user'], 'message': 'У вас нет боев'})
            return False

        data[DB][BALANCE] += USERLEVELS[data[DB][STATUS]]['win_award_balance']
        data[DB][SCRAPS] += USERLEVELS[data[DB][STATUS]]['win_award_scraps']
        data[DB][BATTLES] -= 1
        data[DB][WINS] += 1
        if data[DB][WINS] == 5: data[DB][SCRAPS] += 5

        vk.send({'id': data[VK]['user'], 'message': 'Вы победили. Вы получаете дополнительную награду'})

    elif data[VK]['text'] in COMMANDS['lose']:
        if not data[DB][BATTLES]: 
            vk.send({'id': data[VK]['user'], 'message': 'У вас нет боев'})
            return False

        data[DB][BALANCE] += USERLEVELS[data[DB][STATUS]]['lose_award']
        data[DB][BATTLES] -= 1
        data[DB][LOSES] += 1
        if data[DB][LOSES] == 5: data[DB][BALANCE] += 20

        vk.send({'id': data[VK]['user'], 'message': 'Вы проиграли'})
    elif data[VK]['text'] in COMMANDS['flip']:
        vk.send({'message': choice(['Ходит первый игрок','Ходит второй игрок']), 'peer_id': data[VK]['peer_id']})
    elif data[VK]['text'] in COMMANDS['judge']:
        data[DB][BALANCE] += 1
        data[DB][JUDGE] += 1
        if data[DB][JUDGE] == 10: data[DB][BALANCE] += 10

    return True
