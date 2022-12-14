#!/usr/bin/python3

"""

Handles all interactions with the se push API

See https://documenter.getpostman.com/view/1296288/UzQuNk3E

TODO: handle 400 status requests

"""


from datetime import timedelta
import configparser
import requests_cache

config = configparser.ConfigParser()
config.read("config.ini")
AUTH_HEADER = {'Token': config["Tokens"]["sepush"]}
API_BASE = "https://developer.sepush.co.za/business/2.0/"
CACHE_NAME = "requests_cache"

def _perform_request(endpoint, cache_time=timedelta(days=1)):
    session = requests_cache.CachedSession(CACHE_NAME, expire_after=cache_time)
    response = session.get(API_BASE + endpoint, headers=AUTH_HEADER)
    return response.json()


def find_area(area):
    res = _perform_request("areas_search?text={}".format(area), timedelta(days=10))
    return res


def get_status():
    return _perform_request("status", timedelta(hours=1))["status"]


def get_area_schedule(area_id):
    return _perform_request("area?id={}".format(area_id), cache_time=timedelta(days=6))
