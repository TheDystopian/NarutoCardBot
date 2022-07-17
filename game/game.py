from backend.db import DB
from backend.vk import VK

from assets.dialog import dialog
from threading import Timer
from time import sleep


from functions import generalFunctions
from typing import Any, Optional
from dataclasses import dataclass, field
from os.path import join, dirname
from yaml import safe_load
from enum import Enum, auto



class role(Enum):
    """Player roles"""
    judge = ('Судья', 'judge')
    player = ("Игрок", 'player')
    
    def __init__(self, title, id):
        self.title = title
        self.id = id

class lobby_status(Enum):
    """Lobby statuses"""
    active = ("Идет игра")
    full = ("Полное. Ожидание готовности")
    free = ("Есть места")

    def __init__(self, title):
        self.title = title

@dataclass
class player:
    id: int
    role: role 
    ready: bool = False 
      

@dataclass
class lobby:
    timeoutTask: Timer = None
    players: list = field(default_factory=lambda:[])
    lobbyStatus: lobby_status = lobby_status.free
    location: list = None
    
    def getPlayerIDs(self, *, exclude:int = None): 
        return ','.join(map(str, [player.id for player in self.players if player.id != exclude]))
    
    def timeout(self, vk: VK, dialogs: dialog, compensation: int, punish: int):
        """
        About sum: 
        Format: {'compensation': int, 'pun': int}
        """
        
        db = DB()
    
        for player in lobby.players:
            playerData = db.getDataFromDB(player.id)
            
            if player.ready:
               vk.send(dialogs.getDialogPlain(userid=id, preset = 'AFKcomp'))
               playerData['balance'] += compensation
               if player.role == role.player:
                   playerData['battles'] += 1
            else:
                vk.send(dialogs.getDialogPlain(userid=id, preset = 'AFKpun'))
                playerData['balance'] -= punish
                
            db.editDB(playerData)
                
        self.location.remove(self) 
                

@dataclass      
class game:
    parent: Any
    _vk: VK = None
    _DB: DB = None
    _dialogs: dialog = None
    __file: str = 'game.yaml'
    
    def __init__(self, * ,parent = None):
        if self._vk is None:
            self._vk = parent._vk
        
        if self._DB is None:
            self._DB = parent._db
        
        if self._dialogs is None:
            self._dialogs = parent._dialogs
        
        
        with open(join(dirname(__file__), "..", "configs", self.__file), "r", encoding="utf-8") as fl:
            self._config = safe_load(fl)

class lobbies(game):    
    def __init__(self, parent):
        self.lobbies = []
        super().__init__(parent=parent)   
    
    def addToLobby(self, id: int, role: role):
        freeLobby = next(
            (lobby for lobby in self.lobbies 
            if lobby.lobbyStatus is lobby_status.free
            and len([
                player for player in lobby.players
                if player.role is role
                ]) 
            < self._config['maxPlayers'][role.id]), 
            None)
        
        self._vk.send(self._dialogs.getDialogPlain(userid=id, preset = 'lobbySearch'))
        
        if freeLobby is None:
            self.lobbies.append(
                lobby(
                    players = [player(id = id, role = role)], 
                    location = self.lobbies,
                ))
            return
        
        freeLobby.append(player(id = id, role = role))
        if len(freeLobby.players) == sum(self._config['maxPlayers'].values()):
            self.readyLobby(freeLobby)
            
    def readyLobby(self, lobby: lobby):
        self.__vk.send(
        self._dialogs.getDialogPlain(userid=lobby.getPlayerIDs(), preset = 'lobbyReady')
        ) 

        lobby.status = lobby_status.full
        for player in [player for player in lobby.players if player.role is not role.judge]:
            plr = self._DB.getDataFromDB(player.id)
            plr['battles'] -= 1
            self._DB.editDB(plr)
        
        
        lobby.timeoutTask = Timer(
            self._config.get('timeout',120),
            lobby.timeout(
                self._vk,
                self._dialogs,
                self._config['AFK'].get('compensation',5),
                self._config['AFK'].get('punish',5)
            )
        )

    def setReadiness(self, id, *, lobby: lobby = None):
        if lobby is None:
            lobby = self.findLobby(id)
            if lobby is None: return
        
        player = next((player for player in lobby.players if id == player.id), None)
        player.readiness = True
        if False not in [player.readiness for player in lobby.players]:
            self.allReady(lobby)
        
    def allReady(self, lobby: lobby):
        lobby.timeoutTask.cancel()
        
        self.__vk.send(
        self._dialogs.getDialogPlain(userid=lobby.getPlayerIDs(), preset = 'lobbyActive')
        ) 

        lobby.lobbyStatus = lobby_status.active
    
    def deletePlayer(self, id: int, *, lobby: lobby = None):
        if lobby is None:
            lobby = self.findLobby(id)
            if lobby is None: return
        try: 
            lobby.players.remove(
                next(
                    (player for player in lobby.players
                     if player.id == id)
                    )
                )
        finally:
            pass
        
    def findLobby(self, id: int):
        return next((lobby for lobby in self.lobbies 
                          if id in 
                          [player.id for player in lobby.players]
                          ), None)          

