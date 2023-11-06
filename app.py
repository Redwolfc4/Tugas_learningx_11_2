from flask import (
    Flask, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    jsonify                   
)
from bson import ObjectId
from dotenv import load_dotenv
import os
from os.path import join, dirname
from pymongo import MongoClient
import requests
from datetime import datetime

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

uri = os.environ.get('MONGODB_URI')
client = MongoClient(uri)
db = client[os.environ.get('DB_NAME')]


app = Flask(__name__)

@app.route("/")
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition  
        })
    msg= request.args.get('msg')
    return render_template("index.html", words=words, msg=msg)

@app.route("/detail/<keyword>")
def detail(keyword):
    api_key_dictionary = 'b1e3f9b2-f099-403b-8c8b-3e8ea803a006'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key_dictionary}'
    
    r = requests.get(url)
    definitions = r.json()
    print(definitions)
    
    if not definitions:
        return redirect(url_for(
            'error',
            keyword =keyword,
            definitions = None
        ))
        
    if type(definitions[0]) is str:
        return redirect(url_for(
            'error',
            keyword = keyword,
            definitions = definitions
        ))
    
    status = request.args.get('status_give', 'new') # parameter,value
    print(status)
    
    return render_template(
        "detail.html", 
        word=keyword,
        definitions=definitions,
        status = status
        )

@app.route('/error')
def error():
    definitions = request.args.getlist('definitions')
    keyword = request.args.get('keyword')
    return render_template('error.html', keywords=keyword, definitions=definitions)

@app.route("/api/save_word", methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y-%M-%d %H:%M:%S')
    }
    
    db.words.insert_one(doc)
    
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!'
    })
    
@app.route("/api/delete_word", methods=["DELETE"])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was delete'
    })
    
@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word':word})
    examples = []
    
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id'))
        })
    return jsonify({
        'result': 'success',
        'examples': examples
    })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the example, {example}, for the word, {word}, was saved'
    })


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg': f'Your example for the, {word}, was deleted'
    })

# @app.route("/practice")
# def practice():
#     return render_template('practice.html')

if __name__ == '__main__':
    app.run('0.0.0.0',debug=True,port=5000)