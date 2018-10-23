# -*- coding: utf-8 -*-
import scrapy
import time
from FindNews.items import FindNewsItem
from bs4 import BeautifulSoup
# 数据库相关
from FindNews.dbhelpers.MysqldbHelper import MysqldbHelper
from FindNews.dbhelpers.MysqldbService import MysqldbService
from FindNews.settings import mysql_properties


class News3Spider(scrapy.Spider):
    name = "news3spider"
    tittle = "《长江水利网》"
    print("当前爬虫处理的数据源为" + tittle)
    # 初始化数据库相关信息
    mydb = MysqldbHelper(mysql_properties["host"], mysql_properties["username"], mysql_properties["password"],
                         mysql_properties["port"], mysql_properties["database"])
    print("数据库初始化成功，版本信息--->" + str(mydb.getVersion()))
    db_service = MysqldbService(mydb, tittle)

    root_url = "http://www.cjw.gov.cn"
    start_urls = []
    start_urls.append(root_url + "/xwzx/slyw/")
    # 标志位，当前是否为最后一页
    is_not_end_page = True

    def parse(self, response):
        try:
            # 解析当前页面内容
            soup = BeautifulSoup(response.text, 'lxml')
            all_li = soup.select(".txtnews li")
            for i in range(0, len(all_li)):
                li = all_li[i]
                cur_a = li.select(".left a")[0]
                cur_div = li.select(".right")[0]
                new_item = FindNewsItem()
                new_item["channel_url"] = response.url
                new_item["content_url"] = self.root_url + cur_a["href"]
                new_item["title"] = cur_a.get_text().strip()
                new_item["description"] = "SUCCESS"
                new_item["acquisition_id"] = "6"
                new_item["content_id"] = "暂无"
                new_item["isread"] = cur_div.get_text().strip()[1:-1]
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
            # 跳转到下一页面
            all_page_a = soup.select(".pagecss a")
            next_page_url = ""
            end_page_url = ""
            for next_page_a in all_page_a:
                if next_page_a.get_text() == "下一页":
                    next_page_url = self.root_url + next_page_a["href"]
                if next_page_a.get_text() == "尾页":
                    end_page_url = self.root_url + next_page_a["href"]
            # 标志位，控制是否跳转到下一页
            is_forward_next_page = True
            if next_page_url == end_page_url:
                if self.is_not_end_page:
                    self.is_not_end_page = False
                else:
                    is_forward_next_page = False

            if is_forward_next_page:
                request = scrapy.http.Request(next_page_url, callback=self.parse)
                time.sleep(3)
                yield request
            else:
                print(self.tittle + "页面爬取完成！")
                return
        except Exception as e:
            print("获取页面信息失败" + self.tittle + "-->" + str(e))

    def close(self, reason):
        # 关闭数据库连接
        if self.mydb is not None:
            self.mydb.close()
        return
