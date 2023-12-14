from src.paper_website.arxivorg import ArxivOrg
from src.module.log import log
import sys


class index:

    def __init__(self):
        self.logger = log()
        self.arxivorg = ArxivOrg()

    def index(self):
        print("1:爬论文")
        print("2:翻译classification")
        print("3:翻译title")
        flag = input()
        if flag == '1':
            self.arxivorg.get_exhaustive_url()

        if flag == '2':
            try:
                while True:
                    self.arxivorg.translate_classification()
            except Exception as e:
                self.logger.write_log(f"Err Message:,{str(e)}")
                self.logger.write_log(f"Err Type:, {type(e).__name__}")
                _, _, tb = sys.exc_info()
                self.logger.write_log(f"Err Local:, file : {tb.tb_frame.f_code.co_filename} , row : {tb.tb_lineno}")

        if flag == '3':
            try:
                while True:
                    self.arxivorg.translate_title()
            except Exception as e:
                self.logger.write_log(f"Err Message:,{str(e)}")
                self.logger.write_log(f"Err Type:, {type(e).__name__}")
                _, _, tb = sys.exc_info()
                self.logger.write_log(f"Err Local:, file : {tb.tb_frame.f_code.co_filename} , row : {tb.tb_lineno}")
