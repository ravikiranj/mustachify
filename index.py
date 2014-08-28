#!/usr/bin/env python

import cgi
import urllib
import requests
import json
import mustachify
import pyimgur
import random
import sys

downloadImagePath = "gs_image.jpg"
mustachifyImagePath = "mustachfied_image.jpg"
keyword = " "

def getGoogleImageSearchUrl():
    form = cgi.FieldStorage()
    keyword = ""
    if form.has_key('q'):
        keyword = form['q'].value
    elif len(sys.argv) > 1:
        keyword = sys.argv[1]

    if keyword == "":
        return ""

    googleImageSearchUrl = "https://ajax.googleapis.com/ajax/services/search/images?v=1.0&imgtype=face&q=" + urllib.quote(keyword)
    r = requests.get(googleImageSearchUrl)
    if r.status_code != 200:
        return ""
    jsonResp = json.loads(r.text)
    url = ""
    if "responseData" in jsonResp and "results" in jsonResp["responseData"] and len(jsonResp["responseData"]["results"]) > 0:
        image = random.choice(jsonResp["responseData"]["results"])
        if "url" in image:
            url = image["url"]
    return url
#end

def downloadAndMustachifyImage(url):
    f = open(downloadImagePath,'wb')
    f.write(requests.get(url).content)
    f.close()
    argv = ["mustachify.py", "-i", downloadImagePath, "-o", mustachifyImagePath]
    mustachify.main(argv)
#end

def uploadToImgur():
    CLIENT_ID = "0e2beed54800eb2"
    im = pyimgur.Imgur(CLIENT_ID)
    uploaded_image = im.upload_image(mustachifyImagePath, title="Mustachify "+keyword)
    return uploaded_image.link
#end

url = getGoogleImageSearchUrl()
msg = "There was an error while mustachifying, I blame Ravi!"
if (url != ""):
    downloadAndMustachifyImage(url)
    msg = uploadToImgur()

print msg
