import json
import time
import zipfile
from pymongo import MongoClient
from configparser import ConfigParser

def __parser_twitter_api(reader):
    for line in reader:
        try:
            line = str(line, encoding='utf-8')
            tweet = json.loads(line)
            tid = tweet['id_str']
            timestamp = int(tweet['timestamp_ms'])
            retweet = 'retweeted_status' in tweet
            text = tweet['text']
            full_text = tweet['retweeted_status']['text'] if retweet else tweet['text']
            entities = tweet['entities']
            yield {
                'tid': tid,
                'timestamp': timestamp,
                'retweet': retweet,
                'text': text,
                'full_text': full_text,
                'entities': entities
            }
        except Exception:
            yield None

def __parser_gnip(reader):
    for line in reader:
        try:
            line = str(line, encoding='utf-8')
            tweet = json.loads(line)
            tid = tweet['id']
            timestamp = time.mktime(time.strptime(tweet['postedTime'][:-5],
                                                  '%Y-%m-%dT%H:%M:%S'))
            retweet = tweet['verb'] == 'share'
            text = tweet['body']
            entities = tweet['twitter_entities']
            full_text = tweet['object']['body'] if retweet else tweet['body']
            yield {
                'tid': tid,
                'timestamp': timestamp,
                'retweet': retweet,
                'text': text,
                'full_text': full_text,
                'entities': entities
            }
        except Exception:
            yield None

__parser = {
    'twitter_api': __parser_twitter_api,
    'gnip': __parser_gnip
}

def import_dataset(config, args):
    """Import dataset from an uploaded zip archive file.
    
    :param config: Global configuration.
    :param args: Arguments.
    """
    dataset_name = args['name']
    data_path = args['path']
    parser = args['parser'] if 'parser' in args else 'twitter_api'
    parser = __parser[parser] if parser in __parser else __parser['twitter_api']

    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    collection = client[config['db']['name']][config['db']['col.dataset']]

    bulk = collection.initialize_unordered_bulk_op()
    archive = zipfile.ZipFile(data_path, 'r')
    files = archive.namelist()
    print('Found {} file(s) in the archive'.format(len(files)))
    for f in files:
        for tweet in parser(archive.open(f)):
            if tweet:
                tweet['dataset'] = dataset_name
                bulk.insert(tweet)
    rst = bulk.execute()
    print(rst)
    client.close()


def add_document(config, args):
    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    collection = client[config['db']['name']][config['db']['col.dataset']]

__operation_entries = {
    'import_dataset': import_dataset
}

config = ConfigParser()
config.read('./global.conf')
args = {
    'name': 'TestData',
    'path': '/Users/limteng/Data/test_tweets.zip'
}
__operation_entries['import_dataset'](config, args)