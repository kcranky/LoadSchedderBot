#!/usr/bin/python3

"""

Handles all interactions with the se push API

See https://documenter.getpostman.com/view/1296288/UzQuNk3E

TODO: handle 400 status requests

"""


from datetime import timedelta
import KEYS
import requests_cache

AUTH_HEADER = {'Token': KEYS.sepush_token}
API_BASE = "https://developer.sepush.co.za/business/2.0/"
CACHE_NAME = "requests_cache"

def perform_request(endpoint, cache_time=timedelta(days=1)):
    session = requests_cache.CachedSession(CACHE_NAME, expire_after=cache_time)
    response = session.get(API_BASE + endpoint, headers={'Token': KEYS.sepush_token})
    return response.json()


def find_area(area):
    res = perform_request("areas_search?text={}".format(area), timedelta(days=10))
    return res


def get_status():
    return perform_request("status", timedelta(hours=1))["status"]


def get_area_schedule(area_id):
    return perform_request("area?id={}".format(area_id), cache_time=timedelta(days=6))
