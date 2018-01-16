from credentials import *
from config import *

from bs4 import BeautifulSoup

import re
import os
import json
import hashlib
import tweepy
import urllib.request
import time, datetime

#format string
FORMAT_URL_NEW_RELEASES = 'https://ridibooks.com/new-releases/%s?page=%s?%s'
FORMAT_URL_EVENT = 'https://ridibooks.com/event/%s?page=%s?%s'
FORMAT_URL_BOOK_RENEWAL = 'https://ridibooks.com/support/notice/512?%s'

#get json path
already_book_json_path = os.path.expanduser('already_tweeted_book_id.json')
already_event_json_path = os.path.expanduser('already_tweeted_event_id.json')
already_renewal_book_json_path = os.path.expanduser('renewal_book_hash.json')

#tweepy auth
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


def get_new_event_info(genre, page=1):
	results_list = []
	timestamp = str(int(time.time()))
	target_url = FORMAT_URL_EVENT % (genre, str(page), timestamp)
	
	try:
		#print('DEBUG: downloading new releases book html... ' +  target_url)
		recv_search_html = urllib.request.urlopen(target_url)
	except IOError:
		print('IOError: html download problem : ' + target_url)
	else:
		event_id_regex = re.compile('\/event\/(\d{1,})')
		recv_raw_html = recv_search_html.read()
		decoded_html = recv_raw_html.decode('utf-8')
		soup = BeautifulSoup(decoded_html, 'html.parser')
		raw_results_list = soup.find_all("h3", class_='event_title')
		for raw_result in raw_results_list:
			#raw_result example : <h3 class="event_title"><a href="/event/6884">데이터를 이익으로 바꾸다! 《통계의 힘》 세트특가</a></h3>
			#print(raw_result)
			tmp_event_url = raw_result.a['href']
			if event_id_regex.match(tmp_event_url) is None:
				continue

			event_id = int(event_id_regex.findall(raw_result.a['href'])[0])
			event_title = raw_result.string
			event_url = 'https://ridibooks.com/event/' + str(event_id)

			result_dict = {'event_id':event_id, 'event_title':event_title, 'event_url':event_url}
			results_list.append(result_dict)
			#print(result_dict)

	return results_list
	

def check_new_released_book_info(skip_tweet=False):
	all_results_list = []
	all_results_list.extend(get_new_released_book_info('general', 1))
	all_results_list.extend(get_new_released_book_info('general', 2))
	all_results_list.extend(get_new_released_book_info('comic', 1))	
	all_results_list.extend(get_new_released_book_info('comic', 2))
	#all_results_list.extend(get_new_released_book_info('fantasy', 1))
	#all_results_list.extend(get_new_released_book_info('fantasy', 2))
	#print(all_results_list)

	print('Checking new title... ' + str(datetime.datetime.now()))
	if len(all_results_list) > 0:
		already_tweeted_id_list = [] #['2129000044', '510000575']

		if os.path.exists(already_book_json_path):
			with open(already_book_json_path) as f:
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
				tweet_str = FORMAT_PRINT_BOOK_MSG % (category_str, name_str, brand_str, price_str, obj_id_str)

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

		with open(already_book_json_path, 'w') as f:
			print('Dumping already tweeted titles...')
			json.dump(already_tweeted_id_list, f)
	else:
		print('ERROR: Not found new released titles list')


