# -*- coding: utf-8 -*-

import os, re, db, tweepy

config = os.environ


def auth():
    auth = tweepy.OAuthHandler(config['VK_CROSSPOSTING_TW_CONSUMER_KEY'], config['VK_CROSSPOSTING_TW_CONSUMER_SECRET'])
    auth.set_access_token(config['VK_CROSSPOSTING_TW_ACCESS_KEY'], config['VK_CROSSPOSTING_TW_ACCESS_SECRET'])
    global api 
    api = tweepy.API(auth)
    return api


def check_twitter():
    auth()

    new_posts = {
        'Sum_41': get_new_posts('Sum_41', 'sum41'),
        'fzummo': get_new_posts('Frank', 'fzummo')
    }

    new_count = 0
    for account in new_posts:
        new_count_account = len(new_posts[account])
        new_count += new_count_account
        if new_count_account:
            print('Found {} new {} post{} in Twitter'.format(new_count_account, account, new_count_account>1 and 's' or ''))

    return new_count, new_posts


def get_last_tweet(username):
    tweet = api.user_timeline(screen_name = username, count=1, tweet_mode='extended', exclude_replies='true')
    return tweet[0]


def get_last_tweets(username, since_id):
    '''
    param since_id – Returns only statuses with an ID greater than (that is, more recent than) the specified ID.
    return list of Status objects
    Reference: https://tweepy.readthedocs.io/en/v3.5.0/api.html#API.user_timeline
    '''
    tweets = api.user_timeline(screen_name = username, since_id=since_id, tweet_mode='extended', exclude_replies='true')

    return tweets


def get_new_posts(account, username):
    posts = []
    # Compare post id in the DB log
    try:
        new_posts = 0
        last_id = db.read_logging_table('twitter_'+account)
        if last_id is None:
            # no log in DB, create it
            last_tweet = get_last_tweet(username)
            if hasattr(last_tweet, 'retweeted_status'):
                # it's a retweet
                new_last_id = last_tweet.retweeted_status.id_str
            else:
                new_last_id = last_tweet.id_str

            db.upsert_logging_table("twitter_{}".format(account), new_last_id)
        else:
            # get new pots
            tweets = get_last_tweets(username, last_id[1])
            for tweet in tweets:
                new_posts += 1
                post = get_post(tweet)
                posts.append(post)

        if new_posts > 1:
            posts = list(reversed(posts))

        return posts

    except TypeError as e:
        print('Cannot read DB value, check if values are correct:', e)
        return []


def get_post(tweet):
    '''
    Tweets can only have 1 type of media attached to it. 
    For photos, up to 4 photos can be attached. 
    For videos and GIFs, 1 can be attached. 
    Reference: https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/entities-object
    Reference: https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/extended-entities-object
    '''
    if hasattr(tweet, 'retweeted_status'):
        # it's a retweet
        tweet_data = tweet.retweeted_status
    else:
        tweet_data = tweet

    # Remove url to the tweet from its text
    text = re.sub(r" http\S+$", "", tweet_data.full_text)

    post = {}
    post["type"] = 'text'
    post['data'] = {}
    post['data']['author'] = tweet.user.name
    post['data']['id'] = tweet.id_str
    post['data']['url'] = 'https://twitter.com/Sum41/status/{}'.format(tweet.id_str)
    post['data']['caption'] = text
    post['data']['date'] = str(tweet.created_at)
    post['data']['media'] = []

    entities = tweet_data.entities
    media_entities = get_media_entities(tweet_data)

    # Get Youtube video
    for url in entities['urls']:
        if 'youtu' in url['expanded_url']:
            post['type'] = 'external_video'
            post['data']['media'].append({'type': 'external_video', 'url': url['expanded_url']})

    # Get attached photos, native videos and GIFs
    if media_entities and post['type'] is not 'external_video':
        for media in media_entities['media']:
            mtype, murl = get_media(media)
            post['data']['media'].append({'type': mtype, 'url': murl})
            post['type'] = mtype

    if len(post['data']['media']) > 1:
        post['type'] = 'multi'
    
    return post


def get_media_entities(tweet):
    if hasattr(tweet, 'extended_entities'):
        return tweet.extended_entities
    else: 
        return None


def get_media(media):
    '''
    entities metadata contains the first photo & media type is always ‘photo’
    extended_entities contains all photos with the correct types
    media type: photo, video,  animated_gif
    '''
    if media['type'] == 'video':
        bitrate = 0
        video_url = ''
        for video in media['video_info']['variants']:
            if video['content_type'] == 'video/mp4' and video['bitrate'] > bitrate:
                bitrate = video['bitrate']
                video_url = video['url']
        return media['type'], video_url
    elif media['type'] == 'animated_gif':
        video_url = media['video_info']['variants']['url']
        return 'gif', video_url
    else:
        return media['type'], media['media_url']
