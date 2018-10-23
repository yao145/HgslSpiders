from FindNews.settings import mysql_properties


class MysqldbService:
    def __init__(self, mydb, tittle):
        self.mydb = mydb
        self.tittle = tittle

    def insert_item_to_db(self, item):
        # 先插入到ext_table,然后获取contentid
        key_to_value_ext = {}
        key_to_value_ext["title"] = item["title"]
        key_to_value_ext["origin"] = item["acquisition_id"]
        key_to_value_ext["release_date"] = item["isread"]
        key_to_value_ext["is_bold"] = "0"
        key_to_value_ext["need_regenerate"] = "1"
        rowid = self.mydb.insert(mysql_properties["ext_table"], key_to_value_ext)

        # 设置主表中的content_id
        item["content_id"] = rowid
        keys = ["channel_url", "content_url", "title", "description", "acquisition_id", "content_id", "isread"]
        key_to_value = {}
        for key in keys:
            key_to_value[key] = str(item[key])
        key_to_value["isread"] = ""
        self.mydb.insert(mysql_properties["main_table"], key_to_value)
        print("完成一条记录的入库" + self.tittle + "--->" + item["title"])
        return

    def is_exist_in_db(self, content_url):
        records = self.mydb.executeSql(
            "select count(*) from " + mysql_properties["main_table"] + " where content_url='" + content_url + "'")
        count = records[0][0]
        if count == 0:
            return False
        else:
            return True

