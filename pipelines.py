# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pandas as pd
class CSVPipeline(object):

    def __init__(self):
        self.file_name="itunes.csv"
        self.data=[]

    def process_item(self, item, spider):
        self.data.append(item)

    def close_spider(self, spider):
        df=pd.DataFrame(self.data)
        df.to_csv(self.file_name,index=False,encoding='utf-8')
