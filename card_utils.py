class botUtils:
    def formatCards(cardData: dict, cardCount: int = 1):
        
        """
        About repeat or scraps
        If bool and it's True, then repeat
        If int, than it's scraps
        """  
        return ' '.join(
            filter(
                None, [
                    cardData['raritySymbol'],
                    cardData['name'],
                    f'(Ур. {cardData["level"]})' if cardData["level"] > 1 else '',
                    f'(x{cardCount})' if cardCount > 1 else '',
                    '(За повторки)' if cardData.get('repeat') else f'({cardData.get("scrapCost")} {"Обрывок" if cardData.get("scrapCost") % 10 == 1 else "Обрывка" if cardData.get("scrapCost") % 10 > 1 and cardData.get("scrapCost") % 10 < 5 else "Обрывков"})' if cardData.get("scrapCost") else ''                   
                ]
            )
        )  
        
    def changeStats(data:dict, stats:dict = None, removeStats: dict = None):
        if stats is None: stats = {}
        if removeStats is None: removeStats = {}
        
        for key, val in stats.items():
            data[key] += val 
            
        for key, val in removeStats.items():
            data[key].remove(val)
            
    def findUpgradeableCards(cards: list, params: dict, scrapCount:int = 0) -> list:
        cardData = [
            (card, cards.count(card), cidx)
            for cidx,card in enumerate(cards)
            if card not in cards[cidx + 1:]  
            and card['level'] < card['maxlevel'] 
        ]
        
        upgradeableCards = []
        
        for card, cardCount, cardn in cardData:
            if (
                cardCount >= params['repeatsNeeded'][str(card['rarity'])][card['level']-1]
            ): 
                upgradeableCards.append({
                    "index": cardn,
                    "repeat": params['repeatsNeeded'][str(card['rarity'])][card['level']-1]
                })
           
            else:
                cardCost = params['scrapCosts']['defaultPrice'] + \
                params['scrapCosts']['rarityRatios'][str(card['rarity'])] * \
                card['level'] ** params['scrapCosts']['defaultPower']
                
                if scrapCount >= cardCost:
                    upgradeableCards.append({
                        "index": cardn,
                        "scrapCost": int(cardCost)
                    })  
               
        return upgradeableCards