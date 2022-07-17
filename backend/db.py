from weakref import finalize
from shutil import rmtree
import psycopg, yaml
from psycopg2 import DatabaseError
from os.path import dirname, join


class DB:
    def __init__(self, cfg="db.yaml"):
        """
        This program uses PostgreSQL
        """
        with open(
            join(dirname(__file__), "..", "configs", cfg), "r", encoding="utf-8"
        ) as conf:
            config = yaml.safe_load(conf)

        self.__DB = psycopg.connect(
            dbname=config["dbname"],
            user=config["user"],
            password=config["passwd"],
            host=config["host"],
            port=config["port"],
        )
        self.__DB.autocommit = True
        self.__DBCursor = self.__DB.cursor()
        self.__DBCursor.execute("select * from userdata LIMIT 0")
        self.__DBColumns = [row[0] for row in self.__DBCursor.description]
        self.__final = finalize(self, rmtree, self.__DBCursor, self.__DB)
        

    def __composeDictionary(self, keys, data):
        return dict(zip(keys, data)) if data is not None else None

    def addID(self, userid: int):
        self.__DBCursor.execute(f"INSERT INTO userdata (id) VALUES ({userid})")

    def getDataFromDB(self, user):
        try:
            return self.__composeDictionary(
                self.__DBColumns,
                self.__DBCursor.execute(
                    f"SELECT {','.join(self.__DBColumns)} from userdata WHERE id = {user}"
                ).fetchone(),
            )
        except DatabaseError:
            self.__DB.rollback()

    def editDB(self, newData):
        self.__DBCursor.execute(
            f"UPDATE userdata set { ' ,'.join([f'{key} = {conv(val)}' for key, val in newData.items()]) } where ID = {newData['id']};"
        )

    def getAllDB(self):
        return [
            self.__composeDictionary(self.__DBColumns, i)
            for i in self.__DBCursor.execute("SELECT * FROM userdata").fetchall()
        ]

    def __exit__(self):
        self.__DBCursor.close()
        self.__DB.close()


def conv(that):
    if isinstance(that, int):
        return str(that)
    if isinstance(that, list):
        if not that or isinstance(that[0], dict):
            return f"'{str(that).replace(chr(39),chr(34))}'"
        return f"'{{ {' ,'.join(map(str,that))} }}'"
    return f"'{that}'"
