from credentials import *
from bs4 import BeautifulSoup

import os
import json
import tweepy
import urllib.request
import time, datetime

URL_NEW_RELEASES = 'https://ridibooks.com/new-releases/general?page=1'
# 포맷 예제 : [일반] 편한식사 (보랏빛소) - 7800원 https://ridibooks.com/v2/Detail?id=2129000044
FORMAT_PRINT_MSG = '[%s] %s (%s) - %s원 https://ridibooks.com/v2/Detail?id=%s'
LENGTH_TITLE_LIMIT = 30

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


def find_title_func(tag):
	return tag.has_attr('class') and tag.has_attr('data-track-params')


def check_new_released_book_info():
	try:
		#print('DEBUG: downloading new releases book html...')
		recv_search_html = urllib.request.urlopen(URL_NEW_RELEASES)
	except IOError:
		print('IOError: html download problem')
	else:
		recv_raw_html = recv_search_html.read()
		decoded_html = recv_raw_html.decode('utf-8')
		soup = BeautifulSoup(decoded_html, 'html.parser')
		results_list = soup.find_all(find_title_func, class_='title_link trackable')
		#tmp_result = json.loads(results_list[0]['data-track-params'])
		#print(tmp_result)

		print('Checking new title... ' + str(datetime.datetime.now()))
		already_tweeted_id_list = [] #['2129000044', '510000575']
		already_file_path = os.path.expanduser('already_tweeted_obj_id.json')
		if os.path.exists(already_file_path):
			with open(already_file_path) as f:
				already_tweeted_id_list = json.load(f)

		for result in results_list:
			result_dict = json.loads(result['data-track-params'])
			obj_id_str = result_dict['obj_id']

			if obj_id_str not in already_tweeted_id_list:
				category_str = result_dict['tags']['category']
				name_str = result_dict['tags']['name']
				if len(name_str) > LENGTH_TITLE_LIMIT:
					name_str = name_str[:LENGTH_TITLE_LIMIT - 3] + '...'
				brand_str = result_dict['tags']['brand']
				price_str = result_dict['tags']['price']
				tweet_str = FORMAT_PRINT_MSG % (category_str, name_str, brand_str, price_str, obj_id_str)

				#tweet info
				try:
					api.update_status(tweet_str)
				except tweepy.TweepError as e:
					print(e.reason)
				else:
					print(tweet_str)
					#add already obj list
					already_tweeted_id_list.append(obj_id_str)

		with open(already_file_path, 'w') as f:
				json.dump(already_tweeted_id_list, f)


if __name__ == '__main__':
	while True:
		check_new_released_book_info()
		time.sleep(60*4)