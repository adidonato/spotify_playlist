#!/usr/bin/env python
__author__ = 'Angelo Di Donato'

import argparse
import sys
import re
import logging
import requests
import json
from datetime import timedelta
from datetime import datetime
from abc import ABCMeta
from abc import abstractmethod
from threading import Thread
from Queue import Queue


class SpotifyAPIerror(Exception):
    def __init__(self, status):
        self.status = status

def get_sub_l_len(lst):
    ls_len = 0
    if lst:
        for item in lst:
            ls_len += len(item)
    return ls_len


def issue_smaller_lists(word_list, max_chunk_length=None):
    if not max_chunk_length or max_chunk_length > len(word_list):
        max_chunk_length = len(word_list)
    return [word_list[0:x] for x in range(max_chunk_length, 0, -1)]


class stripper(object):

    def __init__(self, message, max_chunk_length=None):
        self.prefix = []
        self.word_list = message.split()
        if max_chunk_length:
            self.max_chunk_length = max_chunk_length
        else:
            self.max_chunk_length = len(self.word_list)
        self.chunks = issue_smaller_lists(self.word_list, self.max_chunk_length)
        self.counter = 0

    def __iter__(self):
        return self

    def next(self):

        if get_sub_l_len(self.prefix) >= len(self.word_list):
            raise StopIteration

        self.counter += 1
        try:
            current_chunk = self.chunks[self.counter - 1]
            index = get_sub_l_len(self.prefix) + len(current_chunk)
            return self.prefix + [current_chunk] + [self.word_list[index:]]
        except IndexError:
            if self.prefix:
                if len(self.prefix) == 1 and len(self.prefix[0]) == 1:
                    raise StopIteration
                self._backtrack()
                return None
            else:
                raise StopIteration

    def progress(self):

        self.prefix.append(self.chunks[self.counter - 1])
        index = get_sub_l_len(self.prefix)
        self.max_chunk_length = len(self.word_list) - index
        self.chunks = issue_smaller_lists(self.word_list[index:], self.max_chunk_length)
        self.counter = 0

    def _backtrack(self):
        prefix_length = get_sub_l_len(self.prefix)
        last_prefix_group_length = len(self.prefix.pop())
        index = prefix_length - last_prefix_group_length
        self.max_chunk_length = last_prefix_group_length - 1
        self.chunks = issue_smaller_lists(self.word_list[index:], self.max_chunk_length)
        self.counter = 0

def dt_http(datestring):
    return datetime.strptime(datestring, '%a, %d %b %Y %H:%M:%S %Z')


