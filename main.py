from credentials import *
from config import *

from bs4 import BeautifulSoup

import os
import json
import tweepy
import urllib.request
import time, datetime

FORMAT_URL_NEW_RELEASES = 'https://ridibooks.com/new-releases/%s?page=%s?%s'
FILENAME_ALREADY_ADDED_JSON = 'already_tweeted_obj_id.json'

already_file_path = os.path.expanduser(FILENAME_ALREADY_ADDED_JSON)
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


def find_title_func(tag):
	return tag.has_attr('class') and tag.has_attr('data-track-params')


def get_new_released_book_info(genre, page=1):
	results_list = []
	timestamp = str(int(time.time()))
	target_url = FORMAT_URL_NEW_RELEASES % (genre, str(page), timestamp)
	
	try:
		#print('DEBUG: downloading new releases book html... ' +  target_url)
		recv_search_html = urllib.request.urlopen(target_url)
	except IOError:
		print('IOError: html download problem : ' + target_url)
	else:
		recv_raw_html = recv_search_html.read()
		decoded_html = recv_raw_html.decode('utf-8')
		soup = BeautifulSoup(decoded_html, 'html.parser')
		raw_results_list = soup.find_all(find_title_func, class_='title_link trackable')
		for raw_result in raw_results_list:
			result_dict = json.loads(raw_result['data-track-params'])
			results_list.append(result_dict)
			#print(result_dict)

	return results_list
	

def check_new_released_book_info(skip_tweet=False):
	all_results_list = []
	all_results_list.extend(get_new_released_book_info('general', 1))
	all_results_list.extend(get_new_released_book_info('general', 2))
	all_results_list.extend(get_new_released_book_info('comic', 1))
	all_results_list.extend(get_new_released_book_info('comic', 2))
	all_results_list.extend(get_new_released_book_info('fantasy', 1))
	all_results_list.extend(get_new_released_book_info('fantasy', 2))
	#print(all_results_list)

	print('Checking new title... ' + str(datetime.datetime.now()))
	if len(all_results_list) > 0:
		already_tweeted_id_list = [] #['2129000044', '510000575']

		if os.path.exists(already_file_path):
			with open(already_file_path) as f:
				already_tweeted_id_list = json.load(f)

		for result_dict in all_results_list:
			obj_id_str = result_dict['obj_id']
			if obj_id_str not in already_tweeted_id_list:
				category_str = result_dict['tags']['category']
				name_str = result_dict['tags']['name']
				if len(name_str) > LENGTH_TITLE_LIMIT:
					name_str = name_str[:LENGTH_TITLE_LIMIT - 3] + '...'
				brand_str = result_dict['tags']['brand']
				price_str = result_dict['tags']['price']
				tweet_str = FORMAT_PRINT_MSG % (category_str, name_str, brand_str, price_str, obj_id_str)

				if skip_tweet is True:
					print(tweet_str)
					already_tweeted_id_list.append(obj_id_str)
				else:
					#tweet info
					try:
						api.update_status(tweet_str)
					except tweepy.TweepError as e:
						print(e.reason)
					else:
						print(tweet_str)
						#add already obj list
						already_tweeted_id_list.append(obj_id_str)
						#sleep code for protect the spam block
						time.sleep(TIME_TWEET_UPDATE_SECOND)
			else:
				already_tweeted_id_list.append(obj_id_str)

		with open(already_file_path, 'w') as f:
			print('Dumping already tweeted titles...')
			json.dump(already_tweeted_id_list, f)
	else:
		print('ERROR: Not found new released titles list')
	print('COMPLETE! - ' + str(datetime.datetime.now()))


if __name__ == '__main__':
	print('Initializing...')
	check_new_released_book_info(True)

	while True:
		check_new_released_book_info()
		time.sleep(60*TIME_REFRESH_MINUTE)