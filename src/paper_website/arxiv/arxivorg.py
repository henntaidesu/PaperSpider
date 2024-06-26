import sys
from datetime import datetime
import requests
import re
import time
from lxml import html
from src.module.read_conf import ReadConf, ArxivYYMM
from bs4 import BeautifulSoup
from src.model.arxiv_org import ArxivOrgPageModel
from src.module.now_time import now_time, year, moon
from src.module.UUID import UUID
from src.module.log import Log, err1, err2
from src.module.translate import translate
from src.module.chatGPT import openAI
from src.module.rabbitMQ import rabbitmq_produce, rabbitmq_consume


class ArxivOrg:

    def __init__(self):
        self.session = requests.Session()
        self.conf = ReadConf()
        self.if_proxy, self.proxies = self.conf.http_proxy()
        if self.if_proxy is True:
            self.session.proxies.update(self.proxies)
        self.subject_list = ArxivOrgPageModel
        self.logger = Log()

    @staticmethod
    def read_yy_mm_new_data():
        conf = ArxivYYMM()
        yy_mm, code = conf.read_arxiv_yy_mm_code()
        code = str(int(code) + 1).zfill(5)
        return yy_mm, code

    @staticmethod
    def write_code(yy_mm, code):
        conf = ArxivYYMM()
        conf.write_arxiv_yy_mm_code(yy_mm, code)

    def write_yy_mm_code(self, yy_mm):
        conf = ArxivYYMM()
        mm = moon()
        if str(mm) == str(yy_mm)[2:]:
            self.logger.write_log(f"已处理完该阶段数据，暂停6小时", 'info')
            time.sleep(21600)
            return True
        else:
            yy, mm = divmod(int(str(yy_mm)) + 1, 100)
            if mm == 13:
                self.logger.write_log(f"已处理完{yy}年{mm}月数据", 'info')
                yy, mm = yy + 1, 1
            conf.write_arxiv_yy_mm_code(f"{yy:02d}{mm:02d}", "00000")
            return False

    @staticmethod
    def TrimString(Str):
        # if '\n' in Str:
        #     Str = Str.replace('\n', ' ')
        # if ' ' in Str:
        #     Str = Str.replace(' ', '')
        # if '/' in Str:
        #     Str = Str.replace('/', ' ')
        if "'" in Str:
            Str = Str.replace("'", "\\'")
        if '"' in Str:
            Str = Str.replace('"', '\\"')
        return Str

    @staticmethod
    def TrSQL(sql):
        sql = sql.replace("None", "NULL").replace("'NULL'", "NULL")
        return sql

    def get_exhaustive_url(self):
        while True:
            classification_en = None
            classification_zh = None
            title_zh = None
            paper_code = None
            DOI = None
            yy_mm, code = self.read_yy_mm_new_data()
            url = f"https://arxiv.org/abs/{yy_mm}.{code}"
            paper_code = f"{yy_mm}.{code}"
            # url = f"https://arxiv.org/abs/{paper_units}/{yy_mm}{code}"
            # paper_code = f"{paper_units}/{yy_mm}{code}"

            self.logger.write_log(f"{yy_mm}.{code} - URL请求成功 ", 'info')
            try:
                response = self.session.get(url)
            except Exception as e:
                if type(e).__name__ == 'SSLError':
                    self.logger.write_log("SSL Error", 'error')
                    time.sleep(3)
                    self.get_exhaustive_url()
                if type(e).__name__ == 'ProxyError':
                    self.logger.write_log("ProxyError", 'error')
                    time.sleep(3)
                    self.get_exhaustive_url()
                if type(e).__name__ == 'ConnectionError':
                    self.logger.write_log("ConnectionError", 'error')
                    time.sleep(3)
                    self.get_exhaustive_url()
                err2(e)

            tree = html.fromstring(response.content)
            soup = BeautifulSoup(response.text, 'html.parser')

            data_flag = tree.xpath('/html/head/title')[0].text if tree.xpath('/html/head/title') else None
            if data_flag is None or "Article not found" in data_flag or 'identifier not recognized' in data_flag:
                flag = self.write_yy_mm_code(yy_mm)
                if flag:
                    self.get_exhaustive_url()
                else:
                    self.logger.write_log(f"   已爬取完{yy_mm}数据   ", 'info')
                    self.get_exhaustive_url()

            title_en = self.TrimString(str(tree.xpath('//*[@id="abs"]/h1/text()')[0])[2:-2])
            authors_list = self.TrimString(
                " , ".join([p.get_text() for p in soup.find('div', class_='authors').find_all('a')]))
            if len(authors_list) > 512:
                authors_list = authors_list[:512]
            introduction = self.TrimString(" , ".join(tree.xpath('//*[@id="abs"]/blockquote/text()')[1:]))
            classification_en = self.TrimString(str(soup.find('td', class_='tablecell subjects').get_text(strip=True)))

            Journal_reference = soup.find('td', class_='tablecell jref')
            if Journal_reference:
                Journal_reference = Journal_reference.text
                Journal_reference = self.TrimString(Journal_reference)

            Comments = soup.find('td', class_='tablecell comments mathjax')
            if Comments:
                Comments = Comments.text
                Comments = self.TrimString(Comments)

            receive_time = soup.find('div', class_='submission-history')
            receive_time = receive_time.get_text(strip=True)

            size = receive_time[receive_time.rfind("(") + 1:][:-4]
            withdrawn = "0"
            if size == "withdr":
                withdrawn = "1"
                size = receive_time[:receive_time.rfind("[")][:-4]
                size = size[size.rfind("(") + 1:]
            if ',' in size:
                size = size.replace(",", "")

            try:
                DOI = (soup.find('td', class_='tablecell doi')).find('a')['href'][16:]
            except:
                try:
                    DOI = (soup.find('td', class_='tablecell arxivdoi')).find('a')['href'][16:]
                except:
                    DOI = None
            version = None

            # aaa = receive_time
            #
            # for i in range(10):
            #     if f"[v{i+1}]" in aaa:
            #         receive_time = receive_time[receive_time.find(f"[v{i+1}]") + 9:]
            #         receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
            #         version = f'{i+1}'

            if "[v10]" in receive_time:
                receive_time = receive_time[receive_time.find("[v10]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '10'

            elif "[v9]" in receive_time:
                receive_time = receive_time[receive_time.find("[v9]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '9'

            elif "[v8]" in receive_time:
                receive_time = receive_time[receive_time.find("[v8]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '8'

            elif "[v7]" in receive_time:
                receive_time = receive_time[receive_time.find("[v7]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '7'

            elif "[v6]" in receive_time:
                receive_time = receive_time[receive_time.find("[v6]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '6'

            elif "[v5]" in receive_time:
                receive_time = receive_time[receive_time.find("[v5]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '5'

            elif "[v4]" in receive_time:
                receive_time = receive_time[receive_time.find("[v4]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '4'

            elif "[v3]" in receive_time:
                receive_time = receive_time[receive_time.find("[v3]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '3'

            elif "[v2]" in receive_time:
                receive_time = receive_time[receive_time.find("[v2]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '2'

            else:
                receive_time = receive_time[receive_time.find("[v1]") + 9:]
                receive_time = datetime.strptime(receive_time[:receive_time.find("UTC") - 1], "%d %b %Y %H:%M:%S")
                version = '1'

            Now_time, uuid = now_time(), UUID()
            sql = (f"INSERT INTO `index`"
                   f"(`UUID`, `web_site_id`, `classification_en`, `classification_zh`, `source_language`, "
                   f"`title_zh`, `title_en`, `update_time`, `insert_time`, `from`, `state`, `authors`, `Introduction`, "
                   f"`receive_time`, `Journal_reference`, `Comments`, `size`, `DOI`, `version`, `withdrawn`)"
                   f" VALUES ('{uuid}', '{paper_code}', '{classification_en}', '{classification_zh}', 'en', "
                   f"'{title_zh}', '{title_en}', NULL, '{Now_time}', 'arxiv', '00', '{authors_list}', '{introduction}',"
                   f"'{receive_time}','{Journal_reference}','{Comments}',{size},'{DOI}','{version}','{withdrawn}');")

            sql = self.TrSQL(sql)
            self.logger.write_log(f"获取成功", 'info')
            rabbitmq_produce('MYSQL_INSERT', sql)
            self.write_code(yy_mm, code)
            self.logger.write_log(f"更新配置文件成功", 'info')
            # self.logger.write_log(f"[EN : {classification_en}] -> [CN : {classification_zh}]")
            # print("sleep 2s")
            # time.sleep(2)


def translate_classification():
    logger = Log()
    tr = translate()

    while True:
        uuid = None
        data = rabbitmq_consume('ARXIV_paper_status_00')
        if data is None:
            logger.write_log("队列无数据", 'warning')
            time.sleep(32600)
            return
        try:
            data = [item.strip() for item in data.split(',')]
            Now_time = now_time()
            uuid = data[0]
            classification_en = data[1]
            # classification_cn = openAI().openai_chat(classification_en)
            classification_cn = tr.GoogleTR(classification_en, 'zh-CN')
            classification_en = ArxivOrg.TrimString(classification_en)
            logger.write_log(f"[EN : {classification_en}] -> [CN : {classification_cn}]", 'info')
            sql = (f"UPDATE `index` SET `classification_zh` = '{classification_cn}' "
                   f" , `state` = '01', `update_time` = '{Now_time}' WHERE `UUID` = '{uuid}';")
            rabbitmq_produce('MYSQL_UPDATE', sql)
        except Exception as e:
            if type(e).__name__ == 'SSLError':
                logger.write_log("SSL Error", 'error')
                time.sleep(3)
            elif type(e).__name__ == 'APIStatusError':
                logger.write_log("APIStatusError", 'error')
                logger.write_log(f"Err Message:,{str(e)}", 'error')
            else:
                err2(e)
            sql = f"UPDATE `index` SET `state` = '00' WHERE `UUID` = '{uuid}';"
            rabbitmq_produce('MYSQL_UPDATE', sql)
        except KeyboardInterrupt:
            sql = f"UPDATE `index` SET `state` = '00' WHERE `UUID` = '{uuid}';"
            rabbitmq_produce('MYSQL_UPDATE', sql)


def translate_title():
    logger = Log()
    tr = translate()
    GPT = openAI()

    while True:
        try:
            data = rabbitmq_consume('ARXIV_paper_status_01')
            if data is None:
                logger.write_log("队列无数据", 'warning')
                time.sleep(32600)
                return
            data = [item.strip() for item in data.split(',')]
            Now_time = now_time()
            uuid = data[0]
            title_en = data[1]
            title_en = f"{title_en}"
            # title_cn = GPT.openai_chat(title_en)
            title_cn = tr.GoogleTR(title_en, 'zh-CN')
            # title_cn = self.tr.baiduTR("en", "zh", title_cn)
            logger.write_log(f"[EN : {title_en}] -> [CN : {title_cn}]", 'info')
            sql = (f"UPDATE `index` SET `title_zh` = '{title_cn}' "
                   f" , `state` = '02', `update_time` = '{Now_time}' WHERE `UUID` = '{uuid}';")
            rabbitmq_produce('MYSQL_UPDATE', sql)

        except Exception as e:
            if type(e).__name__ == 'SSLError':
                logger.write_log("SSL Error", 'error')
                time.sleep(3)
            elif type(e).__name__ == 'APIStatusError':
                logger.write_log("APIStatusError", 'error')
                logger.write_log(f"Err Message:,{str(e)}", 'error')
            else:
                err2(e)
            sql = f"UPDATE `index` SET `state` = '01' WHERE `UUID` = '{uuid}';"
            rabbitmq_produce('MYSQL_UPDATE', sql)
        except KeyboardInterrupt:
            sql = f"UPDATE `index` SET `state` = '01' WHERE `UUID` = '{uuid}';"
            rabbitmq_produce('MYSQL_UPDATE', sql)