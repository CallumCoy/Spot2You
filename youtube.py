import os.path
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from textify import clean_string, setifyString

CLIENT_SECRET_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


class YouTube:
    playlistMap = {}
    videos = {}
    curTarg = ""
    videos_added = 0
    videos_removed = 0

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    def __init__(self):

        # Get credentials and create an API client
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as __token:
                creds = pickle.load(__token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server()

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as __token:
                pickle.dump(creds, __token)
        self.youtube = build(API_SERVICE_NAME, API_VERSION, credentials=creds)

        self.get_playlists()

    # Searches for the most relevent video, given some search terms.
    def find_video(self, search_term_list):
        request = self.youtube.search().list(
            part="snippet",
            maxResults=1,
            q=search_term_list,
            type="video",
            fields="items(snippet(title),id(videoId))"
        )
        response = self.__executeRequest(request)
        try:
            return {"title": response['items'][0]['snippet']['title'], "vidID": response['items'][0]['id']['videoId']}
        except:
            return None

    # Gets the playlists from the current youtube account.
    def get_playlists(self):
        request = self.youtube.playlists().list(
            part="snippet",
            mine=True,
            fields="items(id,snippet(title)),nextPageToken",
            maxResults=50
        )

        playlistData = self.__executeRequest(request)
        playlists = playlistData['items']

        # Makes a map combining the playlist ID with a playlist name
        for playlist in playlists:
            self.playlistMap.update(
                {[playlist][0]['snippet']['title']: playlist['id']})

        while 'nextPageToken' in playlistData:
            request = self.youtube.playlists().list(
                part="snippet",
                mine=True,
                fields="items(id,snippet(title)),nextPageToken",
                maxResults=50,
                pageToken=playlistData['nextPageToken']
            )
            playlistData = self.__executeRequest(request)
            playlists = playlistData['items']
            for playlist in playlists:
                self.playlistMap.update(
                    {[playlist][0]['snippet']['title']: playlist['id']})

    # Gets, and saves all tracks from a youtube playlist.
    def get_playlist_videos(self, playlist):
        videoSet = []
        request = self.youtube.playlistItems().list(
            part="snippet",
            fields="items(snippet(resourceId(videoId)),snippet(title),id),nextPageToken",
            playlistId=playlist,
            maxResults=50
        )

        playlistData = self.__executeRequest(request)

        # Cleans the response to make lookups easier.
        for video in playlistData['items']:
            clean_video_title = clean_string(video['snippet']['title'])
            videoSet.append({"vidID": video['snippet']['resourceId']['videoId'],
                             "title": clean_video_title, "listPosID": video['id'],
                             "searchTerms": setifyString(clean_video_title)})

        # Youtube returns several pages, with a max of 50 videos.  So we must cycle through all of them.
        while 'nextPageToken' in playlistData:
            request = self.youtube.playlistItems().list(
                part="snippet",
                fields="items(snippet(resourceId(videoId)),snippet(title),id),nextPageToken",
                playlistId=playlist,
                pageToken=playlistData['nextPageToken'],
                maxResults=50
            )

            # Cleans the response to make lookups easier.
            playlistData = self.__executeRequest(request)
            for video in playlistData['items']:
                clean_video_title = clean_string(video['snippet']['title'])
                videoSet.append({"vidID": video['snippet']['resourceId']['videoId'],
                                 "title": clean_video_title, "listPosID": video['id'],
                                 "searchTerms": setifyString(clean_video_title)})

        self.videos.update(
            {playlist: videoSet})

    # Adds songs to youtube playlist.
    def addToPlaylist(self, spotify_tracks, playlistName):

        # Checks if the target even exists.
        if not playlistName in self.playlistMap:
            self.new_playlist(playlistName)

        self.get_playlist_videos(self.playlistMap[playlistName])

        self.curTarg = playlistName
        inYoutubePlaylist = False

        for id, track in spotify_tracks.items():
            if track["added"]:
                continue

            spot_words = track["searchTerms"]

            # Check if the track's artist and title already exist in a video within the YouTube playlist.
            for video in self.videos[self.playlistMap[playlistName]]:
                inYoutubePlaylist = False

                if set(spot_words).issubset(video["searchTerms"]):
                    inYoutubePlaylist = True
                    break

            # If the songs keywords don't exist in the current playlist, search YouTube for it.
            if not inYoutubePlaylist:
                searchInput = track["name"] + " " + " ".join(track["authors"])
                foundVideo = self.find_video(searchInput)

                if foundVideo == None:
                    print("No results found.")
                    break

                # Check if the found video's id already exists in a video within the YouTube playlist.
                for video in self.videos[self.playlistMap[playlistName]]:
                    if foundVideo["vidID"] in video["vidID"]:
                        inYoutubePlaylist = True
                        print(
                            f"Already in playlist: {playlistName}. Video: {video['title']}")
                        # Add the video id to the spotify track
                        track["vidId"] = foundVideo["vidID"]
                        break

            if not inYoutubePlaylist:
                self.add_video(foundVideo["vidID"])
                self.videos_added += 1
                print("Added: " + foundVideo["title"])

            spotify_tracks[id]["added"] = True

        self.__printStats()
        return spotify_tracks

    # prints how many videos were added this session
    def __printStats(self):
        print(
            f"Sync complete, {self.videos_added} video(s) added")

    def add_video(self, video_id):
        request = self.youtube.playlistItems().insert(
            part="snippet",
            body={
                'snippet': {
                    'playlistId': self.playlistMap[self.curTarg],
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        )
        self.__executeRequest(request)

    def new_playlist(self, playlist_name):
        request = self.youtube.playlists().insert(
            part="snippet",
            body={
                "snippet": {
                    "title": playlist_name
                }
            },
            fields="id"
        )
        response = self.__executeRequest(request)

        print(f"{playlist_name} playlist created")
        self.playlistMap.update({playlist_name: [response['id']]})

    def __executeRequest(self, request):
        try:
            return request.execute()
        except Exception as e:
            # Working on getting it to detect if it's a quota error, or something else.
            # if e.json()["reason"] == "quotaExceeded":
            print(e)
            self.__printStats()
            # exit()

            #print(f"Request to youtube failed due to: {e['reason']}")