#class gameFunctions(game, generalFunctions):
#    pass
    # def communucate
    
    
    
    # def game():
    #     if 'stop' in 
        
        
        
    #     if 'judge' in 
        
    # def communicate(self,**_):
    #     player = []     
    
    
    
    # def __init__(self, command: list, data: dict):
    #     self.data = data
        
    #     for command in command:
    #         getattr(self, next(iter(command.keys())), 'communicate')(next(iter(command.values())))
            
        










# class game:
#     @dataclass
#     class game:
#         players: list = field(default_factory=list)
#         judge: int = 0
#         readiness: list = field(default_factory=lambda: [False, False, False])
#         bombTask: Any = None

#         def getFlattened(self):
#             return *self.players, self.judge

#         async def timeBomb(self, parent):
#             await nest_asyncio.asyncio.sleep(parent._func__config["readyWait"])
#             parent.localStorage["prep"].remove(self)
#             parent.AFKPunish(zip(self.getFlattened(), self.readiness))

#         def AFKPunish(self, who):
#             db = DB()
#             for users, readiness in who:
#                 userData = db.getDataFromDB(users)
#                 if readiness:
#                     self.__vk.send(
#                         self.__dialogs.getDialogPlain(users, "AFKCompensation")
#                     )
#                     userData["balance"] += self.__config["AFK"]["compensate"]
#                     userData["battles"] += 1
#                 else:
#                     self.__vk.send(self.__dialogs.getDialogPlain(users, "AFKPunish"))
#                     userData["balance"] -= self.__config["AFK"]["punish"]

#             db.editDB(userData)

#     async def waiter(self):
#         # Temporary fix to keep async event loop used
#         while True:
#             await nest_asyncio.asyncio.sleep(0.001)

#     def gameOnline(self, data, payload, lobby=None):
#         async def foundLobby(lobby):
#             for i, _id in enumerate(lobby.players):
#                 self.__vk.send(
#                     {
#                         "id": _id,
#                         "message": f'Игра найдена. Вы игрок {i+1}.\n Нажмите "Принять игру", чтобы начать игру',
#                         "keyboard": '{"buttons":[[{"action":{"type":"text","label":"Принять игру","payload":"{\\"game\\": \\"game\\"}"},"color":"primary"}]]}',
#                     }
#                 )
#             self.__vk.send(
#                 {
#                     "id": lobby.judge,
#                     "message": "Игра найдена. Вы судья",
#                     "keyboard": '{"buttons":[[{"action":{"type":"text","label":"Принять игру","payload":"{\\"game\\": \\"game\\"}"},"color":"primary"}]]}',
#                 }
#             )
#             for user in lobby.players:
#                 user = self.__db.getDataFromDB(user)
#                 user["battles"] -= 1
#                 self.__db.editDB(user)

