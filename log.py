import os
import logging

# Set up posts log, it stores number of posts to check if new posts were added
log_filename = '.update_log'
log_temp_filename = '.update_log_temp'

""" 	
Log structure:
	key1 value
	key2 value
"""

def setup_log():
	# logger.info, logger.error, logger.debug
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	handler = logging.FileHandler('.info.log')
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	return logger

def get_log_value(key: str):
	"""
	Get value by key. 
	:return requested value
	"""
	if not os.path.exists(log_filename):
		with open(log_filename, 'w'): pass

	with open(log_filename, 'r+') as input_file:
		for line in input_file:
			(db_key, db_value) = line.split()
			if db_key == key:
				input_file.close()
				return db_value


def update_log_value(key: str, new_value: str):
	"""
	Rewrite value by key. 
	"""
	if not os.path.exists(log_filename):
		with open(log_filename, 'w'): pass
		
	with open(log_filename, 'r+') as input_file, open(log_temp_filename, 'w') as output_file:
		for line in input_file:
			(db_key, db_value) = line.split()
			if db_key == key:
				line = line.replace(db_value, new_value)
			output_file.write(line)
		output_file.close()
		input_file.close()
		os.remove(log_filename)
		os.rename(log_temp_filename, log_filename)
