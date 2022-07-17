from os.path import join, dirname
from dataclasses import dataclass
from yaml import safe_load
from assets.cards import cards
from assets.dialog import dialog

from backend.vk import VK


@dataclass
class functionData:
    _vk: VK = None
    _dialogs: dialog = None
    _cards: cards = None
    __file: str = 'functions.yaml'
    
    def __init__(self, parent):
        with open(
            join(dirname(__file__), "configs", self.__file), "r", encoding="utf-8"
        ) as conf:
            self._config = safe_load(conf)
            
        self._vk = parent._vk
        self._dialogs = parent._dialogs
        self._cards = parent._card







class generalFunctions:
    def dialog(self, dialog, data):
        self.funcData._vk.send(
                self.funcData._dialogs.getDialogParsed(data['vk']['peer_id'], dialog, userdata = data['db'])
            )
    
    def upgrade(self, card, data):
        self.editDB = True
        
    
    
    
    
    
    
    
    
    def __init__(self, funcData:functionData , data, payload):
        self.funcData = funcData
        
        self.editDB = False
        
        for func in payload:
            for key, val in func.items():
                method = getattr(self, key, None)
                if method is None: continue
                
                method(val, data)


        

    






















# class func:
#     def __init__(self, parent, *, file="functions.yaml"):
#         from yaml import safe_load
#         from os.path import join, dirname





#         self.rank = rank("rank.yaml", parent._card)

#         nest_asyncio.apply()
#         self._evLoop = nest_asyncio.asyncio.get_event_loop()

#         self.localStorage = {"active": [], "lobby": [], "prep": []}

#     def botFunctions(self, data, isChat, func={}):
#         def dialog(dialog):
#             self.__vk.send(
#                 self.__dialogs.getDialog(data, dialog, self.__card, toGroup=isChat)
#             )
#             return True

#         def game(role):
#             if data["db"]["battles"] <= 0 and not ("stop" in role or "judge" in role):
#                 raise errors.NoBattles

#             self.gameOnline(data, payload=role)

#         def upgrade(what):
#             whichCards = self.__card.getOwnedCards(data["db"]["cards"])

#             upgradedCards = []

#             if not what:
#                 for i, c in zip(whichCards, data["db"]["cards"]):
#                     if (
#                         c["level"] >= i["maxlevel"]
#                         or data["db"]["cards"].count(c)
#                         < self.__config["repeatsNeeded"][str(i["rarity"])]
#                     ):
#                         continue

#                     duplicates = [
#                         j for j, v in enumerate(data["db"]["cards"]) if v == c
#                     ][: self.__config["repeatsNeeded"][str(i["rarity"])]]
#                     if not duplicates:
#                         continue

#                     upgradedCards.append(duplicates[0])
#                     [
#                         data["db"]["cards"].pop(i) and whichCards.pop(i)
#                         for i in reversed(duplicates[1:])
#                     ]
#                     data["db"]["cards"][duplicates[0]]["level"] += 1

#             elif not isinstance(what, list):
#                 return

#             elif (
#                 what[0].lstrip("-").isdecimal()
#                 and what[0] in self.__config["scrapCosts"]
#             ):
#                 if data["db"]["scraps"] < self.__config["scrapCosts"][what[0]]:
#                     raise errors.NotEnough


#                 upgradeable = [
#                     (i, v)
#                     for i, v in enumerate(whichCards)
#                     if v["rarity"] == int(what[0])
#                     and data["db"]["cards"][i]["level"] < v["maxlevel"]
#                 ]

#                 if not upgradeable:
#                     self.__vk.send(
#                         self.__dialogs.getDialog(data, "upgrade_fail", toGroup=True)
#                     )
#                     return

#                 selectedCard = choice(upgradeable)
#                 upgradedCards.append(selectedCard[0])

#                 data["db"]["scraps"] -= self.__config["scrapCosts"][
#                     str(selectedCard[1]["rarity"])
#                 ]
#                 data["db"]["cards"][selectedCard[0]]["level"] += 1

#             else:
#                 i, n = next(
#                     (
#                         (i, n)
#                         for i, n in enumerate(whichCards)
#                         if n["name"].upper().find(" ".join(what)) != -1
#                         and data["db"]["cards"][i]["level"] < n["maxlevel"]
#                     ),
#                     (None, None),
#                 )

#                 if i is None:
#                     raise errors.NoCards

#                 if data["db"]["scraps"] < self.__config["scrapCosts"][str(n["rarity"])]:
#                     raise errors.NotEnough

#                 upgradedCards.append(i)

#                 data["db"]["scraps"] -= self.__config["scrapCosts"][str(n["rarity"])]
#                 data["db"]["cards"][i]["level"] += 1

