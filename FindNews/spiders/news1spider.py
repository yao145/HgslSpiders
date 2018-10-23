# -*- coding: utf-8 -*-
import scrapy
import time
import datetime
from FindNews.items import FindNewsItem
from bs4 import BeautifulSoup
# 导入Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
# 数据库相关
from FindNews.dbhelpers.MysqldbHelper import MysqldbHelper
from FindNews.dbhelpers.MysqldbService import MysqldbService
from FindNews.settings import mysql_properties


class News1Spider(scrapy.Spider):
    name = "news1spider"
    tittle = "《黄冈市水利局官网》"
    print("当前爬虫处理的数据源为" + tittle)
    # 初始化数据库相关信息
    mydb = MysqldbHelper(mysql_properties["host"], mysql_properties["username"], mysql_properties["password"],
                         mysql_properties["port"], mysql_properties["database"])
    print("数据库初始化成功，版本信息--->" + str(mydb.getVersion()))
    db_service = MysqldbService(mydb, tittle)

    root_url = "http://slj.hg.gov.cn"
    start_urls = []
    # 水利新闻
    start_urls.append(root_url + "/col/col9764/index.html")
    # 基层水事
    start_urls.append(root_url + "/col/col9765/index.html")
    # 机关动态
    start_urls.append(root_url + "/col/col9766index.html")
    # 媒体关注
    start_urls.append(root_url + "/col/col9767/index.html")

    # 通知公示
    start_urls.append(root_url + "/col/col9773/index.html")
    # 法律
    start_urls.append(root_url + "/col/col9908/index.html")
    # 法规
    start_urls.append(root_url + "/col/col9909/index.html")
    # 地方性法规
    start_urls.append(root_url + "/col/col9910/index.html")
    # 部委规章
    start_urls.append(root_url + "/col/col9911/index.html")
    # 政策性文件
    start_urls.append(root_url + "/col/col9913/index.html")
    # 规划计划
    start_urls.append(root_url + "/col/col9775/index.html")
    # 重大政策及解读
    start_urls.append(root_url + "/col/col9778/index.html")

    def parse(self, response):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            driver.get(response.url)
            time.sleep(3)
            # 设置每页最大显示2
            select_element = Select(driver.find_element_by_class_name('default_pgPerPage'))
            select_element.select_by_index(len(select_element.options) - 1)
            time.sleep(4)
            # 获取总页数---default_pgTotalPage
            total_element = driver.find_element_by_class_name('default_pgTotalPage')
            # 循环点击下一页，获取每一页的页面内容
            pageNum = int(total_element.text)
            print("页面总数量---->" + str(pageNum))
            for i in range(pageNum):
                cur_page = driver.page_source
                # 解析当前页面内容
                soup = BeautifulSoup(cur_page, 'lxml')
                all_li = soup.select(".default_pgContainer li")
                for iii in range(0, len(all_li)):
                    li = all_li[iii]
                    cur_a = li.find("a")
                    cur_span = li.find("span")
                    new_item = FindNewsItem()
                    new_item["channel_url"] = response.url
                    new_item["content_url"] = self.root_url + cur_a["href"].strip()
                    new_item["title"] = cur_a.get_text().strip()
                    new_item["description"] = "SUCCESS"
                    # 根据基地址给出acquisition_id值
                    if response.url.startswith(self.root_url + "/col/col9775/index.html"):
                        new_item["acquisition_id"] = "801"
                    elif response.url.startswith(self.root_url + "/col/col9908/index.html"):
                        new_item["acquisition_id"] = "802"
                    elif response.url.startswith(self.root_url + "/col/col9909/index.html"):
                        new_item["acquisition_id"] = "802"
                    elif response.url.startswith(self.root_url + "/col/col9910/index.html"):
                        new_item["acquisition_id"] = "802"
                    elif response.url.startswith(self.root_url + "/col/col9911/index.html"):
                        new_item["acquisition_id"] = "803"
                    elif response.url.startswith(self.root_url + "/col/col9913/index.html"):
                        new_item["acquisition_id"] = "803"
                    elif response.url.startswith(self.root_url + "/col/col9778/index.html"):
                        new_item["acquisition_id"] = "803"
                    elif response.url.startswith(self.root_url + "/col/col9773/index.html"):
                        new_item["acquisition_id"] = "10"
                    else:
                        new_item["acquisition_id"] = "8"

                    new_item["content_id"] = "暂无"
                    new_item["isread"] = cur_span.get_text().strip()
                    if self.db_service.is_exist_in_db(new_item["content_url"]):
                        # 存在，并且不是第一次启动
                        if mysql_properties["is_first_start"] != "true":
                            # 如果当前页最后一条都存在于数据库，则认为完成了增量更新
                            # 由于部分页面将重要新闻进行了置顶操作，故不能一存在于数据库就认为增量更新完成
                            # 局限性在于：置顶数量超过一整个页面，可能性极小
                            if iii == len(all_li) - 1:
                                print(self.tittle + "完成增量数据更新，最后一条记录--->" + new_item["title"])
                                return
                    else:
                        self.db_service.insert_item_to_db(new_item)
                    # 如果页面总数操作15页，即300条时，只取半年内的数据内容
                    # 页面最后一个判断时间是否超过半年，由于有些信息被强制置顶,则用每一页最后一条作为时间计数点
                    # 如果超过半年则关闭爬虫
                    if pageNum > 15 and iii == len(all_li) - 1:
                        print(self.tittle + "当前记录时间--->" + cur_span.get_text().strip())
                        # 当前新闻的时间--->日期
                        new_date = datetime.datetime.strptime(cur_span.get_text().strip(), "%Y-%m-%d")
                        cur_date = datetime.datetime.now()
                        interval = cur_date - new_date
                        if interval.days > 180:
                            print(self.tittle + "信息内容超过一年，停止爬虫！")
                            return
                # 跳转到下一页面
                print(self.tittle + "模拟浏览器操作，跳到下一页--->" + str(i + 1))
                driver.find_element_by_class_name("default_pgNext").click()
                time.sleep(4)
        except Exception as e:
            print("获取页面信息失败" + self.tittle + "-->" + str(e))
        finally:
            print("关闭打开的模拟浏览器" + self.tittle + "---->" + response.url)
            driver.quit()

    def close(self, reason):
        # 关闭数据库连接
        if self.mydb is not None:
            self.mydb.close()
        return
