import sqlite3
import configparser


class DBConnection:

    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read("dbs/config.cfg")
        db_name = config.get("Data", "filename")
        self.db = sqlite3.connect(db_name)
        self.db.set_character_set('utf8')
        self.cursor = self.db.cursor()