#             self.__vk.send(
#                 self.__dialogs.getDialog(
#                     data,
#                     "upgrade_fail"
#                     if not len(upgradedCards)
#                     else "upgraded"
#                     if len(upgradedCards) == 1
#                     else "upgraded_multi",
#                     self.__card,
#                     upgradedCards,
#                     toGroup=True,
#                 )
#             )
#             return True

#         def addCardsPool(pool):
#             data["db"]["cards"].extend(self.__card.getCardByPool(pool))
#             self.__vk.send(
#                 self.__dialogs.getDialog(
#                     data,
#                     "poolcards",
#                     self.__card,
#                     selectCard=list(
#                         islice(reversed(range(len(data["db"]["cards"]))), 0, 3)
#                     ),
#                 )
#             )
#             return True

#         def getPack(pack):
#             if self.__config["packSettings"][pack]["price"] > data["db"]["balance"]:
#                 raise errors.NotEnough

#             data["db"]["balance"] -= self.__config["packSettings"][pack]["price"]
#             data["db"]["packs"][pack] += 1

#             self.__vk.send(self.__dialogs.getDialog(data, "gotPack"))

#             return True

#         def showCards(which):
#             if not data["db"]["cards"]:
#                 raise errors.NoCards

#             cds = self.__card.getOwnedCards(data["db"]["cards"])
#             cds = [
#                 (cds.count(n), n) for i, n in enumerate(cds) if n not in cds[i + 1 :]
#             ]

#             if not which:
#                 for c, k in cds:
#                     self.__vk.send(
#                         {
#                             "peer_id": data["vk"].get("peer_id"),
#                             "message": f"x{c}" if c > 1 else None,
#                         },
#                         attachments=k["attachment"],
#                     )
#                 return

#             if isinstance(which, list):
#                 filteredCards = [
#                     n for n in cds if n[1]["name"].upper().find(" ".join(which)) != -1
#                 ]

#             elif (
#                 "level" in which.keys()
#                 and which["level"]
#                 and which["level"][0].lstrip("-").isdecimal()
#             ):
#                 cds = [
#                     i
#                     for i in list(
#                         {frozenset(i.items()): i for i in data["db"]["cards"]}.values()
#                     )
#                     if i["level"] == int(which["level"][0])
#                 ]
#                 filteredCards = [
#                     (data["db"]["cards"].count(c), k)
#                     for c, k in zip(cds, self.__card.getOwnedCards(cds))
#                 ]

#             elif (
#                 "rarity" in which.keys()
#                 and which["rarity"]
#                 and which["rarity"][0].lstrip("-").isdecimal()
#             ):
#                 filteredCards = [
#                     (c, k) for c, k in cds if k["rarity"] == int(which["rarity"][0])
#                 ]

#             else:
#                 return

#             if not filteredCards:
#                 raise errors.NoCards

#             for c, k in filteredCards:
#                 self.__vk.send(
#                     {
#                         "peer_id": data["vk"].get("peer_id"),
#                         "message": f"x{c}" if c > 1 else None,
#                     },
#                     attachments=k["attachment"],
#                 )

#         def give(what):
#             if not what or data["vk"]["reply_id"] is None:
#                 raise NotImplementedError

#             thatUser = self.__db.getDataFromDB(data["vk"]["reply_id"])
#             if thatUser is None:
#                 return False
#             print(what)

#             if (
#                 isinstance(what, list)
#                 and what
#                 and what[0] in {i.upper() for i in self.__dialogs.getStatus()}
#             ):
#                 thatUser["status"] = next(
#                     num
#                     for num, status in enumerate(self.__dialogs.getStatus())
#                     if what[0].upper() == status.upper()
#                 )

#                 premDays = (
#                     int(what[-1])
#                     if len(what) > 1 and what[-1].isdecimal()
#                     else self.__config["defaultPremium"]
#                 )
#                 thatUser["day"] = int(time() // 86400 + premDays + 1)

#                 self.__vk.send(
#                     {
#                         "message": f'Вам был выдан {self.__dialogs.getStatus()[thatUser["status"]]} на {int(thatUser["day"] - 1 - time() // 86400)} {"день" if int(thatUser["day"] - 1 - time() // 86400) == 1 else "дня" if int(thatUser["day"] - 1 - time() // 86400) < 5 else "дней"}',
#                         "id": data["vk"]["reply_id"],
#                     }
#                 )

#             elif "win" in what:
#                 print(thatUser)
#                 self.rank.win(user=thatUser)
#                 thatUser["wins"] += 1
#                 thatUser["balance"] += self.__config["userLevels"][thatUser["status"]][
#                     "winBalance"
#                 ]
#                 thatUser["scraps"] += self.__config["userLevels"][thatUser["status"]][
#                     "winScraps"
#                 ]
#                 if thatUser["wins"] == 5:
#                     thatUser["balance"] += 20

