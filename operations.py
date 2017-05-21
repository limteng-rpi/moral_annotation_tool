import json
import time
import uuid
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

# TODO add indexes

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
    doc_num = 0
    for f in files:
        for tweet in parser(archive.open(f)):
            if tweet:
                doc_num += 1
                tweet['_id'] = str(uuid.uuid4())
                tweet['dataset'] = dataset_name
                bulk.insert(tweet)
    rst = bulk.execute()
    collection.create_index('tid')
    collection.create_index('dataset')
    client.close()
    print(rst)
    print('{} documents are inserted'.format(doc_num))


def get_dataset(config, args):
    """Get all documents.
    
    :return: A list of documents. 
    """
    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    collection = client[config['db']['name']][config['db']['col.dataset']]
    documents = []
    for doc in collection.find():
        doc['id'] = doc.pop('_id', None)
        doc['timestamp'] = time.strftime("%b %d, %Y %H:%M:%S",
                                         time.localtime(doc['timestamp']))
        documents.append(doc)
    client.close()
    return documents

def get_dataset_and_document(config, args):
    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    col_dataset = client[config['db']['name']][config['db']['col.dataset']]
    col_document = client[config['db']['name']][config['db']['col.document']]
    selected_ids = set()
    dataset = []
    document = []
    for doc in col_document.find():
        selected_ids.add(doc['_id'])
        doc['id'] = doc.pop('_id', None)
        doc['timestamp'] = time.strftime("%b %d, %Y %H:%M:%S",
                                         time.localtime(doc['timestamp']))
        document.append(doc)
    for doc in col_dataset.find():
        if doc['_id'] not in selected_ids:
            doc['id'] = doc.pop('_id', None)
            doc['timestamp'] = time.strftime("%b %d, %Y %H:%M:%S",
                                             time.localtime(doc['timestamp']))
            dataset.append(doc)
    return {
        'dataset': dataset,
        'document': document
    }

def add_document(config, args):
    id_list = args['id_list']
    if type(id_list) is str:
        id_list = json.loads(id_list)

    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    data_col = client[config['db']['name']][config['db']['col.dataset']]
    doc_col = client[config['db']['name']][config['db']['col.document']]
    bulk = doc_col.initialize_unordered_bulk_op()
    for doc_id in id_list:
        doc = data_col.find_one({'_id': doc_id})
        bulk.insert(doc)
    bulk.execute()
    client.close()
    return 0

def remove_document(config, args):
    id_list = args['id_list']
    if type(id_list) is str:
        id_list = json.loads(id_list)

    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    doc_col = client[config['db']['name']][config['db']['col.document']]
    bulk = doc_col.initialize_unordered_bulk_op()
    for doc_id in id_list:
        bulk.find({'_id': doc_id}).remove_one()
    bulk.execute()
    client.close()
    return 0

__operation_entries = {
    'import_dataset': import_dataset,
    'get_dataset': get_dataset,
    'add_document': add_document,
    'remove_document': remove_document,
    'get_dataset_and_document': get_dataset_and_document
}

# config = ConfigParser()
# config.read('./global.conf')
# args = {
#     'name': 'TestData',
#     'path': '/Users/limteng/Data/test_tweets.zip'
# }
# __operation_entries['import_dataset'](config, args)