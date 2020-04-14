import sqlite3
#import configparser


class DBConnection:

    def __init__(self):
        #config = configparser.ConfigParser()
        #config.read("dbs/config.cfg")
        #db_name = config["Data"]["filename"]
        db_name = 'C:\\Users\\ittay\\Documents\\Technion repos\\Semester 4\\ComeTogether\\venv\\app\\dbs\\sqlite_db.db'
        self.db = sqlite3.connect(db_name)
        self.cursor = self.db.cursor()