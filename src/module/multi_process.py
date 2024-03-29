import time
from src.module.execution_db import Date_base
import multiprocessing
from src.module.read_conf import read_conf
from src.module.log import Log
from src.module.log import err2


class Process:
    def __init__(self):
        self.database = Date_base()
        self.conf = read_conf()
        self.logger = Log()

    @staticmethod
    def split_list(input_list, num_parts):
        avg = len(input_list) // num_parts
        remainder = len(input_list) % num_parts
        chunks = []
        current_idx = 0

        for i in range(num_parts):
            chunk_size = avg + 1 if i < remainder else avg
            chunks.append(input_list[current_idx:current_idx + chunk_size])
            current_idx += chunk_size

        return chunks

    def multi_process_as_up_group(self, sql, func):
        try:
            processes = int(self.conf.processes())
            date_base = Date_base()
            flag, work_list = date_base.select(sql)
            if len(work_list) == 0:
                return False
            chunks = self.split_list(work_list, processes)
            # 创建进程池
            pool = multiprocessing.Pool(processes=processes)
            pool.imap_unordered(func, chunks)
            pool.close()
            pool.join()

        except Exception as e:
            err2(e)
