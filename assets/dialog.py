from os.path import dirname,join

class dialog:
    def __init__(self,file):
        from yaml import safe_load

        with open(join(dirname(__file__),file),'r',encoding="utf-8") as msg:
            self.__messages = safe_load(msg)

    def getDialog(self, data, dialog, cards,selectCard = [-1]):
        if data['db'] is None:
            return {'id':data['vk']['user'], 'message': self.__messages['main']['greeting']['message'], 'keyboard':self.__messages['main']['greeting']['keyboard'] }


        cardData = cards.getOwnedCards(data['db']['cards'])

        if not isinstance(dialog,list): dialog = [dialog]

        return {'id':data['vk'].get('user'), 
        "message":[ self.__messages['main'][a]['message'].format(
            card = None if not len(data['db']['cards']) else '\n'.join([cardData[i]['name'] for i in selectCard]),
            status = self.__messages['status'][data['db']['status']],
            balance = data['db']['balance'],
            scraps = data['db']['scraps'],
            battles = data['db']['battles']
        ) for a in dialog], 
        'keyboard': self.__messages ['main'][dialog[-1]].get('keyboard'), 
        'peer_id': data['vk'].get('peer_id')
        }
