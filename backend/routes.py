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
@app.route("/songs", methods=["GET"])
def get_songs():
    return jsonify(songs_list)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK"}), 200

@app.route("/count")
def count():
    #songs = db.songs.find()
    num = db.songs.count_documents({})
    return jsonify(dict(count=num)), 200


@app.route("/song")
def songs():
    songs = db.songs.find({})
    return jsonify(dict(songs=parse_json(songs))), 200


@app.route("/song/<int:id>")
def get_song_by_id(id):
    song = db.songs.find_one({"id": id})
    return jsonify(dict(message=parse_json(song))), 200


@app.route("/song", methods=['POST'])
def create_song():
    new_song = request.json
    old_id = db.songs.find_one({"id":new_song["id"]})
    if old_id:
        return jsonify(dict(Message= f"song with id {song['id']} already present"))

    saved = db.songs.insert_one(new_song)

    return jsonify(dict(inserted_id={"$oid": new_song["id"]})), 201


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    new_song = request.json
    old_song = db.songs.find_one({"id":id})
    if old_song:
        db.songs.update_one({"id":id}, {"$set":{**new_song}})
        return jsonify(dict(song=parse_json(db.songs.find_one({"id":id})))), 201
    return jsonify(dict(message="song not found")), 404


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    d = db.songs.delete_one({"id":id})
    print(d)
    if d.deleted_count == 0:
        return jsonify(dict(message="song not found")), 404
    return {}, 204