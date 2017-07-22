import re
import json
import time
import uuid
import zipfile
import traceback
from pymongo import MongoClient
from passlib.hash import pbkdf2_sha256
from bson import json_util

def __parser_twitter_api(reader):
    for line in reader:
        try:
            line = str(line, encoding='utf-8')
            tweet = json.loads(line)
            tid = tweet['id_str']
            # Mon Apr 17 15:33:04 +0000 2017
            timestamp = time.mktime(time.strptime(tweet['created_at'][4:],
                                                  '%b %d %H:%M:%S %z %Y'))
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
            traceback.print_exc()
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

def __parser_script_output(reader):
    for line in reader:
        try:
            line = str(line, encoding='utf-8')
            tweet = json.loads(line)
            tid = tweet['tweet_id']
            text = tweet['tweet']
            retweet = False
            timestamp = time.mktime(time.strptime(tweet['createdAt'][4:],
                                                  '%b %d %H:%M:%S %z %Y'))
            entities = {}
            yield {
                'tid': tid,
                'text': text,
                'full_text': text,
                'retweet': retweet,
                'timestamp': timestamp,
                'entities': entities
            }
        except Exception:
            yield None

def __parser_alm(reader):
    for line in reader:
        try:
            line = str(line, encoding='utf-8')
            tweet = json.loads(line)
            tid = tweet['tid']
            text = tweet['text']
            full_text = tweet['full_text']
            timestamp = tweet['timestamp']
            entities = {'hashtags': tweet['entities']}
            retweet = tweet['retweet']
            yield {
                'tid': tid,
                'text': text,
                'full_text': full_text,
                'retweet': retweet,
                'timestamp': timestamp,
                'entities': entities
            }
        except Exception:
            yield None



