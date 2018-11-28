# coding=utf8

import vkontakte as vk
import instagram as inst
# import faceboook as fb
import twitter as tw
import time, os, db

# db_conn, db_cursor = db.connect_db()
# db.create_update_table(db_conn, db_cursor)


def inst_to_vk(count, posts):
	if count:
		print('Start crossposting Intagram to VK')
		vk_session = vk.create_session()
		for account in posts:
			new_posts_count = 0
			new_total_count = prev_count = int(db.read_logging_table("instagram_{}".format(account))[1])
			for post in posts[account]:
				vk.make_post(vk_session, post["type"], post['data'])
				new_total_count += 1
				new_posts_count += 1
			if new_posts_count:
				print('Successfully posted {} {} post{} to VK'.format(new_posts_count, account, new_posts_count>1 and 's' or ''))
				db.upsert_logging_table("instagram_{}".format(account), str(new_total_count))
		

def twitter_to_vk(count, posts):
	if count:
		print('Start crossposting Twitter to VK')
		vk_session = vk.create_session()
		for account in posts:
			new_last_id = None
			new_posts_count = 0
			for post in posts[account]:
				new_last_id = post['data']['id']
				vk.make_post(vk_session, post["type"], post['data'])
				new_posts_count += 1
			if new_posts_count:
				print('Successfully posted {} {} post{} to VK'.format(new_posts_count, account, new_posts_count>1 and 's' or ''))
				try:
					db.upsert_logging_table("twitter_{}".format(account), str(new_last_id))
				except TypeError as e:
					print('Error by updating ID for Twitter in the database: ' + e)


if __name__ == "__main__":
	db.init()
	start = time.time()

	inst_count, inst_posts = inst.check_instagram()
	inst_to_vk(inst_count, inst_posts)

	# tw_count, tw_posts = tw.check_twitter()
	# twitter_to_vk(tw_count, tw_posts)
	
	db.close_db_conn()
	
	if inst_count:
		end = time.time()
		print('Finished. Execution time: {:.2f} sec'.format(end - start))

	# fb.get_posts()


