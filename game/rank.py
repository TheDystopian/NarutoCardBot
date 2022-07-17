class rank:
    def __init__(self, *, file='rank.yaml'):
        from yaml import safe_load
        from os.path import join, dirname

        with open(
            join(dirname(__file__), "..", "configs", file), "r", encoding="utf-8"
        ) as fl:
            self.__config = safe_load(fl)

    def lose(self, user):
        user["experience"] -= self.__config["expSettings"]["expAdd"][
            next(
                j["expGroup"]
                for i, j in reversed(self.__config["expSettings"]["expLevels"].items())
                if user["experience"] >= int(i)
            )
        ]["lose"]
        if user["experience"] < 0:
            user["experience"] = 0

    def win(self, user):
        user["experience"] += self.__config["expSettings"]["expAdd"][
            next(
                j["expGroup"]
                for i, j in reversed(self.__config["expSettings"]["expLevels"].items())
                if user["experience"] >= int(i)
            )
        ]["win"]

    def getStatus(self, user):
        if "experience" not in user: return 'INVALID_USER'
        return next(
            j["name"]
            for i, j in reversed(self.__config["expSettings"]["expLevels"].items())
            if user["experience"] >= int(i)
        )

    def rwin(self, user):
        for rank, rankInfo in reversed(
            self.__config["expSettings"]["expLevels"].items()
        ):
            if (
                user["experience"]
                < int(rank)
                - self.__config["expSettings"]["expAdd"][rankInfo["expGroup"]]["win"]
            ):
                continue
            user["experience"] -= self.__config["expSettings"]["expAdd"][
                rankInfo["expGroup"]
            ]["win"]
            return

    def rlose(self, user):
        for rank, rankInfo in reversed(
            self.__config["expSettings"]["expLevels"].items()
        ):
            if (
                user["experience"]
                < int(rank)
                + self.__config["expSettings"]["expAdd"][rankInfo["expGroup"]]["lose"]
            ):
                continue
            user["experience"] += self.__config["expSettings"]["expAdd"][
                rankInfo["expGroup"]
            ]["lose"]
            return
