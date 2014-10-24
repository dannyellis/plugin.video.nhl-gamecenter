from xml.dom.minidom import parseString
from datetime import datetime
import time
import pickle

from resources.lib.common import *


def getSeasons():
    #Dowload the xml file
    xmlFile = downloadFile('http://gamecenter.nhl.com/nhlgc/servlets/allarchives',{'date' : 'true', 'isFlex' : 'true'})
    
    #Get available seasons
    xml = parseString(xmlFile)
    seasons = xml.getElementsByTagName("season")
    
    seasonList = []
    
    for season in reversed(seasons):
        print season.attributes["id"].value
        if (season.attributes["id"].value == "2007"):#Links don't work
            break
        elif (season.attributes["id"].value == "2008"):#Links don't work
            break
        elif (season.attributes["id"].value == "2009"):#Links don't work
            break
        else:
            aSeason = [int(season.attributes["id"].value)]
            dates = season.getElementsByTagName("g")

            for date in reversed(dates):
                if len(date.childNodes[0].nodeValue)>10: #Fix for alternative date format
                    if aSeason[-1] != int(date.childNodes[0].nodeValue[5:7]):
                        aSeason.append(int(date.childNodes[0].nodeValue[5:7]))
                else:
                    if aSeason[-1] != int(date.childNodes[0].nodeValue[:2]):
                        aSeason.append(int(date.childNodes[0].nodeValue[:2]))
            
            seasonList.append(aSeason)

    #Save thelist of seasons
    pickle.dump(seasonList, open(os.path.join(ADDON_PATH_PROFILE, 'archive'),"wb"))
    
    return seasonList


def getGames(url):
    
    #Split the url
    splittedURL = url.split("/")
    typeOfVideo = splittedURL[1]
    year = splittedURL[2]
    month = splittedURL[3]

    #Download the xml file
    if typeOfVideo == 'condensed' or int(year) >= 2012:
        values = {'season' : year, 'isFlex' : 'true', 'month' : month, 'condensed' : 'true'}
    else:
        values = {'season' : year, 'isFlex' : 'true', 'month' : month}
    
    xmlFile = downloadFile('http://gamecenter.nhl.com/nhlgc/servlets/archives',values)
    #print xmlFile
    
    #Parse the xml file
    xml = parseString(xmlFile)
    games = xml.getElementsByTagName("game")
    
    #
    gameList = []
    
    #Latest game
    latestGame = games[0].getElementsByTagName("date")[0].childNodes[0].nodeValue[:10]
    latestGame = datetime.fromtimestamp(time.mktime(time.strptime(latestGame,"%Y-%m-%d"))).strftime(xbmc.getRegion('dateshort'))
    
    #Get available games
    for game in games:
        gid = game.getElementsByTagName("gid")[0].childNodes[0].nodeValue
        date = game.getElementsByTagName("date")[0].childNodes[0].nodeValue
        homeTeam = game.getElementsByTagName("homeTeam")[0].childNodes[0].nodeValue
        awayTeam = game.getElementsByTagName("awayTeam")[0].childNodes[0].nodeValue
        streamURL = game.getElementsByTagName("publishPoint")[0].childNodes[0].nodeValue

        try:
            awayGoals = game.getElementsByTagName("awayGoals")[0].childNodes[0].nodeValue
            homeGoals = game.getElementsByTagName("homeGoals")[0].childNodes[0].nodeValue
        except:
            awayGoals = ''
            homeGoals = ''
        
        #Change color of goals
        #awayGoals = '[COLOR=FF00B7EB]'+ awayGoals + '[/COLOR]'
        #homeGoals = '[COLOR=FF00B7EB]'+ homeGoals + '[/COLOR]'
        
        #Versus string
        versus = 31400
        if ALTERNATIVEVS == 'true':
            versus = 31401

        #Localize the date
        date2 = date[:10]
        date = datetime.fromtimestamp(time.mktime(time.strptime(date2,"%Y-%m-%d"))).strftime(xbmc.getRegion('dateshort'))
        
        #Get teamnames
        teams = getTeams()
        
        #Game title
        if awayTeam in teams and homeTeam in teams:
            name = date + ': ' + teams[awayTeam][TEAMNAME] + " " + LOCAL_STRING(versus) + " " + teams[homeTeam][TEAMNAME]
        else:
            name = date + ': ' + awayTeam + " " + LOCAL_STRING(versus) + " " + homeTeam
        
        if typeOfVideo != "lastnight": #Show all games
            gameList.append([name, gid, homeTeam, awayTeam, streamURL])
        elif latestGame == date: #show only latest games
            gameList.append([name, gid, homeTeam, awayTeam, streamURL])
    
    #Save the list of games
    pickle.dump(gameList, open(os.path.join(ADDON_PATH_PROFILE, 'games'),"wb"))
        
    return gameList