#             elif "lose" in what:
#                 self.rank.lose(user=thatUser)
#                 thatUser["loses"] += 1
#                 thatUser["balance"] += self.__config["userLevels"][thatUser["status"]][
#                     "loseBalance"
#                 ]
#                 if thatUser["loses"] == 5:
#                     thatUser["scraps"] += 5

#             elif "balance" in what.keys():
#                 thatUser["balance"] += int(what["balance"][0])

#             elif "scraps" in what.keys():
#                 thatUser["scraps"] += int(what["scraps"][0])

#             elif (
#                 "pack" in what.keys()
#                 and what["pack"][0].lstrip("-").isdecimal()
#                 and int(what["pack"][0]) < len(self.__config["packSettings"])
#             ):
#                 thatUser["packs"][int(what["pack"][0])] += (
#                     int(what["pack"][1])
#                     if len(what["pack"]) > 1 and what["pack"][1].lstrip("-").isdecimal()
#                     else 1
#                 )

#             elif "cards" in what:
#                 if not what:
#                     return False

#                 foundCardLevel = 1
#                 if what["cards"][-1].lstrip("-").isdecimal():
#                     foundCardLevel, what["cards"] = (
#                         int(what["cards"][-1]),
#                         what["cards"][:-1],
#                     )

#                 foundCardID = next(
#                     (
#                         cardID
#                         for cardID, cd in enumerate(self.__card.allCards())
#                         if foundCardLevel <= len(cd["photo"])
#                         and cd["name"].upper().find(" ".join(what["cards"])) != -1
#                     ),
#                     None,
#                 )

#                 if foundCardID is None:
#                     self.__vk.send(
#                         {"peer_id": data["vk"]["peer_id"], "message": "Такой карты нет"}
#                     )
#                     return

#                 thatUser["cards"].append({"id": foundCardID, "level": foundCardLevel})

#             else:
#                 return False

#             print(thatUser)

#             self.__db.editDB(thatUser)

#             return False

#         def remove(what):
#             if not what:
#                 raise NotImplementedError

#             thatUser = self.__db.getDataFromDB(data["vk"]["reply_id"]) if data["vk"]["reply_id"] is None else data['db']
#             if thatUser is None:
#                 return False

#             if "win" in what:
#                 self.rank.rwin(user=thatUser)
#                 thatUser["balance"] -= self.__config["userLevels"][thatUser["status"]][
#                     "winBalance"
#                 ]
#                 thatUser["scraps"] -= self.__config["userLevels"][thatUser["status"]][
#                     "winScraps"
#                 ]
#                 if thatUser["wins"] == 5:
#                     thatUser["balance"] -= 20
#                 thatUser["wins"] -= 1

#             elif "lose" in what:
#                 self.rank.rlose(user=thatUser)
#                 thatUser["balance"] -= self.__config["userLevels"][thatUser["status"]][
#                     "loseBalance"
#                 ]
#                 if thatUser["loses"] == 5:
#                     thatUser["scraps"] -= 5
#                 thatUser["loses"] -= 1

#             elif (
#                 "pack" in what
#                 and what["pack"][0].lstrip("-").isdecimal()
#                 and int(what["pack"][0]) < len(self.__config["packSettings"])
#             ):
#                 thatUser["packs"][int(what["pack"][0])] -= (
#                     int(what["pack"][1])
#                     if len(what["pack"]) > 1 and what["pack"][1].lstrip("-").isdecimal()
#                     else 1
#                 )

#             elif "cards" in what:
#                 if not what:
#                     return

#                 selectedCardLevel = 1
#                 if what["cards"][-1].lstrip("-").isdecimal():
#                     selectedCardLevel, what["cards"] = (
#                         int(what["cards"][-1]),
#                         what["cards"][:-1],
#                     )

#                 foundCardID = next(
#                     (
#                         cardID
#                         for cardID, (cdDB, cdDT) in enumerate(
#                             zip(
#                                 thatUser["cards"],
#                                 self.__card.getOwnedCards(thatUser["cards"]),
#                             )
#                         )
#                         if cdDB["level"] == selectedCardLevel
#                         and cdDT["name"].upper().find(" ".join(what["cards"])) != -1
#                     ),
#                     None,
#                 )

#                 if foundCardID is None:
#                     self.__vk.send(
#                         {
#                             "peer_id": data["vk"]["peer_id"],
#                             "message": "У него нет такой карты",
#                         }
#                     )
#                     return

#                 thatUser["cards"].pop(foundCardID)

#             else:
#                 return False

