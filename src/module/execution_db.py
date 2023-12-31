import sys
from src.module.log import log
from src.module.read_conf import read_conf
from src.module.err_message import err


class Date_base:

    def __init__(self):
        read_db_conf = read_conf()
        self.db = read_db_conf.database()
        self.print_log = log()

    def insert_all(self, sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            self.db.close()
            return True
        except Exception as e:
            if "index.PRIMARY" in str(e):
                self.print_log.write_log("重复数据 " + sql)
                return '重复数据'
            elif "timed out" in str(e):
                self.print_log.write_log("连接数据库超时")
                sys.exit()
            else:
                err(e)
                self.print_log.write_log(sql)
                return False

    def insert_list(self, sql):
        try:
            cursor = self.db.cursor()
            for i in sql:
                cursor.execute(sql[i])
                self.db.commit()
                cursor.close()
            self.db.close()
            return True
        except Exception as e:
            err(e)
            if "timed out" in str(e):
                self.print_log.write_log("连接数据库超时")
            elif "index.PRIMARY" in str(e):
                self.print_log.write_log("重复数据")
                return True
            else:
                err(e)
                self.print_log.write_log(sql)
                return False

    def update_all(self, sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            cursor.close()
            return True
        except Exception as e:
            err(e)
            if "timed out" in str(e):
                self.print_log.write_log("连接数据库超时")
            self.print_log.write_log(sql)
            return False
        finally:
            if hasattr(self, 'db') and self.db:
                self.db.close()

    def select_all(self, sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            return True, result
        except Exception as e:
            err(e)
            if "timed out" in str(e):
                self.print_log.write_log("连接数据库超时")
            self.print_log.write_log(sql)
        finally:
            if hasattr(self, 'db') and self.db:
                self.db.close()

    def delete_all(self, sql):
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            self.db.close()
            return result
        except Exception as e:
            err(e)
            if "timed out" in str(e):
                self.print_log.write_log("连接数据库超时")
            self.print_log.write_log(sql)
        finally:
            if hasattr(self, 'db') and self.db:
                self.db.close()
