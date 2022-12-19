from datetime import date

import psycopg2
from psycopg2 import extras


class DbPostgres:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __del__(self):
        DbPostgres.__instance = None

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname='',
            user='',
            password='',
            host=''
        )
        self.conn.autocommit = True

    def fetch_one(self, query, arg=None, factory=None, clean=None):
        ''' Получает только одно ЕДИНСТВЕННОЕ значение (не ряд!) из таблицы
        :param query: Запрос
        :param arg: Переменные
        :param factory: dic (возвращает словарь - ключ/значение) или list (возвращает list)
        :param clean: С параметром вернет только значение. Без параметра вернет значение  в кортеже.
        '''
        try:
            cur = self.__connection(factory)
            self.__execute(cur, query, arg)
            return self.__fetch(cur, clean)

        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def fetch_all(self, query, arg=None, factory=None):
        """ Получает множетсвенные данные из таблицы
        :param query: Запрос
        :param arg: Переменные
        :param factory: dict (возвращает словарь - ключ/значение) или list (возвращает list)
        """
        try:
            with self.__connection(factory) as cur:
                self.__execute(cur, query, arg)
                return cur.fetchall()


        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def query_set(self, query, arg, message=None):
        """ Обновляет данные в таблице и возвращает сообщение об успешной операции """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, arg)
            return message

        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def close(self):
        cur = self.conn.cursor()
        cur.close()
        self.conn.close()

    def __connection(self, factory=None):
        # Dic - возвращает словарь - ключ/значение
        if factory == 'dict':
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # List - возвращает list (хотя и называется DictCursor)
        elif factory == 'list':
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Tuple
        else:
            cur = self.conn.cursor()

        return cur

    @staticmethod
    def __execute(cur, query, arg=None):
        # Метод 'execute' всегда возвращает None
        if arg:
            cur.execute(query, arg)
        else:
            cur.execute(query)

    @staticmethod
    def __fetch(cur, clean):
        # Если запрос был выполнен успешно, получим данные с помощью 'fetchone'
        if clean == 'no':
            fetch = cur.fetchone()
        else:
            fetch = cur.fetchone()[0]
        return fetch

    @staticmethod
    def __error(error):
        # В том числе, если в БД данных нет, будет ошибка на этапе fetchone
        print(error)
        return None


class BotFunc(DbPostgres):
    def get_keyboard(self, key):
        return [dict(i) for i in self.fetch_all("SELECT name, button_id "
                                                "FROM button "
                                                "WHERE chapter_id = %s ORDER BY button_id", (str(key),), 'dict')]

    def get_button(self, button):
        return [dict(i) for i in self.fetch_all("SELECT * FROM button WHERE button_id = %s", (button,), 'dict')]

    def check_user(self):
        '''Проверка регистрации пользователя'''
        res = []
        for i in self.fetch_all("SELECT user_id FROM users", factory='list'):
            res.append(*i)
        return res

    def enroll_user(self, user_id, user_name, user_fullname):
        '''Регистрация нового пользователя'''
        self.query_set("INSERT INTO users(user_id, name, user_name) VALUES (%s, %s, %s)",
                       (user_id, user_name, user_fullname))

    def enroll_click(self, user_id, button_name, chapter_id):
        '''Запись клика в БД'''
        return self.query_set("INSERT INTO clicker (user_id, button_name,chapter_id, date)"
                              "VALUES (%s, %s, %s, %s)", (self.fetch_one(
            "SELECT id FROM users WHERE user_id =%s", (user_id,)
        ), button_name, chapter_id, date.today()))

    def button_date(self, date):
        '''Возвращает топ 3 кнопки по дате'''
        return self.fetch_all("SELECT button_name, count(button_name) AS cnt FROM clicker WHERE date = %s"
                              " GROUP BY button_name ORDER BY cnt DESC LIMIT 3", (date,))

    def user_date(self, date):
        '''Возвращает топ 3 пользователя по дате'''
        return self.fetch_all("SELECT  user_name, count(clicker.user_id) AS cnt "
                              "FROM clicker JOIN users ON clicker.user_id = users.id "
                              "WHERE date = %s GROUP BY user_name ORDER BY  cnt DESC LIMIT 3", (date,))

    def button_top(self):
        '''Возвращает топ 3 кнопки по разделу'''
        return [dict(i) for i in self.fetch_all("SELECT * FROM (SELECT name, button_name, count(button_name) as cnt, "
                                                "RANK() over (PARTITION BY chapter_id ORDER BY count(button_name) DESC)"
                                                "FROM clicker JOIN chapter "
                                                "ON chapter_id = chapter.button_id GROUP BY button_name, "
                                                "chapter_id, name) AS foo "
                                                "WHERE rank<4", factory='dict')]

    def user_top(self):
        '''Возвращает тор 3 пользователей по разделу'''
        return [dict(i) for i in self.fetch_all("SELECT * FROM "
                                                "(SELECT chapter.name, users.user_name, count(button_name) AS cnt,"
                                                "RANK() OVER(PARTITION BY chapter_id ORDER BY count(button_name) DESC) "
                                                "FROM clicker LEFT JOIN users ON clicker.user_id=users.id "
                                                "LEFT JOIN chapter ON clicker.chapter_id=chapter.button_id "
                                                "GROUP BY clicker.user_id, clicker.chapter_id, "
                                                "chapter.name,users.user_name "
                                                "ORDER BY name , cnt DESC ) AS foo "
                                                "WHERE RANK<4", factory='dict')]

    def save_message(self, user_id, message):
        return self.query_set('INSERT INTO message (user_id, message) VALUES (%s, %s)', (
            self.fetch_one("SELECT id FROM users WHERE user_id =%s", (user_id,)), message,))


db = BotFunc()
