# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FindNewsItem(scrapy.Item):
    channel_url = scrapy.Field()
    content_url = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    acquisition_id = scrapy.Field()
    content_id = scrapy.Field()
    isread = scrapy.Field()
