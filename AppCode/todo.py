#!/usr/bin/env python3

import logging
import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from prometheus_client import Counter, Gauge, CollectorRegistry, generate_latest
from pymongo import MongoClient

app = Flask(__name__)

# Configure debug mode
debug_enabled = os.environ.get('DEBUG_ENABLED', 'false').lower() == 'true'
app.logger.info(f'DEBUG_ENABLED={debug_enabled}')

# Configure logging level
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level)
app.logger.info(f'LOG_LEVEL={log_level}')

# Configure MongoDB endpoint URI
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
app.logger.info(f'MONGO_URI={mongo_uri}')
mongo_client = MongoClient(host=mongo_uri)
try:
    mongo_client.admin.command('ping')
    app.logger.info(f'Connected to MongoDB server at {mongo_uri}')
except Exception as e:
    app.logger.error('Failed to connect to MongoDB server at %s', mongo_uri, exc_info=e)
    sys.exit(1)
db = mongo_client['todo']
collection = db['tasks']

# Configure Prometheus metrics
metrics_enabled = os.environ.get('METRICS_ENABLED', 'true').lower() == 'true'
app.logger.info(f'METRICS_ENABLED={metrics_enabled}')
index_requests = Counter('index_requests', 'Count of requests to index.html page')
tasks_count = Gauge('tasks_count', 'Number of existing tasks')
tasks_added = Counter('tasks_added', 'Count of tasks added')
tasks_edited = Counter('tasks_edited', 'Count of tasks edited')
tasks_deleted = Counter('tasks_deleted', 'Count of tasks deleted')
if metrics_enabled:
    registry = CollectorRegistry()
    registry.register(index_requests)
    registry.register(tasks_count)
    registry.register(tasks_added)
    registry.register(tasks_edited)
    registry.register(tasks_deleted)


def get_all_tasks():
    return collection.find()

def add_task(task):
    app.logger.info(f'Adding task: "{task}"...')
    if not task:
        app.logger.error(f'Task has no value for name - cannot add!')
        return 400
    elif collection.find_one({'task': task}):
        app.logger.error(f'Task "{task}" already in collection - cannot add!')
        return 409
    else:
        date = datetime.utcnow()
        collection.insert_one({'task': task, 'date': date})
        tasks_added.inc()
        tasks_count.inc()
        app.logger.info(f'Task added: "{task}"')
        return 201

def delete_task(task):
    app.logger.info(f'Deleting task: "{task}"...')
    if collection.find_one({'task': task}):
        collection.delete_one({'task': task})
        tasks_deleted.inc()
        tasks_count.dec()
        app.logger.info(f'Task deleted: "{task}"')
        return 202
    else:
        app.logger.error(f'Task "{task}" not found in collection - cannot delete!')
        return 404

def edit_task(old_task, new_task):
    app.logger.info(f'Editing task: "{old_task}" to "{new_task}"...')
    if collection.find_one({'task': new_task}):
        app.logger.error(f'Task "{new_task}" already in collection - cannot edit!')
        return 409
    if collection.find_one({'task': old_task}):
        collection.update_one({'task': old_task}, {'$set': {'task': new_task}})
        tasks_edited.inc()
        app.logger.info(f'Task edited: "{old_task}" -> "{new_task}"')
        return 201
    else:
        app.logger.error(f'Task "{old_task}" not found in collection - cannot edit!')
        return 404

@app.route('/', methods=['GET'])
def index():
    index_requests.inc()
    tasks = get_all_tasks()
    return render_template('index.html', tasks=tasks)

@app.route('/api', methods=['GET'])
def api_index():
    tasks = get_all_tasks()
    result = [task['task'] for task in tasks]
    return jsonify(result), 200

@app.route('/add', methods=['POST'])
def add():
    task = request.form['task']
    add_task(task)
    return redirect(url_for('.index'))

@app.route('/api/add', methods=['POST'])
def api_add():
    task = request.form['task']
    status_code = add_task(task)
    return jsonify({"task": task}), status_code

@app.route('/delete', methods=['POST'])
def delete():
    task = request.form['task']
    delete_task(task)
    return redirect(url_for('.index'))

@app.route('/api/delete', methods=['POST'])
def api_delete():
    task = request.form['task']
    status_code = delete_task(task)
    return jsonify({"task": task}), status_code

@app.route('/api/edit', methods=['PUT'])
def api_edit():
    old_task = request.form['old_task']
    new_task = request.form['new_task']
    status_code = edit_task(old_task, new_task)
    return jsonify({'old_task': old_task, 'new_task': new_task}), status_code

@app.route('/metrics', methods=['GET'])
def metrics():
    if not metrics_enabled:
        app.logger.warn(f'Metrics requested (although disabled)')
        return 'Metrics are disabled', 501
    app.logger.debug(f'Metrics requested')
    return generate_latest(registry)

if __name__ == '__main__':
    app.logger.info(f'Application started')
    app.run(host='0.0.0.0', debug=debug_enabled)
