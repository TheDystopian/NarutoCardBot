#!/usr/bin/env python3
import asyncio
from traceback import format_exc
from multiprocessing import Process


class main:
    def __init__(self):
        from backend.vk import VK
        self._vk = VK("vk.yaml")

        from backend.db import DB
        self._db = DB("db.yaml")

        from assets.cards import cards
        self._card = cards("cards.yaml")

        from game.rank import rank
        self._rank = rank()

        from assets.dialog import dialog
        self._dialogs = dialog(self)

        from core import core
        self._coreCtl = core(self)
        
        
        
        
        
        
        
        
        
        
        

        import logging

        logging.basicConfig(format="%(levelname)s - %(message)s")
        self.logs = logging.getLogger(__name__)
        self.logs.setLevel(logging.INFO)
        self.logs.info("Starting Bot...")

        asyncio.run(self.launch())

    async def launch(self):
        try:
            data = dict()
            
            for data in self._vk.wait():
                self.logs.info(f"GET - {data}")
                self._coreCtl.core(data)

        except Exception as e:
            self.logs.error(f"REASON: {e}, TRACEBACK: {format_exc()}, DATA: {data}")
            self._vk.sendTo(
                f"Directed by:\n{e}\n\nExecutive producer:\n{format_exc()}\nExecutive Producer\n{data}",
                "devs",
            )


if __name__ == "__main__":
    while True:
        try:
            from scheduled import scheduled

            # synchroProc = Process(target=scheduled, name="Timed events")
            # synchroProc.start()

            main()
        except Exception as e:
            print(f"ERROR: {e}\n{format_exc()}")
            
        finally:
            pass
            # synchroProc.join()