def check_new_released_event_info(skip_tweet=False):
	all_results_list = []
	all_results_list.extend(get_new_event_info('general', 1))
	all_results_list.extend(get_new_event_info('general', 2))
	all_results_list.extend(get_new_event_info('comic', 1))	
	all_results_list.extend(get_new_event_info('comic', 2))
	all_results_list.extend(get_new_event_info('fantasy', 1))
	all_results_list.extend(get_new_event_info('fantasy', 2))
	all_results_list.extend(get_new_event_info('romance', 1))
	all_results_list.extend(get_new_event_info('romance', 2))
	all_results_list.extend(get_new_event_info('bl', 1))
	all_results_list.extend(get_new_event_info('bl', 2))
	#print(all_results_list)

	print('Checking new event... ' + str(datetime.datetime.now()))
	if len(all_results_list) > 0:
		already_tweeted_id_list = [] #[6346, 6534]

		if os.path.exists(already_event_json_path):
			with open(already_event_json_path) as f:
				already_tweeted_id_list = json.load(f)

		for result_dict in all_results_list:
			event_id = result_dict['event_id']
			if event_id not in already_tweeted_id_list:
				name_str = result_dict['event_title']
				if len(name_str) > LENGTH_TITLE_LIMIT:
					name_str = name_str[:LENGTH_TITLE_LIMIT - 3] + '...'
				url_str = result_dict['event_url']
				tweet_str = FORMAT_PRINT_EVENT_MSG % (name_str, url_str)

				if skip_tweet is True:
					print(tweet_str)
					already_tweeted_id_list.append(event_id)
				else:
					#tweet info
					try:
						api.update_status(tweet_str)
					except tweepy.TweepError as e:
						print(e.reason)
					else:
						print(tweet_str)
						#add already obj list
						already_tweeted_id_list.append(event_id)
						#sleep code for protect the spam block
						time.sleep(TIME_TWEET_UPDATE_SECOND)

		with open(already_event_json_path, 'w') as f:
			print('Dumping already tweeted event id list...')
			json.dump(already_tweeted_id_list, f)
	else:
		print('ERROR: Not found new released event list')

def check_renewal_book_info(skip_tweet=False):
	timestamp = str(int(time.time()))
	target_url = FORMAT_URL_BOOK_RENEWAL % (timestamp)
	
	print('Checking new renewal book... ' + str(datetime.datetime.now()))
	try:
		recv_search_html = urllib.request.urlopen(target_url)
	except IOError:
		print('IOError: html download problem : ' + target_url)
	else:
		renewal_info_regex = re.compile('<strong>(.*\/.*\/.*\/.*\n●.*)<br')
		recv_raw_html = recv_search_html.read()
		decoded_html = recv_raw_html.decode('utf-8')

		already_tweeted_hash_list = []
		if os.path.exists(already_renewal_book_json_path):
			with open(already_renewal_book_json_path) as f:
				already_tweeted_hash_list = json.load(f)

		for raw_result in re.findall(renewal_info_regex, decoded_html):
			result_str = re.sub(r'<\/strong>\s?<br \/>', r'', raw_result)
			result_hash = hashlib.md5(result_str.encode())
			result_hash_hex = result_hash.hexdigest()
			#DEBUG PRINT
			#print('MD5 : ' + result_hash_hex)
			#print('--------------------------------------------')
			if result_hash_hex not in already_tweeted_hash_list:
				if len(result_str) > LENGTH_TWEET_LIMIT - len(HASHTAG_BOOK_RENEWAL):
					result_str = result_str[:LENGTH_TWEET_LIMIT - (3 + len(HASHTAG_BOOK_RENEWAL))] + '...'
				tweet_str = '%s %s' % (result_str, HASHTAG_BOOK_RENEWAL)
				
				if skip_tweet is True:
					print(tweet_str)
					already_tweeted_hash_list.append(result_hash_hex)
				else:
					#tweet info
					try:
						api.update_status(tweet_str)
					except tweepy.TweepError as e:
						print(e.reason)
					else:
						print(tweet_str)
						#add already obj list
						already_tweeted_hash_list.append(result_hash_hex)
						#sleep code for protect the spam block
						time.sleep(TIME_TWEET_UPDATE_SECOND)

		with open(already_renewal_book_json_path, 'w') as f:
			print('Dumping already tweeted renewal hash list...')
			json.dump(already_tweeted_hash_list, f)


if __name__ == '__main__':
	print('Initializing...')
	#print(results_list)
	if os.path.exists(already_book_json_path):
		os.remove(already_book_json_path)
	if os.path.exists(already_event_json_path):
		os.remove(already_event_json_path)
	if os.path.exists(already_renewal_book_json_path):
		os.remove(already_renewal_book_json_path)

	check_new_released_book_info(skip_tweet=True)
	check_new_released_event_info(skip_tweet=True)
	check_renewal_book_info(skip_tweet=True)

	while True:
		check_new_released_book_info()
		check_new_released_event_info()
		check_renewal_book_info()

		print('COMPLETE! - ' + str(datetime.datetime.now()))
		time.sleep(60*TIME_REFRESH_MINUTE)