#             self.__db.editDB(thatUser)

#             return False

#         def profile(_):
#             if not isChat and data["vk"]["reply_id"] is None:
#                 self.__vk.send(self.__dialogs.getDialog(data, "profile", toGroup=True))
#             elif data["vk"]["reply_id"] is None or data["vk"]["reply_id"] < 1:
#                 self.__vk.send(
#                     self.__dialogs.getDialog(data, "profile_inline", toGroup=True)
#                 )
#             else:
#                 dbUser = self.__db.getDataFromDB(data["vk"]["reply_id"])
#                 if dbUser is None:
#                     return

#                 if not self.__vk.isAdmin(data["vk"]["peer_id"], data["vk"]["user"]):
#                     self.__vk.send(
#                         self.__dialogs.getDialog(
#                             {"vk": data["vk"], "db": dbUser},
#                             "profile_inline_otheruser",
#                             toGroup=True,
#                         )
#                     )
#                 else:
#                     self.__vk.send(
#                         self.__dialogs.getDialog(
#                             {"vk": data["vk"], "db": dbUser}, "profile_inline"
#                         )
#                     )

#         def chance(chance):
#             if (
#                 not chance
#                 or not chance[0].lstrip("-").isdecimal()
#                 or int(chance[0]) not in range(1, 101)
#             ):
#                raise IndexError # Out of range

#             self.__vk.send(
#                 {
#                     "peer_id": data["vk"].get("peer_id"),
#                     "message": "Успешно"
#                     if randrange(1, 101) <= int(chance[0])
#                     else "Не успешно",
#                 }
#             )

#         def destroy(what):
#             if len(data["db"]["cards"]) <= self.__config.get("minimumCards", 0):
#                 raise errors.NoCards

#             cds = self.__card.getOwnedCards(data["db"]["cards"])

#             if isinstance(what, list):
#                 i, n = next(
#                     (
#                         (i, n)
#                         for i, (c, n) in enumerate(zip(data["db"]["cards"], cds))
#                         if n["name"].upper().find(" ".join(what)) != -1
#                         and c["level"] == 1
#                     ),
#                     (None, None),
#                 )

#             elif "rarity" in what and what["rarity"][0].lstrip("-").isdecimal():
#                 i, n = next(
#                     (
#                         (i, n)
#                         for i, (c, n) in enumerate(zip(data["db"]["cards"], cds))
#                         if n["rarity"] == int(what["rarity"][0]) and c["level"] == 1
#                     ),
#                     (None, None),
#                 )

#             if i is None:
#                 raise errors.NoCards

#             data["db"]["cards"].pop(i)
#             data["db"]["scraps"] += self.__config["breakPrice"][str(n["rarity"])]

#             self.__vk.send(
#                 {
#                     "peer_id": data["vk"]["peer_id"],
#                     "message": f'Разорвана карта {n["name"]}. Вы получаете {self.__config["breakPrice"][str(n["rarity"])]} обрывков',
#                 }
#             )
#             return True

#         def openPack(which):
#             if data["db"]["packs"][which] < 1:
#                 raise errors.NoPack

#             data["db"]["packs"][which] -= 1

#             data["db"]["cards"].append(
#                 self.__card.getCardByRarity(
#                     chances=self.__config["packSettings"][which]["rarities"]
#                 )
#             )

#             self.__vk.send(
#                 self.__dialogs.getDialog(data, "purchase", self.__card, toGroup=True)
#             )

#             return True

#         def flip(_):
#             self.__vk.send(
#                 self.__dialogs.getDialog(
#                     data, choice(["firstPlayer", "secondPlayer"]), toGroup=True
#                 )
#             )

#         func, args = next(iter(func.items()))
#         try:
#             return locals()[func](args) if func in locals() else False
        
#         except errors.NotEnough:
#             self.__vk.send(self.__dialogs.getDialog(data, "notenough", toGroup=True))
#         except errors.NoCards:
#             self.__vk.send(self.__dialogs.getDialog(data, "nocards", toGroup=True))
#         except errors.NoPack:
#             self.__vk.send(self.__dialogs.getDialog(data, "nopack", toGroup=True))
#         except IndexError:
#             self.__vk.send({"peer_id": data["vk"].get("peer_id", data["vk"]['user']),"message": "Недопустимое значение"})  
#         except NotImplementedError:
#             self.__vk.send({"peer_id": data["vk"]["peer_id"], "message": "Такое сделать я не могу..."})
#         except errors.NoUser:
#             self.__vk.send(self.__dialogs.getDialog(data, "nouser", toGroup=True))
#         except errors.NoBattles:
#             self.__vk.send(self.__dialogs.getDialog(data, "nobattles"))
            
#         finally: return