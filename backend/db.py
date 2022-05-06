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
        self.__DBColumns=[row[0] for row in self.__DBCursor.execute("select column_name from information_schema.columns where table_name = 'userdata'")]


    def __composeDictionary(self,keys,data):
        return dict(zip(keys,data)) if data is not None else None

    def addID(self,user):
        self.__DBCursor.execute(f"INSERT INTO userdata (id) VALUES ({user})")
        self.__DB.commit()

    def getDataFromDB(self, user):
        return self.__composeDictionary(self.__DBColumns, self.__DBCursor.execute(f"SELECT {','.join(self.__DBColumns)} from userdata WHERE id = {user}").fetchone())

    def editDB(self,newData):
        self.__DBCursor.execute(f"UPDATE userdata set { ' ,'.join([f'{key} = { val if isinstance(val,int) else chr(39) + str(val).replace(chr(39),chr(34)) + chr(39)}' for key, val in newData.items()]) } where ID = {newData['id']};")
        self.__DB.commit()

    def __del__(self):
        self.__DBCursor.close()
        self.__DB.close()