def http_dt(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')


class PLCache(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def put(self, key, value):
        pass

    @abstractmethod
    def remove(self, key):
        pass


class pl_items:

    def __init__(self, name, album, artists, uri, last_modified, expires):
        self.name = name
        self.album = album
        self.artists = artists
        self.uri = uri
        self.last_modified = last_modified
        self.expires = expires

    def is_expired(self):
        return datetime.utcnow() > self.expires

    def __str__(self):
        return self.name

    def __str__(self):
        return self.album

    def __str__(self):
        return self.artists

class MPLCache(PLCache):

    def __init__(self):
        self.cache = {}

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            return None

    def put(self, key, value):
        self.cache[key] = value

    def remove(self, key):
        del self.cache[key]

    def __str__(self):
        output = ""
        for key in self.cache.iterkeys():
            output += "* {} / {} \n".format(key, self.cache[key].uri)
        return output

SPOTIFY_BASE_TRACK_URL = 'http://open.spotify.com/track/'
SPOTIFY_API_SEARCH_TRACK_URL = 'https://api.spotify.com/v1/search'
VALID_API_STATUSCODES = [200, 304, 404]

logger = logging.getLogger(__name__)


def get_url(uri):
    uri_match = re.match(r'spotify:track:(?P<id>\w{22})', uri)
    if uri_match:
        return SPOTIFY_BASE_TRACK_URL + uri_match.group('id')
    return None


class make_playlist(object):

    def __init__(self, cache=None):
        self.cache = cache
        if self.cache and not isinstance(self.cache, PLCache):
            raise AttributeError

    def do_playlist(self, message, use_max_chunk_length=False):
        # cleanup
        message = re.sub(r'[^a-zA-Z0-9\s\']', '', message)
        if use_max_chunk_length:
            max_chunk_length = len(message.split())
        else:
            max_chunk_length = len(message.split()) - 1
        chunker = stripper(message, max_chunk_length)
        playlist = []
        discarded_playlists = []
        index = 0
        words_covered = 0
        for chunk in chunker:
            if not chunk:
                discarded_playlists.append([item for item in playlist])
                words_covered -= len(playlist.pop().name.split())
                index -= 1
                continue

            title = " ".join(chunk[index]).strip().lower()

            if self.cache:
                try:
                    item = self._fetch_item_from_cache(title)
                except SpotifyAPIerror:
                    raise
                if item:
                    playlist.append(item)
                    words_covered += len(chunk[index])
                    index += 1
                    chunker.progress()
                    continue

            try:
                item = self._get_songs(title)
            except SpotifyAPIerror:
                raise
            if item:
                if self.cache:
                    self.cache.put(title, item)
                playlist.append(item)
                words_covered += len(chunk[index])
                index += 1
                chunker.progress()
        if not playlist or words_covered < len(message.split()):
            incomplete = True
            sorted_playlists = sorted(discarded_playlists, key=len, reverse=True)
            playlist = sorted_playlists[0] if sorted_playlists else playlist
        else:
            incomplete = False
        return playlist, incomplete

    @staticmethod
    def _get_songs(title):
        params = {'q': title, 'type': 'track'}
        r = requests.get(SPOTIFY_API_SEARCH_TRACK_URL, params=params)
        if r.status_code not in VALID_API_STATUSCODES:
            raise SpotifyAPIerror(r.status_code)
        elif r.status_code == 404:
            return None

        last_modified = dt_http(r.headers['Date'])
        max_age_match = re.match(r'.*max-age=(?P<age>\d+)', r.headers['Cache-Control'])
        if max_age_match:
            max_age = int(max_age_match.group('age'))
        else:
            max_age = None
        expires = datetime.utcnow() + timedelta(seconds=max_age)
        decoded_result = r.json()
        track_listing = decoded_result['tracks']['items']
        valid_tracks = [track for track in track_listing if title == track['name'].lower().strip()]
        if valid_tracks:
            return pl_items(valid_tracks[0]['name'], valid_tracks[0]['album'], valid_tracks[0]['artists'],  valid_tracks[0]['uri'], last_modified, expires)
        else:
            return None

    def _fetch_item_from_cache(self, title):
        cached_item = self.cache.get(title)
        if cached_item and not cached_item.is_expired():
            logger.debug("went to cache for.. '%s'", title)
            return cached_item
        elif cached_item:
            logger.debug("cache expiration '%s'", title)
            modified_since = http_dt(cached_item.last_modified)
            params = {'q': title, 'type': 'track'}
            headers = {'If-Modified-Since': modified_since}
            r = requests.get(SPOTIFY_API_SEARCH_TRACK_URL, params=params, headers=headers)

            if r.status_code not in VALID_API_STATUSCODES:
                raise SpotifyAPIerror(r.status_code)
            if r.status_code == 304:
                logger.debug("remaining cache '%s'", title)
                return cached_item
            else:
                logger.debug("invalid for '%s'", title)
                self.cache.remove(title)
                return None


class PLGeneratorThread(Thread):

    def __init__(self, queue, generator):
        Thread.__init__(self)
        self.queue = queue
        self.generator = generator
        self.payload = None
        self.incomplete = True
        self.playlist = None
        self.position = None

    def run(self):
        self.payload = self.queue.get()
        self.position = self.payload[1]
        print "running thread {}".format(str(self.position))
        self.playlist, self.incomplete = self.generator.do_playlist(self.payload[0], True)
        self.queue.task_done()


def multi_thread_playlists(list_of_messages, cache):
    queue = Queue()
    generator = make_playlist(cache)
    threads = [PLGeneratorThread(queue, generator) for message in list_of_messages]
    for thread in threads:
        thread.setDaemon(True)
        thread.start()
    for x in range(len(list_of_messages)):
        queue.put((list_of_messages[x], x))

    queue.join()

    return [(thread.playlist, thread.incomplete) for thread in sorted(threads, key=lambda thread: thread.position)]


def multi_naive_playlists(list_of_messages, cache):
    generator = make_playlist(cache)
    results = [generator.do_playlist(message) for message in list_of_messages]
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate a Spotify playlist from the provided message")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-m", "--message", help="The message you want turned into a playlist")
    group.add_argument("-i", "--interactive", help="Run this script in interactive mode",  action='store_true')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",  action='store_true')
    parser.add_argument("-u", "--url", help="use Spotify web url instead of uri",  action='store_true')
    args = parser.parse_args()

    if args.interactive:
        cache = None
    else:
        cache = MPLCache()

    if not args.interactive:
        try:
            messages = [message for message in re.split(r'[.?!/\n]', args.message) if len(message) > 0]
            if len(messages) > 1:
                playlist = []
                incomplete = False
                results = multi_thread_playlists(messages, cache)
                for result in results:
                    if result[1]:
                        incomplete = True
                    playlist.extend(result[0])
            else:
                pl_gen = make_playlist(cache)
                playlist, incomplete = pl_gen.do_playlist(messages[0])
            if playlist:
                if incomplete and args.verbose:
                    print "Only found:"
                for item in playlist:
                    if args.url:
                        url = get_url(item.uri)
                    else:
                        url = item.uri

                    if args.verbose:
                        print item.name + ": " + json.dumps((item.album), sort_keys=True, indent=2, separators=(',', ': '))  + ": " + ": " + json.dumps((item.artists), sort_keys=True, indent=4, separators=(',', ': ')) + url
                    else:
                        print url
            else:
                print "failed to generate playlist"
        except SpotifyAPIerror as e:
            sys.exit("Spotify API error occured({})! Bye!".format(str(e.status)))
    else:
        print "Deprecated"


if __name__ == '__main__':
    main()
