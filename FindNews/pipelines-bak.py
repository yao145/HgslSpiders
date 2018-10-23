# -*- coding: utf-8 -*-
from FindNews.dbhelpers.MysqldbHelper import MysqldbHelper
from FindNews.settings import mysql_properties


class FindnewsPipeline(object):
    temp_values = []
    # 初始化数据库相关信息
    mydb = MysqldbHelper(mysql_properties["host"], mysql_properties["username"], mysql_properties["password"],
                              mysql_properties["port"], mysql_properties["database"])
    print("数据库初始化成功，版本信息--->" + str(mydb.getVersion()))

    def process_item(self, item, spider):
        if item["content_url"] != "0":
            self.temp_values.append(
                [item['channel_url'], item['content_url'], item['title'], item['description'], item['acquisition_id'],
                 item['content_id'], item['isread']])
        # 每20条进行一次批量入库操作
        if len(self.temp_values) == 20:
            self.bulk_insert_to_mysql()
        return item

        # spider结束

    def close_spider(self, spider):
        print("爬虫关闭，最后一点数据进行入库-->" + str(len(self.temp_values)))
        self.bulk_insert_to_mysql()
        # 关闭数据库链接,整个爬虫过程只有一个数据库连接
        # self.mydb.close()

    # 批量插入
    def bulk_insert_to_mysql(self):
        if len(self.temp_values) == 0:
            return
        # 将item数据插入到数据库,jc_acquisition_history
        key = ["channel_url", "content_url", "title", "description", "acquisition_id", "content_id", "isread"]
        self.mydb.insertMany("jc_acquisition_history", key, self.temp_values)
        print("数据库入库成功-->" + str(len(self.temp_values)))
        # 清空缓冲区
        del self.temp_values[:]

