import math
import sqlite3
import time

from flask import url_for


class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def getMenu(self):
        sql = "SELECT * FROM mainmenu"
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения меню", e)
        return []

    def addPost(self, title, text, url):
        try:
            self.__cur.execute(f"SELECT COUNT() AS `count` FROM posts WHERE url like '{url}'")
            res = self.__cur.fetchone()
            if res["count"] > 0:
                print("Статья с таким url уже существует")
                return False

            unix_time = time.time()
            human_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(unix_time))
            self.__cur.execute("INSERT INTO posts VALUES(NULL, ?, ?, ?, ?)", (title, text, url, human_time))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления в БД", e)
            return False
        return True

    def getPost(self, alias):
        try:
            self.__cur.execute(f"SELECT title, text FROM posts WHERE url like '{alias}' LIMIT 1")
            res = self.__cur.fetchone()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения поста из БД", e)

        return False, False

    def getPostsAnonce(self):
        try:
            self.__cur.execute(f"SELECT id, title, text, time, url FROM posts ORDER BY time DESC")
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения поста из БД", e)

        return []

    def addUser(self, name, email, hashed_password):
        try:
            self.__cur.execute(f"SELECT COUNT() as `count` FROM users WHERE email LIKE '{email}'")
            res = self.__cur.fetchone()
            if res["count"] > 0:
                print("Пользователь с такой почтой уже существует")
                return False

            unix_time = time.time()
            human_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(unix_time))
            self.__cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, NULL, ? )",
                               (name, email, hashed_password, human_time))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя", str(e))
            return False

        return True

    def getUser(self, user_id):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE id = {user_id} LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("пользователь не найден")
                return False
            return res
        except sqlite3.Error as e:
            print("Ошибка получения данных из БД", str(e))
        return False

    def getUserByEmail(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email = '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("пользователь не найден")
                return False
            return res
        except sqlite3.Error as e:
            print("Ошибка получения данных из БД", str(e))
        return False

    def updateUserAvatar(self, avatar, user_id):
        if not avatar:
            return False

        try:
            binary = sqlite3.Binary(avatar)
            self.__cur.execute(f"UPDATE users SET avatar = ? WHERE id = ?", (binary, user_id))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка обновления аватара", str(e))
            return False
        return True