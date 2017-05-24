import os
import time
from flask import Flask, redirect, jsonify, render_template, request, session,\
    Response, send_from_directory
from werkzeug.utils import secure_filename
from operations import __operation_entries, __admin_operation_entries, \
    check_user, add_annotation, get_progress, create_annotation_file
from urllib.parse import quote_plus
from bson import json_util, ObjectId


from configparser import ConfigParser

__current_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
config = ConfigParser()
config.read(os.path.join(__current_dir, 'global.conf'))
__upload_dir = os.path.join(__current_dir, config['default']['upload_dir'])
__download_dir = os.path.join(__current_dir, config['default']['download_dir'])

if not os.path.exists(__upload_dir):
    os.makedirs(__upload_dir)
if not os.path.exists(__download_dir):
    os.makedirs(__download_dir)

@app.route('/')
def hello_world():
    if session.get('login'):
        return render_template('index.html', username=session.get('username'))
    else:
        return redirect('/login')

@app.route('/management')
def management():
    if session.get('login') and session.get('username')  == 'admin':
        return render_template('management.html')
    else:
        return redirect('/login?redirect={}'.format(quote_plus(request.url)))

@app.route('/progress', methods=['GET', 'POST'])
def progress():
    if session.get('login') and session.get('username') == 'admin':
        if request.method == 'GET':
            return render_template('progress.html')
        else:
            return json_util.dumps({'code': 200, 'result': get_progress(config, request.form)})
    else:
        return redirect('/login?redirect={}'.format(quote_plus(request.url)))


@app.route('/annotation', methods=['GET', 'POST'])
def annotation():
    if session.get('login'):
        if request.method == 'GET':
            if 'dataset' in request.args:
                dataset = request.args['dataset']
                batch_size = request.args['batch_size'] if 'batch_size' in request.args else 50
                document_list = __operation_entries['get_document'](config, {
                    'dataset': dataset,
                    'batch_size': batch_size,
                    'username': session.get('username')
                })
                if len(document_list) > 0:
                    return render_template('annotation.html',
                                           doc_list=document_list,
                                           dataset=dataset,
                                           username=session.get('username'))
                else:
                    return 'All documents have been annotated'
            else:
                return 'No specified dataset'
        elif request.method == 'POST':
            rst = add_annotation(config, {
                'username': session.get('username'),
                'annotation_list': request.form['annotation_list']
            })
            if rst:
                return jsonify({'code': 200})
            else:
                return jsonify({'code': 500})
        else:
            return 'Invalid method: {}'.format(request.method)
    else:
        return redirect('/login?redirect={}'.format(quote_plus(request.url)))


@app.route('/operation', methods=['GET', 'POST'])
def operation():
    if request.method == 'GET':
        args = request.args
    elif request.method == 'POST':
        args = request.form
    else:
        return jsonify({'code': 500, 'msg': 'Invalid method: {}'.format(request.method)})
    if 'entry' in args and args['entry'] in __operation_entries:
        try:
            entry = args['entry']
            result = __operation_entries[entry](config, args)
            return jsonify({'code': 200, 'result': result})
        except Exception as e:
            print(e)
            return jsonify({'code': 500, 'msg': 'Error: {}'.format(e)})
    else:
        return jsonify({'code': 500, 'msg': 'Invalid entry'})


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if session.get('login') and session.get('username') == 'admin':
        if request.method == 'POST':
            print(request.files)
            if 'file' not in request.files:
                return jsonify({'code': 500, 'msg': 'No file part'})
            file = request.files['file']
            if file.filename == '':
                return jsonify({'code': 500, 'msg': 'No selected file'})
            if file:
                if file.filename.endswith('.zip'):
                    dataset_name = request.form['dataset']
                    format = request.form['format']
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(__upload_dir, filename))
                    __operation_entries['import_dataset'](config, {
                        'name': dataset_name,
                        'path': os.path.join(__upload_dir, filename),
                        'parser': format
                    })
                    os.unlink(os.path.join(__upload_dir, filename))
                    return jsonify({'code': 200, 'msg': 'File uploaded'})
                else:
                    return jsonify({'code': 500, 'msg': 'Please upload ZIP archive'})
            return jsonify({'code': 500, 'msg': 'Unknown error'})
        else:
            return render_template('upload.html')
    else:
        return jsonify({'code': 401, 'msg': 'Authorization failed: need admin account'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session['login'] = False
        session['username'] = None
        return render_template('login.html')
    elif request.method == 'POST':
        result = check_user(config, request.form)
        if result['code'] == 200:
            session['login'] = True
            session['username'] = request.form['username']
        return jsonify(result)
    else:
        return 'Invalid method: {}'.format(request.method)


@app.route('/logout')
def logout():
    session['login'] = False
    session['username'] = None
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        session['login'] = False
        session['username'] = None
        return render_template('register.html')
    elif request.method == 'POST':
        result = __admin_operation_entries['add_user'](config, request.form)
        return jsonify(result)
    else:
        return 'Invalid method: {}'.format(request.method)


@app.route("/export", methods=['POST', 'GET'])
def export():
    if request.method == 'POST':
        for f in os.listdir(__download_dir):
            f = os.path.join(__download_dir, f)
            try:
                if os.path.isfile(f):
                    os.unlink(f)
            except Exception as e:
                print(e)
        file_content = create_annotation_file(config, request.form)
        filename = os.path.join(__download_dir, 'annotation_{}.tsv'
                .format(int(time.time())))
        with open(filename, 'w', encoding='utf-8') as w:
            w.write(file_content)
            w.close()
        return jsonify({'filename': os.path.basename(filename)})

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    if session.get('login') and session.get('username') == 'admin':
        return send_from_directory(directory=__download_dir, filename=filename)
    else:
        return jsonify({'code': 401, 'msg': 'Authorization failed: need admin account'})

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
