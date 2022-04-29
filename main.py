def bot_main():
    from backend.vk import VK
    vk = VK('vk.yaml')

    from backend.db import DB
    db = DB('db.yaml')

    from assets.dialog import dialog
    dialogs = dialog("dialogs.yaml")

    from assets.cards import cards
    card = cards('cards.yaml')


    from brain import brains_main_bot,brains_chat_bot

    data = dict()

    try:
        for data in vk.wait():
            data = {'vk':data, 'db': db.getDataFromDB(data['user'])}

            if data['vk']['peer_id'] == data['vk']['user']:
                match brains_main_bot(data,vk, dialogs,card):
                    case None:
                        db.addID(data['vk']['user'])
                    case True:
                        db.editDB(data['db'])

            elif brains_chat_bot(data,vk):
                db.editDB(data['db'])
    except Exception as e:
        vk.sendToAdmins(f'О нет! Я упаль!!!\nКод ошибки:\n{e}\nОбрабатываемые данные в тот момент:\n{data}')
        return e


if __name__ == '__main__':
    import logging
    from cysystemd import journal

    logging.basicConfig(level=logging.ERROR)
    log = logging.getLogger()
    log.addHandler(journal.JournaldLogHandler())

    while True:
        log.exception(f'Oh no! Bot Crashed! Error: {bot_main()}')
