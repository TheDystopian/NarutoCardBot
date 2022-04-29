from os.path import dirname,join

class dialog:
    def __init__(self,file):
        from yaml import safe_load

        with open(join(dirname(__file__),file),'r',encoding="utf-8") as msg:
            self.__messages = safe_load(msg)

    def getDialog(self,data,cards,selectCard = -1):
        if data['db'] is None:
            return {'id':data['vk']['user'], 'message': self.__messages['main']['greeting']['message'], 'keyboard':self.__messages['main']['greeting']['keyboard'] }

        dialog = data['vk']['payload']['dialog']

        cardData = cards.getOwnedCards(data['db']['cards'])

        return {'id':data['vk']['user'], 
        "message":[ self.__messages['main'][a]['message'].format(
            card = '\n'.join([i['name'] for i in cardData[selectCard]]) if isinstance(selectCard,slice) else cardData[selectCard]['name'] if data['db']['cards'] != [] else None,
            status = self.__messages['status'][data['db']['status']],
            balance = data['db']['balance'],
            scraps = data['db']['scraps'],
            battles = data['db']['battles']
        ) for a in dialog] , 'keyboard': self.__messages ['main'][dialog[-1]]['keyboard'] if 'keyboard' in self.__messages ['main'][dialog[-1]] else None
        }
