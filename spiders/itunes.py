# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item
import scrapy
import re
from collections import defaultdict
import os
from scrapy.conf import settings
class ItunesSpider(CrawlSpider):
	name = "itunes"
	allowed_domains = ["itunes.apple.com","www.apple.com"]
	start_urls = ['http://www.apple.com/itunes/charts/songs']

	def parse(self, response):
		self.logger.info("Calling parse")
		self.logger.info('Hi, this is an item page! %s' % response.url)
		for href in response.css("div.section-content > ul>li>h4>a"):
		#href=response.css("div.section-content > ul>li>h4>a")[0]
			singer=href.xpath('text()').extract()[0]
			url=href.xpath('@href').extract()[0]
			self.logger.info("Singer is %s" % singer)
			self.logger.info("URL IS %s" % url)
			requests=scrapy.Request(url,callback=self.parse_song_listings)
			requests.meta["singer"]=singer
			yield requests

		'''
		hxs = HtmlXPathSelector(response)
		item = Item()
		item['id'] = hxs.select('//td[@id="item_id"]/text()').re(r'ID: (\d+)')
		item['name'] = hxs.select('//td[@id="item_name"]/text()').extract()
		item['description'] = hxs.select('//td[@id="item_description"]/text()').extract()
		return item
		'''
	def parse_song_listings(self,response):
		current_pg_no=1
		if "pgno"  in response.meta:
			current_pg_no=int(response.meta['pgno'])	
		self.logger.info("Calling parse_song_listigs for page %d" %current_pg_no)
		song_hrefs=response.css("div.tracklist-content-box > table > tbody > tr >td:first-child+td>span>a")
		pagination=response.css("ul.list.paginate >li>a:not(.selected)")
		singer=response.meta['singer']
		for song_href in song_hrefs:
			song=song_href.xpath('./span/text()').extract()[0]
			url=song_href.xpath('@href').extract()[0]
			self.logger.info("Song is %s" % song)
			self.logger.info("URL IS %s" % url)
			requests=scrapy.Request(url,callback=self.parse_song_page)
			requests.meta['song']=song
			requests.meta['singer']=singer
			yield requests
		#Handle Pagination
		
		self.logger.info("Handling paginaion")
		for pg in pagination:
			page_number=pg.xpath('text()').extract()[0]
			self.logger.info("Extracted page number is %s" %page_number)
			self.logger.info(re.search("/d+",page_number,re.UNICODE))
			if "Next" !=page_number and ("Next" not in page_number):
				self.logger.info(type(page_number))
				self.logger.info("Regex Matched")
				if int(page_number) >current_pg_no:
					self.logger.info("Greater than Current Page Number")
					url=pg.xpath('@href').extract()[0]	
					requests=scrapy.Request(url,callback=self.parse_song_listings)
					requests.meta['pgno']=int(page_number)
					requests.meta['singer']=singer
					yield requests	
			else:
				self.logger.info("Page number %s did not match regex" %page_number)							
	#>td:not(:first-child)
	def parse_song_page(self,response):

			data=defaultdict(str)
			with open(os.path.join(settings.get('HTML_FILE_PATH'),response.meta['singer'] \
					+"_"+response.meta['song']+".html"),'wb') as  html_file:
				html_file.write(response.body)

			self.logger.info("Calling parse_song_page")
			#print "parsing song page for" +response.meta['song']
			
			album_info_div=response.css('div.lockup.product.album.music')[0]
			try:
				album_price_span=album_info_div.css('ul.list >li>span.price')[0]
				album_price=album_price_span.xpath("text()").extract()[0]
				data["Album_Price"]=album_price
			except:	
				data["Album_Price"]=None
				self.logger.info("Error setting album price for song :%s  by singer: %s"\
				 %(response.meta['song'],response.meta['singer']))
			try:	
				genre_elements=album_info_div.css('ul.list >li.genre>a>span')
				genre=",".join([ genre.xpath('text()').extract()[0] for genre in genre_elements])
				data["Genre"]=genre
			except:
				data["Genre"]=None
				self.logger.info("Error setting Genre for song :%s  by singer: %s"\
				 %(response.meta['song'],response.meta['singer']))
			try:
				released_span=album_info_div.css('ul.list >li.release-date>span:not(.label)')[0]
				released=released_span.xpath('text()').extract()[0]
				data["Released"]=released
			except:	
				data["Released"]=None
				self.logger.info("Error setting Date Released for song :%s  by singer: %s"\
				 %(response.meta['song'],response.meta['singer']))
			try:	
				copyright_span=album_info_div.css('ul.list >li.copyright')[0]
				copyright=copyright_span.xpath('text()').extract()[0]
				data["CopyRight"]=copyright
			except:	
				data["CopyRight"]=None
				self.logger.info("Error setting copyright for song :%s  by singer: %s"\
				 %(response.meta['song'],response.meta['singer']))
			customer_rating=response.css("div.rating>span")[0].xpath('text()').extract()[0]
			data["Customer_Rating"]=customer_rating
			try:
				album_name=response.css("div#title>div.left>h1")[0].xpath('text()').extract()[0]
				data["Album_Name"]=album_name
			except:
				data["Album_Name"]=None
				self.logger.info("Error setting Album Name for song :%s  by singer: %s"\
				 %(response.meta['song'],response.meta['singer']))
			song_rows=response.css("div.track-list.album.music>div.tracklist-content-box>table>tbody>tr")
			for row in song_rows:
					try:
						name_element=row.css("td.name>span>span.text")[0]
						data["Song_Name"]=name_element.xpath('text()').extract()[0]
					except:	
						data["Song_Name"]=None
						self.logger.info("Error setting song name for song :%s  by singer: %s"\
				 %(response.meta['song'],response.meta['singer']))
					try:	
						artist_element=row.css("td.artist>a>span.text")[0]
						data["Artist_Name"]=artist_element.xpath('text()').extract()[0]
					except:
						data["Artist_Name"]=singer
						self.logger.info("Error setting Artist Name for song :%s  by singer: %s"\
				 		%(response.meta['song'],response.meta['singer']))
					try:	
						time_element=row.css("td.time>span>span.text")[0]	
						data["Time"]=time_element.xpath('text()').extract()[0]

					except:
						data["Time"]=None	
						self.logger.info("Error setting time for song :%s  by singer: %s"\
				 		%(response.meta['song'],response.meta['singer']))
					
					try:
						price_element=row.css("td.price>span>span")[0]	
						data["Price"]=price_element.xpath('text()').extract()[0]
					except:	
						try:
							price_element=row.css("td.price>span")[0]	
							data["Price"]=price_element.xpath('text()').extract()[0]
						except:
							data['Price']=None
							self.logger.info("Error setting Price for song :%s  by singer: %s"\
				 				%(response.meta['song'],response.meta['singer']))	
			return data			

