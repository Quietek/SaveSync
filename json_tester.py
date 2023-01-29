import requests
import json
r = ''
r = requests.get("https://www.pcgamingwiki.com/w/api.php?action=cargoquery&tables=Infobox_game,Cloud&fields=Cloud.Steam,Cloud.GOG_Galaxy,Cloud.Discord,Cloud.Epic_Games_Launcher,Cloud.EA_Desktop,Cloud.OneDrive,Cloud.Ubisoft_Connect,Cloud.Xbox,Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Released,Infobox_game.Cover_URL&join_on=Infobox_game._pageID=Cloud._pageID&where=Infobox_game.Steam_AppID%20HOLDS%20%22" + "373420" + "%22&format=json")
cargo = r.json()['cargoquery']
steamcloud = 'Unknown'
pageID = 'Unknown'
q = ""
if len(cargo) > 0:
    steamcloud = cargo[0]['title']['Steam']
    pageID = cargo[0]['title']['PageID']
    q = requests.get("https://www.pcgamingwiki.com/w/api.php?action=parse&format=json&pageid=" + pageID + "&prop=wikitext")
print(q.json()['parse']['wikitext']['*'])
