from yaml import safe_load
from os.path import dirname, join
from itertools import chain
import errors
from game.game import lobbies
from functions import functionData, generalFunctions


class dictRecursive:
    def get(_dict):
        if not isinstance(_dict, dict):
            return _dict
        return dictRecursive.get(next(iter(_dict.values())))

    def set(_dict, val):
        if not isinstance(_dict, dict):
            return val
        return {
            next(iter(_dict.keys())): dictRecursive.set(next(iter(_dict.values())), val)
        }


class core:
    def __init__(self, parent, *, file="core.yaml"):
        with open(
            join(dirname(__file__), "configs", file), "r", encoding="utf-8"
        ) as conf:
            self.__config = safe_load(conf)

        self._vk = parent._vk
        self._db = parent._db
        self._dialogs = parent._dialogs
        self._card = parent._card

        self._game = lobbies(self)
        self._func = functionData(self)

        self.__allCommands = set(
            chain.from_iterable(
                [i["activateOn"] for i in list(self.__config["commands"].values())]
            )
        )
        self.__allSubCommands = set(
            chain.from_iterable(
                [i["activateOn"] for i in list(self.__config["subOptions"].values())]
            )
        )

    def messageState(self, data):
        isChat = data["user"] != data["peer_id"]
        
        lobby = self._game.findLobby(data['user'])
        isAdmin = self._vk.isAdmin(data["peer_id"], data["user"])

        return isChat, isAdmin, lobby

    def textRecognition(self, data, isChat, lobby, isAdmin):
        if len(data["text"]) < 2 or not data["text"][0] in self.__config["commandCall"]:
            return None
        payload = []

        for command in data["text"].upper().split():
            try:
                isCommand = command[0] in self.__config["commandCall"]
                
                if isCommand and command[1:] in self.__allCommands:
                    foundKey = next(
                        (
                            k
                            for k, v in self.__config["commands"].items()
                            if command[1:] in v["activateOn"]
                        )
                    )

                    if (
                        isChat
                        and "chat" not in self.__config["commands"][foundKey]["permittedIn"]
                        or not isChat
                        and "bot" not in self.__config["commands"][foundKey]["permittedIn"]
                        or not isAdmin
                        and "admins" in self.__config["commands"][foundKey]["permittedIn"]
                    ):
                        raise errors.AccessDenied


                    payload.append({foundKey: None})

                elif command in self.__allSubCommands:
                    if not payload:
                        continue
                    payload[-1][list(payload[-1].keys())[-1]] = next(
                        (
                            k
                            for k, v in self.__config["subOptions"].items()
                            if command in v["activateOn"]
                        )
                    )
                else:
                    if not payload:
                        continue
                    if list(payload[-1].values())[-1] is None:
                        payload[-1][list(payload[-1].keys())[-1]] = [command]

                    elif isinstance(list(payload[-1].values())[-1], list):
                        payload[-1][list(payload[-1].keys())[-1]].append(command)

                    elif isinstance(list(payload[-1].values())[-1], dict):
                        payload[-1] = dictRecursive.set(
                            payload[-1],
                            dictRecursive.get(list(payload[-1].values())[-1]) + [command],
                        )

                    else:
                        items = list(payload[-1].items())[-1]
                        payload[-1][items[0]] = {items[1]: [command]}
                        
            except errors.AccessDenied:
                self._vk.send(
                        {
                            "peer_id": data["peer_id"],
                            "message": self.__config["notPermitted"],
                        }
                    )
                continue     
            

        return payload

    def core(self, data):
        def payloadHandle(payload):
            PAYLOADCONVERT = {
                "tutorial": {"dialog": "tutorial"},
                "shop": {"dialog": "shop_inline"},
                "varenik": {"dialog": "varenik"},
                "leha": {"dialog": "leha"},
                "gerych": {"dialog": "gerych"},
                "pack_dialog": {"dialog": "packs_inline"},
                "removeKB": {"dialog": "kb_placeholder"},
            }

            if isinstance(payload, dict):
                payload = [payload]

            for index, func in enumerate(payload):
                if not isinstance(func, dict):
                    continue
                if list(func.keys())[0] in PAYLOADCONVERT.keys():
                    payload[index] = PAYLOADCONVERT[list(func.keys())[0]]

            func = generalFunctions(self._func, data,payload)

            self._db.editDB(data["db"])

        def greeting():
            dataNew = {"vk": data, "db": self._db.getDataFromDB(data["user"])}
            if dataNew["db"] is not None:
                return dataNew

            if data["peer_id"] != data["user"]:
                return False

            self._db.addID(dataNew["vk"]["user"])
            self._vk.send(self._dialogs.getDialogPlain(data['user'], preset = ["greeting"]))
            return False

        payload = data["payload"]
        isChat, isAdmin, lobby = self.messageState(data)

        if payload is None:
            payload = self.textRecognition(data, isChat, lobby, isAdmin)
            if not payload and not lobby:
                return

        data = greeting()
        if not data:
            return

        payloadHandle(payload)
