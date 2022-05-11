#!/usr/bin/env python3

def bot_main():
    import logging
    logging.basicConfig(format='%(levelname)s - %(message)s')
    logs = logging.getLogger(__name__)
    logs.setLevel(logging.INFO)
	
    from backend.vk import VK
    vk = VK('vk.yaml')

    from backend.db import DB
    db = DB('db.yaml')

    from assets.dialog import dialog
    dialogs = dialog("dialogs.yaml")

    from assets.cards import cards
    card = cards('cards.yaml')
    
    from core import core
    coreCtl = core('core.yaml')
    
    from traceback import format_exc

    data = dict()

    try:
        for data in vk.wait():
            if data['user'] < 1: continue


            data = {'vk':data, 'db': db.getDataFromDB(data['user'])}

            if data['db'] is None:
                if data['vk']['peer_id'] != data['vk']['user']: continue

                vk.send(dialogs.getDialog(data,'greeting',card))
                db.addID(data['vk']['user'])
                logs.info(f'NEW USER: {data["vk"]["user"]}')
                continue


            logs.info(f'GET: {data}')

            if coreCtl.core(data,vk,dialogs,card,db,data['vk']['peer_id'] != data['vk']['user']):
                logs.info(f'WRITE TO DB: {data["db"]}')
                db.editDB(data['db'])

    except Exception as e:
        logs.error(f"REASON: {e}, TRACEBACK: {format_exc()}, DATA: {data}. RESTARTING")
        vk.sendToAdmins(f'Directed by:\n{e}\n\nExecutive producer:\n{format_exc()}\nExecutive Producer\n{data}')


if __name__ == '__main__':
    while True:
        bot_main()
