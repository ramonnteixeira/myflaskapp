import os
import json
from datetime import datetime
from flask import Flask, request, render_template, abort, send_from_directory, jsonify
from flask.ext.socketio import SocketIO, emit
from flask.ext.pymongo import PyMongo
from bson.objectid import ObjectId
from bson import json_util

app = Flask(__name__)
app.config.from_pyfile('flaskapp.cfg')
socketio = SocketIO(app)

if __name__ == '__main__':
    app.config['MONGO_DBNAME'] = 'kanban-dev'
else:
    mongodb_host = os.environ.get('OPENSHIFT_MONGODB_DB_HOST','localhost')
    mongodb_port = os.environ.get('OPENSHIFT_MONGODB_DB_PORT','27017')
    app.config['MONGO_HOST'] = os.environ['OPENSHIFT_MONGODB_DB_HOST']
    app.config['MONGO_PORT'] = os.environ['OPENSHIFT_MONGODB_DB_PORT']
    app.config['MONGO_USERNAME'] = 'admin'
    app.config['MONGO_PASSWORD'] = '4sFxnI1c3cmE'
    app.config['MONGO_DBNAME'] = 'myflaskapp'

mongo = PyMongo(app)
copyright = 'Kanban Betha 0.0.1 Develop by ramon.nteixeira@gmail.com'
 
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def to_json(cursor):
    return [json.loads(json.dumps(doc, cls=CustomEncoder)) for doc in cursor]

def from_json(json_docs):
    return [json.loads(j_doc, default=json_util.object) for j_doc in json_docs]
 
def getNextSequence(name):
    counter = mongo.db.counters.find_one({'id' : name})
    atual = 0;

    if bool(counter):
        atual = counter['value']

    atual = atual+1

    mongo.db.counters.update({'id' : name}, {'$set': {'value':atual}}, True)
    return atual

@app.route('/<path:resource>')
def serveStaticResource(resource):
    return send_from_directory('static/', resource)

@app.route('/')
def index():
    return render_template('kanban.html', copyright=copyright)

@app.errorhandler(404)
def not_found(error):
    return render_template('notfound.html')

@app.route('/db/populate', methods=['GET'])
def populate_db():
    tasks = [
        {'id': 1, 'title': 'Titulo Post-it 001', 'description': 'Descricao 001', 'color': 'yellow', 'stepId':1 },
        {'id': 2, 'title': 'Titulo Post-it 002', 'description': 'Descricao 002', 'color':'red', 'stepId':1},
        {'id': 3, 'title': 'Titulo Post-it 003', 'description': 'Descricao 003', 'color':'yellow', 'stepId':1},
        {'id': 4, 'title': 'Titulo Post-it 004', 'description': 'Descricao 004', 'color':'red', 'stepId':1}
    ]

    steps = [
        {'id': 1, 'title': 'A fazer', 'tasks': []},
        {'id': 2, 'title': 'Fazendo', 'tasks': []},
        {'id': 3, 'title': 'Fazer/Teste', 'tasks': []},
        {'id': 4, 'title': 'Testando', 'tasks': []},
        {'id': 5, 'title': 'Impedido', 'tasks': []},
        {'id': 6, 'title': 'Feito', 'tasks': [], 'isFinally':True}
    ];

    if len(to_json(mongo.db.steps.find())) == 0:
        for step in steps:
            step['id'] = getNextSequence('step')
            mongo.db.steps.insert(step)
    
    if len(to_json(mongo.db.tasks.find())) == 0:
        for task in tasks:
            task['id'] = getNextSequence('task')
            mongo.db.tasks.insert(task)

    return '<p>Database populada com sucesso</p>'

@app.route('/api/steps', methods=['GET'])
def get_steps():
    steps = to_json(mongo.db.steps.find())
    for step in steps:
        step['tasks'] = to_json(mongo.db.tasks.find({'stepId': step['id']}))

    return jsonify({'steps': steps})

@app.route('/api/tasks/<int:task_id>/<int:step_id>', methods=['GET'])
def new_step(task_id, step_id):
    mongo.db.tasks.update({'id' : task_id}, {'$set': {'stepId':step_id}})
    return get_steps()

@app.route('/api/tasks', methods=['POST'])
def create_task():
    task = request.json
    if not task or not 'title' in task:
        abort(400)

    task['id'] = getNextSequence('task');
    mongo.db.tasks.insert(task)

    return jsonify({'result': True})

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = request.json
    if not task or not 'title' in task:
        abort(400)

    mongo.db.tasks.update({'id' : task['id']}, {'$set': task})

    return jsonify({'result': True})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    mongo.db.tasks.remove({'id': task_id})
    return jsonify({'result': True})

@socketio.on('broadcast update', namespace='/update_steps')
def update_steps():
    emit('update_all_clients', broadcast=True)


if __name__ == '__main__':
    socketio.run(app)
