# coding=utf8

import requests, json, db, sys
from typing import Any, Dict, Iterator
from bs4 import BeautifulSoup

names_dict = {
	'sum41': ' Sum 41',
	'deryckwhibley': 'Дерик',
	'dave_brownsound': 'Дэйв',
	'dummyado': 'Том',
	'officialconemccaslin': 'Коун',
} 

def create_session():
	"""Return default anonymous requests.Session object."""
	global inst_session
	inst_session = requests.Session()
	return inst_session


def shortcode() -> str:
	"""Post shortcode: part of the URL of the post is instagram.com/p/<shortcode>/."""
	return node['shortcode'] if 'shortcode' in node else node['code']


def parse_page(url: str, page_type: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
	"""Scrap an Instagram page

	:param url: URL, relative to www.instagram.com/
	:param page_type: name of JSON element to parse (PostPage, ProfilePage)
	:param params: GET parameters
	:return: Decoded response dictionary
	"""
	try:
		resp = inst_session.get('https://www.instagram.com/' + url, params=params)
		resp.raise_for_status()
	except requests.HTTPError:
		raise requests.HTTPError('Received non 200 status code from Instagram')
	except requests.RequestException:
		raise requests.RequestException
	else:
		soup = BeautifulSoup(resp.text, 'html.parser')
		body = soup.find('body')
		script_tag = body.find('script')
		raw_string = script_tag.text.strip().replace('window._sharedData =', '').replace(';', '')
		data = json.loads(raw_string)['entry_data'][page_type][0]
		return data


def get_profile_metadata(profile_name: str) -> Dict[str, Any]:
	"""
	Parse the profile webpage and find JSON with the page data
	"""
	return parse_page('{}/'.format(profile_name), 'ProfilePage')['graphql']["user"]


def get_post_metadata(shortcode: str) -> Dict[str, Any]:
	"""
	Parse the post webpage and find JSON with the page data
	"""
	return parse_page("p/{0}/".format(shortcode), 'PostPage')["graphql"]["shortcode_media"]


def get_new_posts(log_key: str, username: str):
	"""
	Get the last posts, return new posts if they exist
	"""
	profile_metadata = get_profile_metadata(username)
	
	# Compare posts amount in the DB log
	current_count = profile_metadata["edge_owner_to_timeline_media"]["count"]
	try:
		prev_count = db.read_logging_table('instagram_'+log_key)
		if prev_count is None:
			db.upsert_logging_table("instagram_{}".format(log_key), str(current_count))
			new_posts = 0
		else:
			new_posts = current_count - int(prev_count[1])
	except TypeError as e:
		print('Cannot read DB value, check if values are correct:', e)
		sys.exit()

	posts = []
	if new_posts:
		for idx, node in enumerate(profile_metadata['edge_owner_to_timeline_media']['edges']):
			if idx < new_posts: # if idx == 10:
				posts.append(get_post(inst_session, node['node']))
	if new_posts > 1:
		posts = list(reversed(posts))

	return posts


def get_post(post_data: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Download everything associated with an instagram post, i.e. picture, caption and video.

	:param post_data: Post to process.
	:return: post object with extracted information
	"""

	post = {}
	post['data'] = {}
	post['data']['author'] = names_dict[post_data['owner']['username']]
	post['data']['id'] = post_data['shortcode']
	post['data']['url'] = 'https://instagram.com/p/'+post_data['shortcode']
	post['data']['caption'] = post_data['edge_media_to_caption']['edges'][0]['node']['text']
	post['data']['date'] = post_data['taken_at_timestamp']
	post['data']['media'] = []

	# Get images and video urls
	if post_data['__typename'] == 'GraphVideo':
		post['type'] = 'video'
		sub_post_data = get_post_metadata(post_data['shortcode'])
		post['data']['media'].append({'type': 'video', 'url': sub_post_data['video_url']})
  
	elif post_data['__typename'] == 'GraphSidecar':
		post['type'] = 'multi'
		sub_post_data = get_post_metadata(post_data['shortcode'])['edge_sidecar_to_children']['edges']
		for sub_post in sub_post_data:
			if sub_post['node']['is_video']:
				post['data']['media'].append({'type': 'video', 'url': sub_post['node']['video_url']})
			else:
				post['data']['media'].append({'type': 'image', 'url': sub_post['node']['display_url']})

	else:
		# GraphImage
		post['type'] = 'image'
		post['data']['media'].append({'type': 'image', 'url': post_data['display_url']})

	return post


def check_instagram():
	create_session()

	new_posts = {
		'Sum_41': get_new_posts('Sum_41', 'sum41'),
		'Deryck': get_new_posts('Deryck', 'deryckwhibley'),
		'Dave': get_new_posts('Dave', 'dave_brownsound'),
		'Tom': get_new_posts('Tom', 'dummyado'),
		'Cone': get_new_posts('Cone', 'officialconemccaslin'),
		'Frank': get_new_posts('Frank', 'frankzummo'),
		# 'TNS': get_new_posts('TNS', 'sum41_tns')
	}

	new_count = 0
	for account in new_posts:
		new_count_account = len(new_posts[account])
		new_count += new_count_account
		if new_count_account:
			print('Found {} new {} post{} in Instagram'.format(new_count_account, account, new_count>1 and 's' or ''))

	return new_count, new_posts