#             self.localStorage["lobby"].remove(lobby)
#             self.localStorage["prep"].append(lobby)
#             lobby.bombTask = self._evLoop.create_task(
#                 self.localStorage["prep"][-1].timeBomb(self)
#             )
#             await nest_asyncio.asyncio.sleep(0.001)

#         async def readyPlayer(lobby):
#             lobby.readiness[lobby.getFlattened().index(data["vk"]["user"])] = True
#             if False in lobby.readiness or lobby not in self.localStorage["prep"]:
#                 return

#             lobby.bombTask.cancel()
#             self.__vk.send(
#                 {
#                     "peer_id": ",".join(map(str, lobby.getFlattened())),
#                     "message": "Все готовы! Можете писать",
#                     "keyboard": '{"buttons":[]}',
#                 }
#             )

#             self.localStorage["prep"].remove(lobby)
#             self.localStorage["active"].append(lobby)

#         async def matchMaking(payload):
#             if "stop" in payload:
#                 try:
#                     self.localStorage["lobby"].remove(
#                         next(
#                             i
#                             for i in self.localStorage["lobby"]
#                             if data["vk"]["user"] in i.getFlattened()
#                         )
#                     )
#                 except (KeyError, TypeError, StopIteration):
#                     self.__vk.send(self.__dialogs.getDialog(data, "profile"))
#                 else:
#                     self.__vk.send(self.__dialogs.getDialog(data, "cancel_search"))

#             elif data["vk"]["user"] in list(
#                 chain.from_iterable(
#                     {i.getFlattened() for i in self.localStorage["lobby"]}
#                 )
#             ):
#                 return

#             if "random" in payload:
#                 payload = choice(["judge", "player", "player"])

#             if "judge" in payload:
#                 # For - else actually makes sense here
#                 # Lobby.judge is int, so you cant use any (not iterable)
#                 # You cant use equations in listcomp
#                 # + i dont need to iterate agin to find full lobbies later
#                 for lobby in self.localStorage["lobby"]:
#                     if lobby.judge != 0:
#                         continue

#                     lobby.judge = data["vk"]["user"]
#                     if len(lobby.players) < 2:
#                         break

#                     await foundLobby(lobby)
#                     return
#                 else:
#                     self.localStorage["lobby"].append(self.game([], data["vk"]["user"]))
#                 self.__vk.send(self.__dialogs.getDialog(data, "find_lobby"))

#             elif "player" in payload:
#                 for lobby in self.localStorage["lobby"]:
#                     if len(lobby.players) >= 2:
#                         continue

#                     lobby.players.append(data["vk"]["user"])
#                     if len(lobby.players) < 2 or lobby.judge == 0:
#                         break

#                     await foundLobby(lobby)
#                     return
#                 else:
#                     self.localStorage["lobby"].append(self.game([data["vk"]["user"]]))
#                 self.__vk.send(self.__dialogs.getDialog(data, "find_lobby"))

#         def gameCommands(lobby):
#             def win(playerNumber):
#                 if (
#                     not data["vk"]["user"] == lobby.judge
#                     or not playerNumber
#                     or not isinstance(playerNumber, list)
#                     or not playerNumber[-1].isdecimal()
#                     or not int(playerNumber[-1]) in range(1, 3)
#                 ):
#                     return
#                 playerNumber = int(playerNumber[-1])

#                 dataUsers = [
#                     self.__db.getDataFromDB(userid) for userid in lobby.players
#                 ]
#                 winner = int(playerNumber) - 1

#                 dataUsers[winner]["balance"] += self.__config["userLevels"][
#                     dataUsers[winner]["status"]
#                 ]["winBalance"]
#                 dataUsers[winner]["scraps"] += self.__config["userLevels"][
#                     dataUsers[winner]["status"]
#                 ]["winScraps"]
#                 dataUsers[winner]["wins"] += 1

