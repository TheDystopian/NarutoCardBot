from cmath import isinf
import psycopg,yaml
from os.path import dirname,join

class DB:
    def __init__(self,cfg):
        '''
        This program uses PostgreSQL
        '''
        with open(join(dirname(__file__),cfg),"r",encoding= "utf-8") as conf:
            config = yaml.safe_load(conf)

        self.__DB = psycopg.connect(
            dbname=config["dbname"],
            user=config["user"],
            password=config["passwd"],
            host=config["host"],
            port=config["port"]
        )
        self.__DBCursor=self.__DB.cursor()
        self.__DBCursor.execute("select * from userdata LIMIT 0")
        self.__DBColumns=[row[0] for row in self.__DBCursor.description]


    def __composeDictionary(self,keys,data):
        return dict(zip(keys,data)) if data is not None else None

    def addID(self,user):
        self.__DBCursor.execute(f"INSERT INTO userdata (id) VALUES ({user})")
        self.__DB.commit()

    def getDataFromDB(self, user):
        return self.__composeDictionary(self.__DBColumns, self.__DBCursor.execute(f"SELECT {','.join(self.__DBColumns)} from userdata WHERE id = {user}").fetchone())



    def editDB(self,newData):
        self.__DBCursor.execute(f"UPDATE userdata set { ' ,'.join([f'{key} = {conv(val)}' for key, val in newData.items()]) } where ID = {newData['id']};")
        self.__DB.commit()

    def __del__(self):
        self.__DBCursor.close()
        self.__DB.close()


def conv(that):
    if isinstance(that, int): return str(that)
    if isinstance(that, list):
        if not that or isinstance(that[0],dict):
            return f"'{str(that).replace(chr(39),chr(34))}'"
        return f"'{{ {' ,'.join(map(str,that))} }}'"
    return f"'{that}'"

