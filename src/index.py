from src.module.multi_process import Process
from src.module.read_conf import ReadConf


class Index:

    def __init__(self):
        self.process = Process()
        self.conf = ReadConf()

    def index(self):
        flag = '6'
        if flag == '1':
            from src.paper_website.arxiv.arxivorg import ArxivOrg
            print("获取arxiv论文")
            ArxivOrg().get_exhaustive_url()

        if flag == '2':
            from src.paper_website.arxiv.arxivorg import translate_classification
            print("翻译classification")
            self.process.multi_process(translate_classification)

        if flag == '3':
            from src.paper_website.arxiv.arxivorg import translate_title
            print("翻译title")
            self.process.multi_process(translate_title)

        if flag == '4':
            from src.paper_website.arxiv.arxiv_paper_down import Arxiv_paper_down
            print("下载arxiv论文")
            Arxiv_paper_down().paper_down()

        if flag == '5':
            from src.paper_website.cnki.run_cnki import run_get_paper_title
            print("获取cnki论文基础数据")
            run_get_paper_title()

        if flag == '6':
            from src.paper_website.cnki.run_cnki import run_get_paper_info
            print("获取cnki论文详细数据")
            self.process.multi_process(run_get_paper_info)

        if flag == '7':
            from src.paper_website.cnki.run_cnki import run_multi_title_data
            print("处理CNKI查询标题重复数据")
            self.process.multi_process(run_multi_title_data)

        if flag == '8':
            from src.paper_website.cnki.run_cnki import run_multi_title_info
            print("获取CNKI查询标题重复数据详细内容")
            self.process.multi_process(run_multi_title_info)

        if flag == '9':
            from src.ES.arXiv import create_arxiv_index
            print("向ES添加arxiv数据")
            sql = (f"SELECT * FROM `index` WHERE ES_date is NULL and `from` = 'arxiv' "
                   f"and `state` not in ('00', '01') limit 5000")
            self.process.multi_process_as_up_group(sql, create_arxiv_index)

        if flag == '10':
            from src.ES.cnki import create_cnki_index
            print("向ES添加cnki数据")
            sql = f"SELECT * FROM `index` WHERE `from` = 'cnki' and ES_date is NULL limit 10000"
            self.process.multi_process_as_up_group(sql, create_cnki_index)

        if flag == '11':
            from src.ES.cnki import create_cnki_page_flag
            print("向ES添加CNKI_date_flag数据")
            create_cnki_page_flag()

        if flag == '12':
            from src.paper_website.cnki.run_cnki import run_paper_type_number
            run_paper_type_number()

        if flag == 'a':
            from src.data_processing.index_table_processing import cnki_index_data_processing
            print('数据清洗')
            cnki_index_data_processing()

        # run_get_paper_info()
