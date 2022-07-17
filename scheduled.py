from backend.db import DB
from backend.vk import VK
import schedule, time, logging
from os.path import join, dirname
from yaml import safe_load

DAILY_RESET = "12:00:00"
WEEKLY_RESET = 2


class scheduled:
    def event1(self):
        self.log.info("Daily event triggered")
        
        
        
        
        
        
        with open(
            join(dirname(__file__), "configs", file), "r", encoding="utf-8"
        ) as conf:
            self.__dailyData = safe_load(conf)

        for dbRow in self.DB.getAllDB():
            dbRow["battles"] = self.__dailyData["userLevels"][dbRow["status"]][
                "battles"
            ]
            dbRow["loses"] = dbRow["wins"] = dbRow["judge"] = 0

            if dbRow["status"] and dbRow["day"] - time() // 86400 == 1:
                self.VK.send(
                    {
                        "message": f'Ваш статус {self.__dialogs.getStatus()[dbRow["status"]]} заканчивается. Для пополнения напишите в администрацию',
                        "id": dbRow["id"],
                    }
                )
            if dbRow["status"] and dbRow["day"] - time() // 86400 <= 0:
                self.VK.send(
                    {
                        "message": f'Ваш статус {self.__dialogs.getStatus()[dbRow["status"]]} истек. Для пополнения напишите в администрацию',
                        "id": dbRow["id"],
                    }
                )
                dbRow["status"] = 0

            self.DB.editDB(dbRow)

    def event2(self):
        self.log.info("2 week event triggered")
        with open(
            join(dirname(__file__), "configs", file), "r", encoding="utf-8"
        ) as conf:
            self.__rankData = safe_load(conf)

        def giveRewards(user, whatToGive):
            def balance(amount):
                user["balance"] += amount

            def scraps(amount):
                user["scraps"] += amount

            def cardPack(packs):
                for pack in packs:
                    user["packs"][pack] += 1

            def card(cardData):
                user["cards"].append(
                    self.__cards.getCardByRarity(
                        chances={str(cardData.get("rarity", 1)): 100},
                        level=cardData.get("level", 1),
                    )
                )

            # This will allow to call functions above
            for i in whatToGive:
                for j, k in i.items():
                    locals()[j](k)
            return user

        for user in db.getAllDB():
            levels = {
                int(level): levelInfo
                for level, levelInfo in self.__rankData["expSettings"][
                    "expLevels"
                ].items()
                if int(level) <= user["experience"]
            }

            user = giveRewards(user, [i["reward"] for i in levels.values()])
            user["experience"] = (
                list(levels.keys())[-2] if len(levels.keys()) >= 2 else 0
            )

            db.editDB(user)

    def __init__(self):
        self.DB = DB()
        self.VK = VK()

        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)

        self.log.info("Starting scheduleing service...")

        schedule.every().day.at(DAILY_RESET).do(self.event1)
        schedule.every(WEEKLY_RESET).weeks.do(self.event2)

        while True:
            schedule.run_pending()
            time.sleep(1)
