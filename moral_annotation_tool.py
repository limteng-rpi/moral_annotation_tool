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
app.config['UPLOAD_FOLDER'] = __upload_dir

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/management')
def management():
    return render_template('management.html')

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
    if 'file' not in request.files:
        return jsonify({'code': 500, 'msg': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 500, 'msg': 'No selected file'})
    if file and file.filename.endswith('.zip'):
        filename = secure_filename(file.filename)
        file.save(os.path.join(__upload_dir, filename))
        return jsonify({'code': 200, 'msg': 'File uploaded'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
