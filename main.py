# coding=utf8

import vkontakte as vk
import instagram as inst
import time, os, db


# db_conn, db_cursor = db.connect_db()
# db.create_update_table(db_conn, db_cursor)


def inst_to_vk(count, posts):
	if count:
		start = time.time()
		print('Start crossposting Instagram to VK')
		vk_session = vk.create_session()
		for account in posts:
			new_posts_count = 0
			new_count = prev_count = db.read_logging_table("instagram_{}".format(account))[1]
			for post in posts[account]:
				vk.make_post(vk_session, post["type"], post['data'])
				new_count += 1
				new_posts_count += 1
			if new_posts_count:
				print('Successfully posted {} {} post{} to VK'.format(new_posts_count, account, new_count>1 and 's' or ''))
				db.upsert_logging_table("instagram_{}".format(account), new_count)
		end = time.time()
		print('Finished. Execution time: {:.2f} sec'.format(end - start))


if __name__ == "__main__":
	db.init()
	inst_count, inst_posts = inst.check_instagram()
	inst_to_vk(inst_count, inst_posts)
	db.close_db_conn()