__parser = {
    'twitter_api': __parser_twitter_api,
    'gnip': __parser_gnip,
    'script_output': __parser_script_output,
    'alm': __parser_alm,
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
    files = [f for f in archive.namelist() if not f.startswith('__MACOSX')
             and f.endswith('json')]
    print(args)
    print('Found {} file(s) in the archive'.format(len(files)))
    print(files)
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
        doc['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S",
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
        doc['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                         time.localtime(doc['timestamp']))
        document.append(doc)
    for doc in col_dataset.find():
        if doc['_id'] not in selected_ids:
            doc['id'] = doc.pop('_id', None)
            doc['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime(doc['timestamp']))
            dataset.append(doc)
    return {
        'dataset': dataset,
        'document': document
    }

def get_document(config, args):
    batch_size = args['batch_size'] if 'batch_size' in args else 50
    dataset = args['dataset']
    username = args['username']
    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    col_document = client[config['db']['name']][config['db']['col.document']]
    col_annotation = client[config['db']['name']][config['db']['col.annotation']]
    annotated_doc = set()
    for anno in col_annotation.find({'username': username}):
        annotated_doc.add(anno['uuid'])
    batch = []
    for doc in col_document.find({'dataset': dataset}):
        uuid = doc['_id']
        if uuid in annotated_doc:
            continue
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S",
                                         time.localtime(doc['timestamp']))
        tid = doc['tid']
        text = doc['full_text']
        text_char = [[i, c] for i, c in enumerate(text, 0)]
        retweet = doc['retweet']
        batch.append({
            'id': uuid,
            'timestamp': timestamp,
            'text': text,
            'text_char': text_char,
            'retweet': retweet,
            'tid': tid
        })
        if len(batch) >= batch_size:
            break
    client.close()
    return batch

def get_document_single(config, args):
    dataset = args['dataset']
    tid = args['tid']
    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    col_document = client[config['db']['name']][config['db']['col.document']]
    doc = col_document.find_one({'tid': tid, 'dataset': dataset})
    if doc:
        return [{
            'id': doc['_id'],
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S",
                                       time.localtime(doc['timestamp'])),
            'text': doc['full_text'],
            'text_char': [[i, c] for i, c in enumerate(doc['full_text'], 0)],
            'retweet': doc['retweet'],
            'tid': tid
        }]
    else:
        return None

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

def encrypt_password(password, rounds=100000, salt_size=3):
    return pbkdf2_sha256.encrypt(password, rounds=rounds, salt_size=salt_size)

def verify_password(password, encrypt):
    return pbkdf2_sha256.verify(password, encrypt)

def add_user(config, args):
    try:
        username = args['username']
        password = args['password']
        first_name = args['firstname']
        last_name = args['lastname']

        username_pattern = re.compile('^[A-Za-z0-9]{4,20}$')
        name_pattern = re.compile('^[A-Za-z]{1,30}$')
        password_pattern = re.compile('^[A-Za-z0-9#\\.@$%^_-]{8,20}$')

        if not username_pattern.match(username):
            return {'code': 406, 'msg': 'Invalid username'}
        if not name_pattern.match(first_name):
            return {'code': 406, 'msg': 'Invalid first name'}
        if not name_pattern.match(last_name):
            return {'code': 406, 'msg': 'Invalid last name'}
        if not password_pattern.match(password):
            return {'code': 406, 'msg': 'Invalid password'}

        db_host = config['db']['host']
        db_port = int(config['db']['port'])
        client = MongoClient(host=db_host, port=db_port)
        user_col = client[config['db']['name']][config['db']['col.user']]

        if user_col.find_one({'_id': username}) is not None:
            client.close()
            return {'code': 406, 'msg': 'This username has been used'}

        user_col.insert({
            '_id': username,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'password': encrypt_password(password)
        })
        client.close()
        return {'code': 200}
    except Exception as e:
        print(e)
        return {'code': 500, 'msg': e}

def check_user(config, args):
    try:
        username = args['username']
        password = args['password']

        db_host = config['db']['host']
        db_port = int(config['db']['port'])
        client = MongoClient(host=db_host, port=db_port)
        user_col = client[config['db']['name']][config['db']['col.user']]

        user_record = user_col.find_one({'_id': username})
        client.close()
        if user_record is None:
            return {'code': 404, 'msg': 'Username doesn\'t exist'}
        else:
            encrypt = user_record['password']
            if verify_password(password, encrypt):
                return {'code': 200}
            else:
                return {'code': 401, 'msg': 'Incorrect password'}
    except Exception as e:
        return {'code': 500, 'msg': str(e)}

def add_annotation(config, args):
    try:
        username = args['username']
        annotation_list = json.loads(args['annotation_list'])
        db_host = config['db']['host']
        db_port = int(config['db']['port'])
        client = MongoClient(host=db_host, port=db_port)
        col_annotation = client[config['db']['name']][config['db']['col.annotation']]
        bulk = col_annotation.initialize_unordered_bulk_op()
        for annotation in annotation_list:
            annotation['username'] = username
            bulk.insert(annotation)
        rst = bulk.execute()
        client.close()
        print(rst)
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def update_annotation(config, args):
    try:
        username = args['username']
        annotation_list = json.loads(args['annotation_list'])
        db_host = config['db']['host']
        db_port = int(config['db']['port'])
        client = MongoClient(host=db_host, port=db_port)
        col_annotation = client[config['db']['name']][config['db']['col.annotation']]
        bulk = col_annotation.initialize_unordered_bulk_op()
        for annotation in annotation_list:
            annotation['username'] = username
            col_annotation.remove({'username': username, 'uuid': annotation['uuid']})
            bulk.insert(annotation)
        rst = bulk.execute()
        client.close()
        print(rst)
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def get_dataset_names(config, args):
    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    doc_col = client[config['db']['name']][config['db']['col.document']]
    dataset = set()
    for doc in doc_col.find():
        dataset.add(doc['dataset'])
    client.close()
    return list(dataset)

def get_user_document(config, args):
    dataset = args['dataset']
    username = args['username']

    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    col_document = client[config['db']['name']][config['db']['col.document']]
    col_annotation = client[config['db']['name']][config['db']['col.annotation']]

    annotated_doc = set()
    document_list = []
    for anno in col_annotation.find({'username': username}):
        annotated_doc.add(anno['uuid'])
    for doc in col_document.find({'dataset': dataset}):
        uuid = doc['_id']
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.localtime(doc['timestamp']))
        tid = doc['tid']
        text = doc['full_text']
        retweet = '●' if doc['retweet'] else '○'
        annotated = '●' if uuid in annotated_doc else '○'
        document_list.append({
            'recid': len(document_list),
            'uuid': uuid,
            'timestamp': timestamp,
            'text': text,
            'retweet': retweet,
            'annotated': annotated,
            'tid': tid
        })
    client.close()
    return document_list

def get_progress(config, args):
    dataset = args['dataset']
    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    col_document = client[config['db']['name']][config['db']['col.document']]
    col_annotation = client[config['db']['name']][config['db']['col.annotation']]
    annotation_list = []
    for anno in col_annotation.find({'dataset': dataset}):
        uuid = anno['uuid']
        doc = col_document.find_one({'_id': uuid})
        anno['doc'] = doc
        anno['tid'] = doc['tid']
        anno['text'] = doc['full_text']
        anno['recid'] = len(annotation_list)
        anno['unclear'] = '●' if 'unclear' in anno and anno['unclear'] else '○'
        anno['skip'] = '●' if 'skip' in anno and anno['skip'] else '○'
        anno['retweet'] = '●' if doc['retweet'] else '○'
        anno['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S",
                                          time.localtime(anno['timestamp']))
        annotation_list.append(anno)
    client.close()
    return annotation_list

def create_annotation_file(config, args):
    id_list = json_util.loads(args['id_list'])
    db_host = config['db']['host']
    db_port = int(config['db']['port'])
    client = MongoClient(host=db_host, port=db_port)
    col_document = client[config['db']['name']][config['db']['col.document']]
    col_annotation = client[config['db']['name']][config['db']['col.annotation']]
    result = 'Dataset\tTweet ID\tUsername\tFoundation\tComment\tAbstract Issue' \
             '\tIssue Start\tIssue End\tIssue\n'
    for _id in id_list:
        anno = col_annotation.find_one({'_id': _id})
        uuid = anno['uuid']
        dataset = anno['dataset']
        username = anno['username']
        issue = anno['issue'] if 'issue' in anno else ''
        issue_start = anno['issue_start'] if 'issue_start' in anno else ''
        issue_end = anno['issue_end'] if 'issue_end' in anno else ''
        abs_issue = anno['abstract_issue'] if 'abstract_issue' in anno else ''
        comment = anno['comment'] if 'comment' in anno else ''
        category = ','.join(anno['category']) if 'category' in anno else ''
        doc = col_document.find_one({'_id': uuid})
        tid = doc['tid']
        result += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'\
            .format(dataset, tid, username, category, comment, abs_issue,
                    issue_start, issue_end, issue).replace('\n', ' ') + '\n'
    return result


def get_annotation(config, args):
    username = args['username']
    uuid = args['uuid']
    with MongoClient(host=config['db']['host'], port=int(config['db']['port'])) as client:
        col_annotation = client[config['db']['name']][config['db']['col.annotation']]
        annotation = col_annotation.find_one({'username': username, 'uuid': uuid})
        if annotation:
            annotation.pop('_id', None)
            return {'annotated': True, 'annotation': annotation}
        else:
            return {'annotated': False}



__operation_entries = {
    'import_dataset': import_dataset,
    'get_dataset': get_dataset,
    'add_document': add_document,
    'remove_document': remove_document,
    'get_dataset_and_document': get_dataset_and_document,
    'get_document': get_document,
    'get_dataset_names': get_dataset_names,
    'get_user_document': get_user_document,
    'get_document_single': get_document_single,
    'get_annotation': get_annotation
}

__admin_operation_entries = {
    'add_user': add_user
}