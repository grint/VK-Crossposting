# coding=utf8

import vkontakte as vk
import instagram as inst
import log
import time, os

logger = log.setup_log()

def inst_to_vk(count, posts):
	if count:
		start = time.time()
		logger.info('Start crossposting Instagram to VK')
		vk_session = vk.create_session()
		for account in posts:
			new_posts_count = 0
			new_count = prev_count = int(log.get_log_value("instagram_{}".format(account)))
			for post in posts[account]:
				vk.make_post(vk_session, post["type"], post['data'])
				new_count += 1
				new_posts_count += 1
			if new_posts_count:
				logger.info('Successfully posted {} {} post{} to VK'.format(new_posts_count, account, new_count>1 and 's' or ''))
				log.update_log_value("instagram_{}".format(account), str(new_count))
		end = time.time()
		logger.info('Finished. Execution time: {:.2f} sec\n{:77s}'.format(end - start, ('-' * 77)))


if __name__ == "__main__":
	# inst_count, inst_posts = inst.check_instagram(logger)
	# inst_to_vk(inst_count, inst_posts)

	print(os.environ['VK_CROSSPOSTING_GROUP_ID'])
	
