def bot_main():
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

    data = dict()

    try:
        for data in vk.wait():
            if data['user'] < 1: continue
            data = {'vk':data, 'db': db.getDataFromDB(data['user'])}

            if data['db'] is None:
                vk.send(dialogs.getDialog(data,'greeting',card))
                db.addID(data['vk']['user'])
                continue

            if coreCtl.core(data,vk,dialogs,card,db,data['vk']['peer_id'] != data['vk']['user']):
                db.editDB(data['db'])

    except Exception as e:
        print(e)
        if e.args[0][:4] != "HTTPS":
            vk.sendToAdmins(f'Directed by:\n{e}\nExecutive producer:\n{data}')


if __name__ == '__main__':
    while True:
        bot_main()
