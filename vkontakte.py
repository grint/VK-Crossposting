#coding=utf8

import sys, requests, json, vk, os
from urllib.request import urlopen
from urllib.error import URLError
# from googletrans import Translator
from py_translator import Translator

is_prod = (os.environ.get('IS_HEROKU',  None) == 'True')
config = os.environ


def create_session():
	'''
	Create a session with all VK API methods.
	Reference: https://pypi.python.org/pypi/vk/
	'''
	session = vk.Session(config['VK_CROSSPOSTING_ACCESS_TOKEN'])
	api = vk.API(session, v='5.92')
	return api


def make_post(session, post_type, post_data):
	'''
	Make a VK post according to its type
	'''

	# transl = Translator().translate(post_data['caption'], dest='ru')
	if post_data['caption']:
		transl = '\n\nАвто-перевод:\n{}'.format(Translator().translate(text=post_data['caption'], dest='ru').text)
	else:
		transl = ''

	text = '{}:\n\n{}{}\n\nСсылка на пост: {}'.format(post_data['author'], post_data['caption'], transl, post_data['url'])
	video_title = 'Sum 41 Update - ' + post_data['caption'][:30] + '...'

	if post_type == 'image':
		attachments = upload_photo(session, post_data['media'][0]['url'])
	
	elif post_type == 'video':
		attachments = upload_video(session, post_data['media'][0]['url'], video_title, post_data['caption'])

	elif post_type == 'external_video':
		attachments = upload_external_video(session, post_data['media'][0]['url'], video_title, post_data['caption'])

	elif post_type == 'multi':
		attachments_arr = []
		for media in post_data['media']:
			if media['type'] == 'image':
				attachment = upload_photo(session, media['url'])
				attachments_arr.append(attachment)
			elif media['type'] == 'video':
				attachment = upload_video(session, media['url'], video_title, post_data['caption'])
				attachments_arr.append(attachment)
		attachments = ','.join(attachments_arr)
	
	else: # just text
		attachments = ''
	
	post_text(session, text, attachments)


def post_text(session, message, attachments):
	'''
	Make simple post with text and attachmets.
	:param attachments - comma-separated urls
	Reference: https://vk.com/dev/wall.post
	'''
	session.wall.post(owner_id='-'+config['VK_CROSSPOSTING_GROUP_ID'], from_group=1, message=message, attachments=attachments)
	

def upload_photo(session, img_url):
	'''
	Upload image to VK and get its URL

	Reference: https://vk.com/dev/upload_files
	Reference: https://vk.com/dev/photos.getUploadServer
	Reference: https://vk.com/dev/photos.save
	'''

	# Get image to upload
	img = {'photo': ('image.jpg', urlopen(img_url))}

	# Get VK server for image upload
	result = session.photos.getUploadServer(group_id=config['VK_CROSSPOSTING_GROUP_ID'], album_id=config['VK_CROSSPOSTING_PHOTO_ALBUM_ID'])
	upload_url = result['upload_url']

	# Post image to this url
	response = requests.post(upload_url, files=img)
	result = json.loads(response.text)
	# print(result)

	# Save image 
	response = session.photos.save(photos_list=result['photos_list'], album_id=config['VK_CROSSPOSTING_PHOTO_ALBUM_ID'], hash=result['hash'], server=result['server'], group_id=config['VK_CROSSPOSTING_GROUP_ID'])

	return 'photo'+str(response[0]['owner_id'])+'_'+str(response[0]['id'])


def upload_video(session, video_url, title, message):
	'''
	Make a post with video and text.
	Reference: https://vk.com/dev/upload_files
	Reference: https://vk.com/dev/video.save 
	'''

	# Get video to upload
	try: 
		mp4 = urlopen(video_url)
	except URLError as e:
		sys.exit(e.reason)
	
	video = {'video_file': ('video.mp4', mp4)}
	
	# Get upload URL
	result = session.video.save(group_id=config['VK_CROSSPOSTING_GROUP_ID'], name=title, description=message, album_id=config['VK_CROSSPOSTING_VIDEO_ALBUM_ID'])
	upload_url = result['upload_url']

	# Post video to this url
	response = requests.post(upload_url, files=video)

	if result['video_id']:
		return 'video'+str(result['owner_id'])+'_'+str(result['video_id'])
	else:
		sys.exit(response.json())


def upload_external_video(session, video_url, title, message):
	'''
	Make a post with video and text.
	Reference: https://vk.com/dev/upload_files
	Reference: https://vk.com/dev/video.save 
	'''

	result = session.video.save(group_id=config['VK_CROSSPOSTING_GROUP_ID'], link=video_url, name=title, description=message, album_id=config['VK_CROSSPOSTING_VIDEO_ALBUM_ID'])
	response = requests.get(result['upload_url'])
	
	if result['video_id']:
		return 'video'+str(result['owner_id'])+'_'+str(result['video_id'])
	else:
		sys.exit(response.json())