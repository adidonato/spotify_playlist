# Spotify Playlist Generator


## Usage

From the command line run the script providing the input text to run against the Spotify API and return a playlist.
Use ``-m`` argument for text input and optional ``-v`` for full song metadata as json dump instead of URI only.
Uses the [Spotify Web API](https://developer.spotify.com/web-api/) and does not require a Spotify account.

##### Full output example

```
python playlist_generator.py -m "input text for playlist generation" -v

Input: {
  "album_type": "album",
  "available_markets": [
    "AD",
    "AR",
    "AT",
    "AU",
    "BE",
    "BG",
    "BO",
    "BR",
    "CA",
    "CH",
    "CL",
    "CO",
    "CR",
    "CY",
    "CZ",
    "DE",
    "DK",
    "DO",
    "EC",
    "EE",
    "ES",
    "FI",
    "FR",
    "GB",
    "GR",
    "GT",
    "HK",
    "HN",
    "HU",
    "IE",
    "IS",
    "IT",
    "LI",
    "LT",
    "LU",
    "LV",
    "MC",
    "MT",
    "MX",
    "MY",
    "NI",
    "NL",
    "NO",
    "NZ",
    "PA",
    "PE",
    "PH",
    "PL",
    "PT",
    "PY",
    "RO",
    "SE",
    "SG",
    "SI",
    "SK",
    "SV",
    "TR",
    "TW",
    "US",
    "UY"
  ],
  "external_urls": {
    "spotify": "https://open.spotify.com/album/4EjywcOrNzRG9qHbKlDqtI"
  },
  "href": "https://api.spotify.com/v1/albums/4EjywcOrNzRG9qHbKlDqtI",
  "id": "4EjywcOrNzRG9qHbKlDqtI",
  "images": [
    {
      "height": 640,
      "url": "https://i.scdn.co/image/553b9eb986ad8e71fd73f6ca8b8836524b9b7e2f",
      "width": 640
    },
    {
      "height": 300,
      "url": "https://i.scdn.co/image/fe14dece366b67969daf4e383db0a9fa20683eaa",
      "width": 300
    },
    {
      "height": 64,
      "url": "https://i.scdn.co/image/09b05000576810ed5330c2dcaed13d4c8ac63e80",
      "width": 64
    }
  ],
  "name": "Feel.Love.Thinking.Of.",
  "type": "album",
  "uri": "spotify:album:4EjywcOrNzRG9qHbKlDqtI"
}: : [
    {
        "external_urls": {
            "spotify": "https://open.spotify.com/artist/5f3XEqM6vNrETqlzCMufGK"
        },
        "href": "https://api.spotify.com/v1/artists/5f3XEqM6vNrETqlzCMufGK",
        "id": "5f3XEqM6vNrETqlzCMufGK",
        "name": "Faunts",
        "type": "artist",
        "uri": "spotify:artist:5f3XEqM6vNrETqlzCMufGK"
    }
]spotify:track:2r2NTJJvFDYnze4dCQkEqs

```

##### Get only URI example

```
$ python playlist_generator.py -m "input text for playlist generation"

spotify:track:2r2NTJJvFDYnze4dCQkEqs

```

## License

Use in complaince with the [Spotify Terms Of Use](https://developer.spotify.com/developer-terms-of-use/)
