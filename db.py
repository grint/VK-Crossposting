import psycopg2, os
import urllib.parse as urlparse

config = os.environ

def init():
    global conn
    global cursor
    conn, cursor = connect_db()
    create_logging_table()


def connect_db():
    try:
        url = urlparse.urlparse(config['VK_CROSSPOSTING_DATABASE'])
        dbname = url.path[1:]
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = conn.cursor()
        return conn, cursor

    except (Exception, psycopg2.Error) as error:
        print ("Error while connecting to PostgreSQL:", error)


def create_logging_table():
    try:
        create_table_query = '''CREATE TABLE IF NOT EXISTS update_log (account text PRIMARY KEY, num_posts int)'''
        cursor.execute(create_table_query)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print ("Error while creating PostgreSQL table:", error)


def upsert_logging_table(account, num_posts):
    try:
        sql_insert_query = '''INSERT INTO update_log(account, num_posts) VALUES (%s, %s) ON CONFLICT (account) DO UPDATE SET num_posts = EXCLUDED.num_posts;'''
        cursor.execute(sql_insert_query, (account,num_posts))
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print ("Error while inserting to PostgreSQL table:", error)


def read_logging_table(account_name):
    '''
    return tuple (account, post_num)
    '''
    try:
        cursor.execute('''SELECT account, num_posts FROM update_log WHERE account=%s''', (account_name,))
        row = cursor.fetchone()
        if cursor is not None:
            cursor.close()
        return row
    except (Exception, psycopg2.DatabaseError) as error:
        print ("Error while reading PostgreSQL table:", error)


def close_db_conn():
    if conn is not None:
        conn.close()