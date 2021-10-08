from pyyoutube import Api
from config import config
import webbrowser
from enum import IntEnum
from datetime import datetime
import time
import json
import os

class VideoStatus(IntEnum):
    AVAILABLE = 1
    PRIVATE = 2
    DELETED = 3

def get_video_status(title, description):
    if title == "Private video" and description == "This video is private.":
        return VideoStatus.PRIVATE
    if title == "Deleted video" and description == "This video is unavailable.":
        return VideoStatus.PRIVATE
    return VideoStatus.AVAILABLE

def make_video(video_id, title, status):
    return {
        "video_id": video_id,
        "title": title,
        "status": status,
    }

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def printAndWrite(file, string, color=Colors.ENDC):
	print(color + string + Colors.ENDC)
	file.write(string + "\n")

def generate_action(video_id, title, action):
    return "[{}] [{}]\t{}".format(video_id, action, title)

VERSION = 1
storage = {}

api = Api(client_id=config["client-id"], client_secret=config["client-secret"])

auth_url = api.get_authorization_url()[0]
webbrowser.open(auth_url)
print()
print("{}Visit the following url to sign-in:{}\n{}".format(Colors.HEADER, Colors.ENDC, auth_url))
print()
auth_response = input("{}Paste the entire url after you have authorized:{} ".format(Colors.HEADER, Colors.ENDC))
api.generate_access_token(authorization_response=auth_response)

if os.path.exists("storage.json"):
    with open("storage.json", "r") as storageFile:
        storage = json.loads(storageFile.read())["data"]

with open("logs/{}.log".format(time.time()), "w") as logFile:
    printAndWrite(logFile, "******************************************************************************")
    printAndWrite(logFile, "Report generated on " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    printAndWrite(logFile, "******************************************************************************")
    playlists = api.get_playlists(mine=True, count=None)
    for playlist in playlists.items:
        printAndWrite(logFile, "Playlist: {}".format(playlist.snippet.title), Colors.HEADER)
        if playlist.id not in storage:
            storage[playlist.id] = {}
            printAndWrite(logFile, "New playlist is now tracked!")
        playlist_items = api.get_playlist_items(playlist_id=playlist.id, count=None)
        for video in playlist_items.items:
            if video.snippet.resourceId.kind != "youtube#video":
                continue
            video_id = video.contentDetails.videoId
            title = video.snippet.title
            description = video.snippet.description
            status = get_video_status(title, description)
            if video_id not in storage[playlist.id]:
                storage[playlist.id][video_id] = make_video(video_id, title, status)
                continue
            storage_video = storage[playlist.id][video_id]
            if status == VideoStatus.AVAILABLE:
                if storage_video["status"] == VideoStatus.AVAILABLE: # A -> A
                    storage_video["title"] = title
                elif storage_video["status"] == VideoStatus.PRIVATE: # P -> A
                    storage_video["title"] = title
                    printAndWrite(logFile, generate_action(video_id, storage_video["title"], "Private -> Available"), Colors.OKGREEN)
            elif status == VideoStatus.PRIVATE:
                if storage_video["status"] == VideoStatus.AVAILABLE: # A -> P
                    printAndWrite(logFile, generate_action(video_id, storage_video["title"], "Available -> Private"), Colors.FAIL)
            elif status == VideoStatus.DELETED:
                if storage_video["status"] == VideoStatus.AVAILABLE: # A -> D
                    printAndWrite(logFile, generate_action(video_id, storage_video["title"], "Available -> Deleted"), Colors.FAIL)
                elif storage_video["status"] == VideoStatus.PRIVATE: # P -> D
                    printAndWrite(logFile, generate_action(video_id, storage_video["title"], "Private -> Deleted"), Colors.WARNING)
            storage_video["status"] = status
        printAndWrite(logFile, "******************************************************************************")
    printAndWrite(logFile, "Log saved to {}".format(logFile.name))

export = {
    "VERSION": VERSION,
    "data": storage,
}

with open("storage.json", "w") as storageFile:
    storageFile.write(json.dumps(export))
