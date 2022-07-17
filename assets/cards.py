from random import choice, randint
from operator import itemgetter
from os.path import dirname, join


class cards:
    def __init__(self, file):
        from yaml import safe_load

        with open(
            join(dirname(__file__), "..", "configs", file), "r", encoding="utf-8"
        ) as cfg:
            self.__cards = safe_load(cfg)

        self.__pooledCards = [i for i in self.__cards["cards"] if "pool" in i]
        self.__droppedCards = [
            id for id, card in enumerate(self.__cards["cards"]) if card["rarity"] > 0
        ]

    def getCardByRarity(self, cards=None, chances={}, level=1):
        if not isinstance(chances, dict):
            chances = {chances: None}
        if None in chances.values():
            return {
                "id": self.__cards["cards"].index(
                    choice(
                        [
                            i
                            for i in self.__cards["cards"]
                            if i["rarity"] == int(next(iter(chances.keys())))
                        ]
                    )
                )
                if next(iter(chances.keys())) != "0"
                else choice(self.__droppedCards),
                "level": 1,
            }

        chances = (
            {k: chances[k] for k in sorted(chances, reverse=True)}
            if chances != {}
            else self.__cards["defaultProbs"]
        )

        rarities = (
            {str(i.get("rarity")) for i in cards} if cards is not None else set(chances)
        )
        if cards is None:
            cards = self.__cards["cards"]

        # arrange to get correct rarities
        chances = {k: v for k, v in chances.items() if k in rarities}

        if "1" in rarities and not "1" in chances:
            chances["1"] = 100 - sum(chances.values())

        # get probability
        prob = randint(1, sum(chances.values()))

        # then correct probabilities
        chances = {
            k: sum(list(chances.values())[: i + 1])
            for i, k in enumerate(chances.keys())
        }

        # constant for list comrehension
        chosenRarity = next((k for k, v in chances.items() if prob <= v), "1")

        return {
            "id": self.__cards["cards"].index(
                choice([a for a in cards if str(a["rarity"]) == chosenRarity])
            ),
            "level": level,
        }

    def getCardByPool(self, pool):
        if not isinstance(pool, list):
            pool = [pool]

        poolCont = [
            [b for b in self.__pooledCards if "pool" in b and b["pool"] == c]
            for c in pool
        ]

        # str is for json compatibility
        return [self.getCardByRarity(a) for a in poolCont]

    def getOwnedCards(self, carddata: list, *, select: int|slice = None, sortByRarity: bool=None):
        if not carddata: return []
        selectedCards = carddata if select is None else carddata[select]
        if not isinstance(selectedCards, list): selectedCards = [selectedCards]
        returnable = [
            {
                "name": self.__cards["cards"][i["id"]]["name"],
                "rarity": self.__cards["cards"][i["id"]]["rarity"],
                "attachment": self.__cards["cards"][i["id"]]["photo"][
                    f'lvl{i["level"]}'
                ],
                "maxlevel": len(self.__cards["cards"][i["id"]]["photo"]),
            }
            for i in selectedCards
        ]
        return (
            returnable
            if sortByRarity is None
            else sorted(returnable, key=itemgetter("rarity"))
        )

    def allCards(self):
        return self.__cards["cards"]
