from os.path import dirname, join
from game.rank import rank


class dialog:
    def __init__(self,parent, file = 'dialogs.yaml'):
        from yaml import safe_load

        self.__cards = parent._card
        self.__rank = parent._rank

        with open(
            join(dirname(__file__), "..", "configs", file), "r", encoding="utf-8"
        ) as msg:
            self.__messages = safe_load(msg)

    def getStatus(self):
        return self.__messages["status"]

    def getDialogPlain(self, userid: int|str, *, preset = ['error'], text=None, script = None):
        if not isinstance(preset, list): preset = [preset]
        
        return {
            'id': userid,
            'message': [text] if text else 
            [self.__messages['main'].get(p, 'error').get('message', 'DIALOG_PLACEHOLDER') for p in preset],
            'keyboard': self.__messages['main'].get(preset[-1], script)
        }
        
    def getDialogParsed(self, receiverID: int|str, preset: str|list = ['error'], *, userdata: dict, selectCard: int|slice =-1):
        if not isinstance(preset, list): preset = [preset]

        return {
            "id": receiverID,
            "message": [
                self.__messages['main']
                .get(msg, 'error')
                .get('message', 'DIALOG_PLACEHOLDER')
                .format(
                    card = '\n'.join([
                        card['name'] for card in
                        self.__cards.getOwnedCards(
                            userdata.get("cards", [{'id': -1, 'level':1}]),
                            select = selectCard)
                        ]),
                    status = self.__messages["status"][userdata.get("status", 0)],
                    balance = userdata.get("balance", 0),
                    scraps = userdata.get("scraps", 0),
                    battles = userdata.get("battles", 0),
                    packs = userdata.get("packs", [0,0,0,0]),
                    rank = f'{self.__rank.getStatus(userdata)} ({userdata.get("experience", 0)})',
                ) for msg in preset],
            "keyboard": self.__messages["main"][preset[-1]].get("keyboard"),
        }