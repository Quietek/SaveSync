#!/usr/bin/env python
import requests
import json



if (__name__ == "__main__"):
    print("Requesting wiki page entry for Divinity: Original Sin Enhanced Edition...")
    FormattedRequest = "https://www.pcgamingwiki.com/w/api.php?action=cargoquery&tables=Infobox_game,Cloud&fields=Cloud.Steam,Cloud.GOG_Galaxy,Cloud.Discord,Cloud.Epic_Games_Launcher,Cloud.EA_Desktop,Cloud.OneDrive,Cloud.Ubisoft_Connect,Cloud.Xbox,Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Released,Infobox_game.Cover_URL&join_on=Infobox_game._pageID=Cloud._pageID&where=Infobox_game.Steam_AppID%20HOLDS%20%22" + "373420" + "%22&format=json"
    r = ''
    qformatted = ''
    cargo = ''
    r = requests.get(FormattedRequest)
    cargo = r.json()['cargoquery']
    steamcloud = 'Unknown'
    pageID = 'Unknown'
    q = ""
    if len(cargo) > 0:
        if 'title' in cargo[0]:
            if 'Steam' in cargo[0]['title']:
                steamcloud = cargo[0]['title']['Steam']
        if steamcloud == 'Unknown':
            print("ERROR: Could not parse information on steam cloud status from wiki page.")
        else:
            print("Steam Cloud information successfully retrieved! Here's the value we got: ")
            print(steamcloud)
        if 'title' in cargo[0]:
            if 'PageID' in cargo[0]['title']:
                pageID = cargo[0]['title']['PageID']
        if pageID == 'Unknown':
            print("ERROR: Could not parse information on the wiki's page ID from the response we received from PCGamingWiki.")
        else:
            qformatted = "https://www.pcgamingwiki.com/w/api.php?action=parse&format=json&pageid=" + pageID + "&prop=wikitext"
            q = requests.get(qformatted)
    if q != "" and 'parse' in q.json() and 'wikitext' in q.json()['parse']:
        print("Data successfully retrieved from PCGaming Wiki!")
        print('Here is the full wikipage text: ')
        print(q.json()['parse']['wikitext']['*'])
    elif q != "":
        print("ERROR: a JSON response was received but it is missing expected fields")
        print("Here is the full json data received: ")
        print(q.json())
        print("And here is the relevant request url: ")
        print(qformatted)
    elif cargo != '':
        print("ERROR: a JSON response was received to our initial request, but we could not determine a PageID from it's contents.")
        print("The relevent request URL is: " + formattedRequest)
        print("The data received looks like: ")
        print(cargo)
    else:
        print("ERROR: no data was received from PCGamingWiki, if this isn't due to maintenance on the site or a temporary outage, there likely need to be changes to the request formatting.")
        print("The relevant request URL looked is: " + FormattedRequest)
