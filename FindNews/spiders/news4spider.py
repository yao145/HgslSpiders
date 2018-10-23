# -*- coding: utf-8 -*-
import scrapy
import time
import datetime
from FindNews.items import FindNewsItem
from bs4 import BeautifulSoup
# 导入Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# 数据库相关
from FindNews.dbhelpers.MysqldbHelper import MysqldbHelper
from FindNews.dbhelpers.MysqldbService import MysqldbService
from FindNews.settings import mysql_properties


class News4Spider(scrapy.Spider):
    name = "news4spider"
    tittle = "《湖北省水利厅》"
    print("当前爬虫处理的数据源为" + tittle)
    # 初始化数据库相关信息
    mydb = MysqldbHelper(mysql_properties["host"], mysql_properties["username"], mysql_properties["password"],
                         mysql_properties["port"], mysql_properties["database"])
    print("数据库初始化成功，版本信息--->" + str(mydb.getVersion()))
    db_service = MysqldbService(mydb, tittle)

    root_url = "http://www.hubeiwater.gov.cn/"
    start_urls = []
    start_urls.append(root_url + "news/hotnews/index.shtml")
    start_urls.append(root_url + "news/jcss/index.shtml")
    start_urls.append(root_url + "news/csdt/index.shtml")

    def parse(self, response):
        try:
            # 解析当前页面内容
            soup = BeautifulSoup(response.text, 'lxml')
            all_li = soup.select(".gl_list li")
            for i in range(0, len(all_li)):
                li = all_li[i]
                cur_a = li.find("a")
                cur_span = li.find("span")
                new_item = FindNewsItem()
                new_item["channel_url"] = response.url
                if cur_a["href"].startswith("../../"):
                    new_item["content_url"] = self.root_url + cur_a["href"][6:]
                else:
                    pos = response.url.rfind("/")
                    new_item["content_url"] = response.url[:pos] + cur_a["href"][1:]
                new_item["title"] = cur_a.get_text().strip()
                new_item["description"] = "SUCCESS"
                # 根据基地址给出acquisition_id值
                if response.url.startswith("http://www.hubeiwater.gov.cn/news/jcss"):
                    new_item["acquisition_id"] = "15"
                elif response.url.startswith("http://www.hubeiwater.gov.cn/news/csdt"):
                    new_item["acquisition_id"] = "16"
                else:
                    new_item["acquisition_id"] = "7"
                new_item["content_id"] = "暂无"
                new_item["isread"] = cur_span.get_text().strip()
                if self.db_service.is_exist_in_db(new_item["content_url"]):
                    # 存在，并且不是第一次启动
                    if mysql_properties["is_first_start"] != "true":
                        # 如果当前页最后一条都存在于数据库，则认为完成了增量更新
                        # 由于部分页面将重要新闻进行了置顶操作，故不能一存在于数据库就认为增量更新完成
                        # 局限性在于：置顶数量超过一整个页面，可能性极小
                        if i == len(all_li) - 1:
                            print(self.tittle + "完成增量数据更新，最后一条记录--->" + new_item["title"])
                            return
                else:
                    self.db_service.insert_item_to_db(new_item)
                # 页面最后一个判断时间是否超过半年，由于有些信息被强制置顶
                # 如果超过半年则关闭爬虫
                if i == len(all_li) - 1:
                    print(self.tittle + "当前记录时间--->" + cur_span.get_text().strip())
                    # 当前新闻的时间--->日期
                    new_date = datetime.datetime.strptime(cur_span.get_text().strip(), "%Y-%m-%d")
                    cur_date = datetime.datetime.now()
                    interval = cur_date - new_date
                    if interval.days > 180:
                        print(self.tittle + "信息内容超过一年，停止爬虫！")
                        return

            # 跳转到下一页面---由于是js代码，无法获取分页信息
            # 改用selenium模拟浏览器的方式获取下一页地址
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            driver.get(response.url)
            time.sleep(4)
            cur_page = driver.page_source
            soup2 = BeautifulSoup(cur_page, 'lxml')
            all_page_a = soup2.select(".black2 a")
            for next_page_a in all_page_a:
                if next_page_a.get_text() == ">" and next_page_a["href"] is not None:
                    pos = response.url.rfind("/")
                    next_page_url = response.url[:pos] + "/" + next_page_a["href"]
                    request = scrapy.http.Request(next_page_url, callback=self.parse)
                    time.sleep(4)
                    yield request
        except Exception as e:
            print("获取页面信息失败" + self.tittle + "-->" + str(e))

    def close(self, reason):
        # 关闭数据库连接
        if self.mydb is not None:
            self.mydb.close()
        return
