# mysql
import string

import pymysql
import random


def _gen_verification_code(length=9):
    # 包含所有的字母和数字
    characters = string.ascii_letters + string.digits
    # 随机选择长度为length的字符组成验证码
    verification_code = ''.join(random.choice(characters) for _ in range(length))
    return verification_code


class Database:
    def __init__(self, url=None, port=3306, user='root', password='root', database='caramel'):
        self.url = url
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        if not url:
            self.db = None
            self.cursor = None
            return
        try:
            self.db = pymysql.connect(host=url, port=port, user=user,
                                      password=password, database=database)
        except Exception as e:
            raise e
        self.cursor = self.db.cursor()

    def __del__(self):
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()

    def reconnect(self):
        """重新连接数据库"""
        self.db = pymysql.connect(host=self.url, port=self.port, user=self.user,
                                  password=self.password, database=self.database)
        self.cursor = self.db.cursor()

    def execute(self, sql, args=None, reties=3):
        if not self.cursor:
            self.reconnect()
        for _ in range(reties):
            try:
                self.cursor.execute(sql, args)
                return
            except Exception as e:
                self.reconnect()
                continue
        raise Exception("数据库连接失败，重试次数：{}".format(reties))

    def commit(self):
        self.db.commit()

    def remove_expired_captcha(self):
        self.execute("DELETE FROM participant WHERE expires < NOW()")
        self.commit()

    def gen_captcha(self, user_id: str, already_in_procedure=False):
        # 随机生成9位验证码，使用ASCII码生成只含数字和字母的验证码
        captcha = _gen_verification_code()
        if already_in_procedure:
            # 如果用户已经存在，更新验证码
            self.execute("UPDATE participant SET captcha = %s, expires = NOW() + INTERVAL 5 MINUTE WHERE qid = %s",
                         (captcha, user_id))
        # 将验证码插入数据库
        else:
            self.execute("INSERT INTO participant (qid, captcha, expires) VALUES (%s, %s, NOW() + INTERVAL 20 MINUTE)",
                         (user_id, captcha))
        return captcha

    def rollback(self):
        self.db.rollback()
