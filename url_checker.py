
import requests
import json
import re


def unshorten_url(url):
    return requests.head(url, allow_redirects=True).url

def coordinates(url):

    response = requests.get(url)

    resp_json_payload = response.json()

    print(json.dumps(resp_json_payload, indent=2))

    print(resp_json_payload['results'][0]['geometry']['location'])


def test1():

    print(unshorten_url("https://goo.gl/maps/uJX7nPUjFKM2"))

    print(coordinates(unshorten_url("https://goo.gl/maps/uJX7nPUjFKM2")))

    print(coordinates('https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA'))

    return

def test2(text):

    print(coordinates('https://maps.googleapis.com/maps/api/geocode/json?address={},+Burbank,+CA'.format(text)))

def extract_lat_long_from(gmap_link):
    lat_long = gmap_link.replace("http://maps.google.com/maps?q=", "")
    lat_long = lat_long.replace("https://maps.google.com/maps?q=", "")
    lat_long = lat_long.replace("https://www.google.com/maps/place/", "")

    pattern = re.compile("^(\-?\d+(\.\d+)?),\s*(\-?\d+(\.\d+)?)$")

    if pattern.match(lat_long):
        return lat_long

    return None

def tolonglat(url):

  # lat = url.replace('/^.+!3d(.+)!4d.+$/', '$1')
  # lng = url.replace('/^.+!4d(.+)!6e.+$/', '$1')7

  lat = re.search('/^.+!3d(.+)!4d.+$/', url, re.IGNORECASE).group(1)
  lng = 0
  return "{0},[1]".format(lat,lng)

def main():
    # test2('McCambridge Park')


    print(tolonglat('https://www.google.com/maps/place/Los+Angeles+Zoo/@34.1413692,-118.295336,15z/data=!4m8!1m2!2m1!1sLa+zoo!3m4!1s0x80c2c0659751c7d5:0x3641cb15292865fd!8m2!3d34.14889!4d-118.283786?shorturl=1'))

main()


