import os
from flask import Flask, redirect, jsonify, render_template, request, session
from werkzeug.utils import secure_filename
from operations import __operation_entries
from configparser import ConfigParser

__current_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
config = ConfigParser()
config.read(os.path.join(__current_dir, 'global.conf'))
__upload_dir = os.path.join(__current_dir, config['default']['upload_dir'])

if not os.path.exists(__upload_dir):
    os.makedirs(__upload_dir)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/management')
def management():
    return render_template('management.html')

@app.route('/annotation')
def annotation():
    if 'dataset' in request.args:
        dataset = request.args['dataset']

    else:
        return 'No specified dataset'

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
    if request.method == 'POST':
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
                return jsonify({'code': 200, 'msg': 'File uploaded'})
            else:
                return jsonify({'code': 500, 'msg': 'Please upload ZIP archive'})
        return jsonify({'code': 500, 'msg': 'Unknown error'})
    else:
        return render_template('upload.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        pass
    else:
        return 'Invalid method: {}'.format(request.method)


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
