#!/usr/bin/env python

import cgi
import urllib
import requests
import json
import mustachify
import pyimgur

downloadImagePath = "gs_image.jpg"
mustachifyImagePath = "mustachfied_image.jpg"

def getSearchQuery():
    query = ""
    form = cgi.FieldStorage()
    if form.has_key('q'):
        query = form['q'].value
    return query
#end

def getUrl():
    url = ""
    form = cgi.FieldStorage()
    if form.has_key('url'):
        url = form['url'].value
    return url
#end

def getGoogleImageSearchUrl(query):
   
    googleImageSearchUrl = "https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=" + urllib.quote(query)
    r = requests.get(googleImageSearchUrl)
    if r.status_code != 200:
        return ""
    jsonResp = json.loads(r.text)
    url = ""
    if "responseData" in jsonResp and "results" in jsonResp["responseData"] and len(jsonResp["responseData"]["results"]) > 0 and "url" in jsonResp["responseData"]["results"][0]:
        url = jsonResp["responseData"]["results"][0]["url"]
    return url
#end

def downloadAndMustachifyImage(url):
    f = open(downloadImagePath,'wb')
    f.write(requests.get(url).content)
    f.close()
    argv = ["mustachify.py", "-i", downloadImagePath, "-o", mustachifyImagePath]
    mustachify.main(argv)
#end

def uploadToImgur(query):
    CLIENT_ID = "0e2beed54800eb2"
    im = pyimgur.Imgur(CLIENT_ID)
    uploaded_image = im.upload_image(mustachifyImagePath, title="Mustachify "+query)
    return uploaded_image.link
#end

msg = "There was an error while mustachifying, I blame Ravi!"
try:
    query = getSearchQuery()
    url = getUrl()

    if query != "" and url == "":
        url = getGoogleImageSearchUrl(query)

    if url != "":
        downloadAndMustachifyImage(url)
        msg = uploadToImgur(query)
    print msg
except:
    print msg
    import sys
    print >> sys.stderr, sys.exc_info()[0]

