from src.module.execution_db import db
import multiprocessing
from src.module.read_conf import read_conf
from src.paper_website.arxivorg import ArxivOrg
from functools import partial


class Process:
    def __init__(self):
        self.database = db()
        self.conf = read_conf()
        self.arxiv = ArxivOrg()

    def split_list(self, input_list, num_parts):
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
        processes = int(self.conf.processes())
        date_base = db()
        flag, work_list = date_base.select_all(sql)
        if len(work_list) == 0:
            print("已完成获取AS UPGroup")
            return False
        chunks = self.split_list(work_list, processes)
        # func_with_args = partial(func, *args)
        pool = multiprocessing.Pool(processes=processes)
        pool.map(func, chunks)
        pool.close()
        pool.join()