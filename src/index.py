from src.paper_website.arxiv.arxivorg import ArxivOrg, translate_classification, translate_title
from src.module.log import Log
from src.module.multi_process import Process
from src.paper_website.arxiv.arxiv_paper_down import Arxiv_paper_down
from src.paper_website.cnki.run_cnki import run_get_paper_title, run_get_paper_info
from src.ES.arXiv import create_arxiv_index
from src.ES.cnki import create_cnki_index
from src.module.read_conf import read_conf
from src.module.Re_table_data import compare_data_index_to_cnki_inf
from src.data_processing.index_table_processing import cnki_index_data_processing
import asyncio
import sys


class Index:

    def __init__(self):
        self.conf = read_conf()
        self.logger = Log()
        self.arxivorg = ArxivOrg()
        self.process = Process()
        self.Arxiv_paper_down = Arxiv_paper_down()

    def index(self):
        flag = '6'
        if flag == '1':
            print("获取arxiv论文")
            self.arxivorg.get_exhaustive_url()

        if flag == '2':
            print("翻译classification")
            while True:
                sql = f"SELECT UUID, classification_en FROM `index` WHERE state = '00'  and `from` = 'arxiv' "
                asyncio.run(self.process.multi_process_as_up_group(sql, translate_classification))

        if flag == '3':
            print("翻译title")
            while True:
                sql = (f" SELECT UUID, title_en FROM `Paper`.`index`"
                       f" WHERE state = '01' and `from` = 'arxiv'"
                       f" ORDER BY receive_time desc limit 10000")
                self.process.multi_process_as_up_group(sql, translate_title)

        if flag == '4':
            print("下载arxiv论文")
            while True:
                sql = (f"SELECT UUIDs, web_site_id, version, withdrawn "
                       f"FROM `Paper`.`index`WHERE state = '02' and classification_zh "
                       f" like '%cs%' ORDER BY receive_time desc limit 10000")
                self.Arxiv_paper_down.paper_down(sql)

        if flag == '5':
            print("获取cnki论文基础数据")
            run_get_paper_title(0, 0, 0, False)

        if flag == '6':
            limit = int(self.conf.processes()) * 10
            print("获取cnki论文详细数据")
            sql = (f"SELECT * FROM `cnki_index` WHERE `start` = '0' AND db_type in ('1', '2', '3') "
                   f"ORDER BY receive_time DESC LIMIT 3000, {limit}")
            self.process.multi_process_as_up_group(sql, run_get_paper_info)

        if flag == '7':
            print("向ES添加数据")
            sql = f"SELECT * FROM `index` WHERE ES_date is NULL and `from` = 'arxiv' and `state` not in ('00', '01') limit 5000"
            # sql = f"SELECT * FROM `index` WHERE `from` = 'cnki' and ES_date is NULL limit 10000"
            self.process.multi_process_as_up_group(sql, create_arxiv_index)

        if flag == 'a':
            print('数据清洗')
            cnki_index_data_processing()

        # run_get_paper_info()
