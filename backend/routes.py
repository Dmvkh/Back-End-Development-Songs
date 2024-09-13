from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    doc_count = db.songs.count_documents({})
    return jsonify(dict(count=doc_count)), 200

@app.route("/song")
def songs():
    song_list = db.songs.find({})
    return jsonify(dict(songs=parse_json(song_list))), 200

@app.route("/song/<int:id>")
def get_song_by_id(id):
    song = db.songs.find_one({"id": id})
    return jsonify(dict(songs=parse_json(song))), 200

@app.route("/song", methods=["POST"])
def create_song():
    new_song_data = parse_json(request.json)
    old_song = db.songs.find_one({"id": new_song_data["id"]})
    
    if not old_song:        
        db.songs.insert_one(new_song_data)

        return parse_json(new_song_data), 200
    else: 
        return jsonify(dict(Message="song with id " + str(new_song_data["id"]) + " already present")), 302

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    new_song_data = parse_json(request.json)
    old_song = db.songs.find_one({"id": id})
    
    if not old_song:
        return jsonify(dict(message="song not found")), 404
    else: 

        filter = {"id": id}
        newvalues = { "$set": new_song_data }
        
        result = db.songs.update_one(filter, newvalues)
        updated_song = db.songs.find_one({"id": id})
        if result.modified_count > 0:
            return parse_json(updated_song), 201
        else:
            return jsonify(dict(message="song found, but nothing updated")), 200

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):

    result = db.songs.delete_one({"id": id})
    
    if result.deleted_count > 0:
        return "", 204
    else:
         return jsonify(dict(message="song not found")), 404