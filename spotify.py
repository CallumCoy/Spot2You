import spotipy
from spotipy.oauth2 import SpotifyOAuth

from textify import clean_string, setifyString


class Spotify:
    playlists = {}
    playlistMap = []

    def __init__(self, client_id, client_secret, redirect_url, scope, username):
        self.__username = username
        self.__sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                              client_secret=client_secret,
                                                              redirect_uri=redirect_url,
                                                              scope=scope))

    def printPlaylists(self):
        for index, playlist in enumerate(self.playlists):
            print(index, ".", playlist, ":", len(self.playlists[playlist]))

    def getSavedTracks(self):
        tracks = []
        SavedTracks = self.__getUsersSaved()

        # Formats all tracks from the saved playlist
        for track in SavedTracks['items']:
            cleanTitle = clean_string(track['track']['name'])
            cleanAuthors = list(
                map(self.__getArtist, track['track']['artists']))

            tracks.append(
                {"name": cleanTitle,
                 "authors": cleanAuthors,
                 "searchTerms": setifyString(cleanTitle + " " + " ".join(cleanAuthors))})

        # Spotify returns several pages with max length of 20 tracks, so we need to cycle through all of them.
        while SavedTracks['next']:
            SavedTracks = self.__getNextItem(SavedTracks)
            tracks = self.__generateTrackList(SavedTracks['items'], tracks)

        self.playlists.update({"starred": tracks})
        self.playlistMap.append("starred")

    # Gets all other playlists from spotify.
    def getPlaylists(self):
        playlists_data = []
        PlaylistList = self.__getUsersPlaylists()

        # Forms a list of all the playlists the user has on their profile.
        for playlist in PlaylistList['items']:
            playlists_data.append(
                {"name": playlist['name'], "id": playlist['id']})

        # Spotify returns pages with a max of 50 playlists a page, so we pull the playlists from all pages.
        while PlaylistList['next']:
            PlaylistList = self.__getNextItem(PlaylistList)
            playlists_data = self.__generateTrackList(
                PlaylistList['items'], playlists_data)

        # Cycle through each playlist getting all tracks
        for playlist in playlists_data:
            tracks = []

            playlistData = self.__getPlaylistsTracks(
                playlist['id'], playlist["name"])
            tracks = self.__generateTrackList(playlistData['items'], tracks)

            # Spotify returns several pages each with a max of 20 tracks, so we cycle through all pages.
            while playlistData['next']:
                playlistData = self.__getNextItem(playlistData)
                tracks = self.__generateTrackList(
                    playlistData['items'], tracks)

            self.playlists.update({playlist["name"]: tracks})
            self.playlistMap.append(playlist["name"])

    # Cleans tracklist data, and adds a list of search terms.
    def __generateTrackList(self, rawTracks, refinedTracks):
        for track in rawTracks:
            cleanTitle = clean_string(track['track']['name'])
            cleanAuthors = list(
                map(self.__getArtist, track['track']['artists']))

            refinedTracks.append(
                {"name": cleanTitle,
                 "authors": cleanAuthors,
                 "searchTerms": setifyString(cleanTitle + " " + " ".join(cleanAuthors))})

        return refinedTracks

    # Retrieves a users "saved" songs, aka Liked songs.  Spotify saves this playlist seperate from all the other playlists.
    def __getUsersSaved(self):
        attempts = 0

        # Spotify's API files quite often.  ~5% of the time so this is jut makes sure it gets the info.  But will also fail eventually to prevent looping
        while attempts <= 5:
            try:
                results = self.__sp.current_user_saved_tracks()
                return results
            except:
                attempts = attempts + 1
                if attempts > 5:
                    print("Failed to get saved tracks.")

        return {}

    def __getUsersPlaylists(self):
        attempts = 0

        # Spotify's API files quite often.  ~5% of the time so this is jut makes sure it gets the info.  But will also fail eventually to prevent looping
        while attempts <= 5:
            try:
                playlistTracks = self.__sp.current_user_playlists()
                return playlistTracks
            except:
                attempts = attempts + 1
                if attempts > 5:
                    print("Failed to get playlists.")
                    break
        return {}

    def __getPlaylistsTracks(self, playlistID, playlistName):
        attempts = 0

        # Spotify's API files quite often.  ~5% of the time so this is jut makes sure it gets the info.  But will also fail eventually to prevent looping
        while attempts <= 5:
            try:
                playlistTracks = self.__sp.user_playlist_tracks(
                    self.__username, playlistID)
                return playlistTracks
            except:
                attempts = attempts + 1
                if attempts > 5:
                    print("Failed to get tracks for:", playlistName)
                    break

        return {}

    def __getNextItem(self, curVal):
        attempts = 0

        # Spotify's API files quite often.  ~5% of the time so this is jut makes sure it gets the info.  But will also fail eventually to prevent looping
        while attempts <= 5:
            try:
                nextVal = self.__sp.next(curVal)
                return nextVal
            except:
                attempts = attempts + 1
                if attempts > 5:
                    print("Failed to get all songs for.")
                    attempts = 0

        return {}

    # Returns artist,  only exiasts for some map calls.
    def __getArtist(self, artist):
        return artist["name"]