def getGameLinks(url):
    
    #Video type
    typeOfVideo = url.split("/")[1]
    year = url.split("/")[2]
    
    if typeOfVideo == "lastnight":
        if "archive" in url:
            typeOfVideo = "archive"
        elif "condensed" in url:
            typeOfVideo = "condensed"
        elif "highlights" in url:
            typeOfVideo = "highlights"
    
    #Load the list of games
    gameList = pickle.load(open(os.path.join(ADDON_PATH_PROFILE, 'games'),"rb"))
    
    #
    linkList = []
    
    #Get the url of the game
    for game in gameList:
        if game[1] in url:
            #Add teamnames and game title to the list
            title = game[0]
            homeTeam = game[2]
            awayTeam = game[3]
            linkList = [title, [homeTeam, awayTeam]]
            
            #Quality settings            
            if QUALITY == 4 or 'bestquality' in url:
                quality = ''
            elif '5000K' in url:
                quality = '_5000' 
            elif QUALITY == 3 or '4500K' in url:
                quality = '_4500'
                if int(year) >= 2012:
                    quality = '_4500'
                else:
                    quality = '_3000'
            elif QUALITY == 2 or '3000K' in url:
                quality = '_3000'
            elif QUALITY == 1 or '1600K' in url:
                quality = '_1600'
            else:
                quality = '_800'
            
            #Get the HLS stream
            playPath = game[4][37:][:-49]
            http_url = "http://nhl.cdn.neulion.net/" + playPath[4:] + "/v1/playlist" + quality + ".m3u8"
            http_url = http_url.replace('/pc/', '/ced/')
            
            #Fix for 2012-2013 season
            if int(year) >= 2012:
                http_url = http_url.replace('http://nhl.cdn.neulion.net/', 'http://nlds150.cdnak.neulion.com/')
                http_url = http_url.replace('s/nhlmobile/vod/nhl/', 'nlds_vod/nhl/vod/')
                http_url = http_url.replace('/v1/playlist', '')
                http_url = http_url.replace('.m3u8', '_ced.mp4.m3u8')

                #Fix for early games in the season
                http_url = http_url.replace('condensed_ced', 'condensed_1_ced')
                http_url = http_url.replace('condensed_4500', 'condensed_1_4500')
                http_url = http_url.replace('condensed_3000', 'condensed_1_3000')
                http_url = http_url.replace('condensed_1600', 'condensed_1_1600')
                http_url = http_url.replace('condensed_800', 'condensed_1_800')

                #Fix for some streams
                http_url = http_url.replace('s/as3/', '')
                
                if typeOfVideo == 'archive':
                    http_url = http_url.replace('condensed', 'whole')
                    http_url = http_url.replace('_ced.mp4', '_ipad.mp4')
                elif typeOfVideo == 'highlights':
                    http_url = http_url.replace('condensed', 'continuous')
            
            
            home_url = http_url
            away_url = http_url.replace('_h_', '_a_')
            
            
            #Home url
            linkList.append([LOCAL_STRING(31320), home_url])
            
            #Away url
            linkList.append([LOCAL_STRING(31330), away_url])

            #French streams (experimental)
            """
            if homeTeam == 'MON' or homeTeam == 'OTT':
                home_url = home_url.replace('/nhl/', '/nhlfr/')
                home_url = home_url.replace('nlds138', 'nlds60')
                linkList.append([LOCAL_STRING(31320) + ' (' + LOCAL_STRING(31340) + ')', home_url])
            if awayTeam == 'MON' or awayTeam == 'OTT':
                away_url = away_url.replace('/nhl/', '/nhlfr/')
                away_url = away_url.replace('nlds138', 'nlds60')
                linkList.append([LOCAL_STRING(31330) + ' (' + LOCAL_STRING(31340) + ')', away_url])
            """
            

            break
    
    return linkList
    