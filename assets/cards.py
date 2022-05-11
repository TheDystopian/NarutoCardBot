from random import choice,randint
from operator import itemgetter
from os.path import dirname,join

class cards:
    def __init__(self, file):
        from yaml import safe_load
        with open(join(dirname(__file__),file),'r',encoding='utf-8') as cfg:
            self.__cards = safe_load(cfg)

        self.__pooledCards = [i for i in self.__cards['cards'] if 'pool' in i]

    def getCardByRarity(self, cards = None, chances = {}):
        if '0' in chances:
            return {
                'id': randint(0,len(self.__cards['cards']) - 1),
                'level': 1
            }

        chances = {k:chances[k] for k in sorted(chances,reverse=True)} if chances != {} else self.__cards['defaultProbs']

        rarities = {str(i.get('rarity')) for i in cards} if cards is not None else set(chances)
        if cards is None: cards = self.__cards['cards']

        # first filter 
        chances = {k: v for k,v in chances.items() if k in rarities}

        if '1' in rarities and not '1' in chances: chances['1'] = 100 - sum(chances.values())

        prob = randint(1,sum(chances.values()))

        # then correct probabilities
        chances = {k:sum(list(chances.values())[:i+1]) for i, k in enumerate(chances.keys()) }

        # constant for list comrehension
        chosenRarity = next((k for k,v in chances.items() if prob <= v), '1')

        return {'id':self.__cards['cards'].index(choice([
        a for a in cards 
        if str(a['rarity']) == chosenRarity
        ])),
        'level':1}

    def getCardByPool(self,pool):
        if not isinstance(pool,list): pool = [pool]

        poolCont = [[b for b in self.__pooledCards if 'pool' in b and b['pool'] == c] for c in pool]

        # str is for json compatibility
        return [self.getCardByRarity(a) for a in poolCont]

    def getOwnedCards(self,carddata,sortByRarity = None):
        returnable = [{
            'name': self.__cards['cards'][i['id']]['name'],
            'rarity': self.__cards['cards'][i['id']]['rarity'],
            'attachment': self.__cards['cards'][i['id']]['photo'][f'lvl{i["level"]}']
        } for i in carddata]
        return returnable if sortByRarity is None else sorted(returnable, key=itemgetter('rarity'))

    def allCards(self):
        return self.__cards['cards']