#                 self.__vk.send(
#                     {
#                         "id": dataUsers[winner]["id"],
#                         "message": f'Вы победили. Вы получаете {self.__config["userLevels"][dataUsers[winner]["status"]]["winBalance"]} монет и {self.__config["userLevels"][dataUsers[winner]["status"]]["winScraps"]} обрывка',
#                         "keyboard": '{"buttons":[[{"action":{"type":"text","label":"В профиль","payload":"{\\"dialog\\":\\"profile\\"}"},"color":"primary"}]]}',
#                     }
#                 )
#                 if dataUsers[winner]["wins"] == 5:
#                     dataUsers[winner]["balance"] += 20
#                     self.__vk.send(
#                         {
#                             "id": dataUsers[winner]["id"],
#                             "message": f"У вас винстрик 5. Вы получаете 20 монет",
#                         }
#                     )

#                 self.rank.win(user=dataUsers[winner])

#                 self.__db.editDB(dataUsers[winner])

#                 for users in [n for i, n in enumerate(dataUsers) if i != winner]:
#                     users["balance"] += self.__config["userLevels"][users["status"]][
#                         "loseBalance"
#                     ]
#                     users["loses"] += 1

#                     self.__vk.send(
#                         {
#                             "id": users["id"],
#                             "message": f'Вы проиграли. Вы получаете {self.__config["userLevels"][users["status"]]["loseBalance"]} монет',
#                             "keyboard": '{"buttons":[[{"action":{"type":"text","label":"В профиль","payload":"{\\"dialog\\":\\"profile\\"}"},"color":"primary"}]]}',
#                         }
#                     )
#                     if users["loses"] == 5:
#                         users["scraps"] += 5
#                         self.__vk.send(
#                             {
#                                 "id": users["id"],
#                                 "message": f"У вас лузстрик 5. Вы получаете 5 обрывков",
#                             }
#                         )

#                     self.rank.lose(user=users)

#                     self.__db.editDB(users)

#                 data["db"]["balance"] += 1
#                 data["db"]["judge"] += 1
#                 self.__vk.send(
#                     {
#                         "id": data["vk"]["user"],
#                         "message": f"Вы получаете 1 монету за судейство",
#                     }
#                 )
#                 if not data["db"]["judge"] % 10:
#                     data["db"]["balance"] += 10
#                     self.__vk.send(
#                         {
#                             "id": data["vk"]["user"],
#                             "message": f"Вы получаете 10 монету за активное судейство",
#                         }
#                     )
#                 self.__db.editDB(data["db"])

#                 self.localStorage["active"].remove(lobby)

#                 return True

#             def flip(_):
#                 flip = self.__dialogs.getDialog(
#                     data, choice(["firstPlayer", "secondPlayer"])
#                 )
#                 flip["peer_id"] = ",".join(map(str, lobby.getFlattened()))
#                 self.__vk.send(flip)

#             if not payload:
#                 return False
#             func, args = next(iter(payload[0].items()))
#             return locals()[func](args) if func in locals() else None

#         if lobby is None:
#             nest_asyncio.asyncio.run(matchMaking(payload))
#             return

#         elif payload and "game" in payload:
#             return nest_asyncio.asyncio.run(readyPlayer(lobby))

#         elif not gameCommands(lobby):
#             role = ["Игрок 1", "Игрок 2", "Судья"][
#                 lobby.getFlattened().index(data["vk"]["user"])
#             ]
#             self.__vk.send(
#                 {
#                     "peer_id": ",".join(
#                         map(
#                             str,
#                             [
#                                 i for i in lobby.getFlattened()
#                                 if i != data["vk"]["user"]
#                             ],
#                         )
#                     ),
#                     "message": f"{role}:\n{data['vk']['text']}",
#                 },
#                 attachments=data["vk"]["attachments"],
#                 sendSeparately=False,
#             )
