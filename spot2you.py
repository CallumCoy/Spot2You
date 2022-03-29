import json

from spotify import Spotify
from youtube import YouTube


def main():
    # Gets data for connecting to the Spotify API.
    with open('config.json', 'r') as myfile:
        data = myfile.read()

    config_data = json.loads(data)

    # Initiate connection to spotifies API
    spotify = Spotify(
        config_data['spotify_client_id'],
        config_data['spotify_client_secret'],
        config_data['spotify_redirect_uri'],
        config_data['spotify_scope'],
        config_data['spotify_username']
    )

    # Retrieves Spotify's playlist data.
    spotify.getPlaylists()
    spotify.printPlaylists()
    # Constantly tries to get a valid input, which is "all", "cancel", or a comination of the shown numbers.
    targetPlaylists = []

    while targetPlaylists == []:
        playlistSelection = str(input(
            "Please enter the corresponding numbers for the playlists you want to make.  You can also type 'all' and 'cancel'.  Please seperate each number by a space.\n"))

        if playlistSelection == "cancel":
            exit()

        if playlistSelection == "all":
            targetPlaylists = spotify.playlistMap
        else:
            # Takes a users input, and clears out any invalid inputs.
            playlistSelection = playlistSelection.split()
            playlistSelection = [
                x for x in playlistSelection if x.isnumeric()]
            playlistSelection = list(map(int, playlistSelection))
            playlistSelection = list(filter(lambda item: item < len(
                spotify.playlistMap) and item >= 0, playlistSelection))

            for item in playlistSelection:
                targetPlaylists.append(spotify.playlistMap[item])

        if targetPlaylists == []:
            print("No playlists were selected.\n\n")
            continue

    print(
        f"You have selected the following playlist/s: \n {targetPlaylists}")

    if "starred" in targetPlaylists:
        spotify.getSavedTracks()

    spotify.getTracks(targetPlaylists)

    # Starts opening youtube API connection.
    youtube = YouTube()

    # Tries adding all of the playlists that were selected.
    for playlist in targetPlaylists:
        print(playlist)
        youtube.addToPlaylist(spotify.playlists[playlist], playlist)


main()
