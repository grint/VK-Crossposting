import os, facebook

config = os.environ

def get_posts():
    '''
    Reference: https://facebook-sdk.readthedocs.io/en/latest/api.html
    '''

    try:
        graph = facebook.GraphAPI(access_token=config['VK_CROSSPOSTING_FB_ACEESS_TOKEN'])
        page = graph.get_object(id='sum41')
        query_string = 'posts?limit={0}'.format(count)
        posts = graph.get_connections(page['id'], query_string)

        print(page)

    except facebook.GraphAPIError as e:
        print(e)
        return None

