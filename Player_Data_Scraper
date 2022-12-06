import requests
import bs4
import pandas as pd
import re
from time import sleep
from random import randint

def findTables(url):
    res = requests.get(url)
    comm = re.compile("<!--|-->")
    soup = bs4.BeautifulSoup(comm.sub("", res.text), 'lxml')
    divs = soup.findAll('div', id = "content")
    divs = divs[0].findAll("div", id=re.compile("^all"))
    ids = []
    for div in divs:
        searchme = str(div.findAll("table"))
        x = searchme[searchme.find("id=") + 3: searchme.find(">")]
        x = x.replace("\"", "")
        if len(x) > 0:
            ids.append(x)
    return(ids)

def pullTable(url, tableID):
    res = requests.get(url)
    sleep(randint(1,5))
    comm = re.compile("<!--|-->")
    soup = bs4.BeautifulSoup(comm.sub("", res.text), 'lxml')
    tables = soup.findAll('table', id = tableID)
    data_rows = tables[0].findAll('tr')
    data_header = tables[0].findAll('thead')
    data_header = data_header[0].findAll("tr")
    data_header = data_header[0].findAll("th")
    game_data = [[td.getText() for td in data_rows[i].findAll(['th','td'])]
        for i in range(len(data_rows))
        ]
    data = pd.DataFrame(game_data)
    header = []
    for i in range(len(data.columns)):
        header.append(data_header[i].getText())
    data.columns = header
    data = data.loc[data[header[0]] != header[0]]
    data = data.reset_index(drop = True)
    return(data)

def boxScoreUrls(url):
    sleep(randint(1,5))
    res = requests.get(url, headers = {'User-agent': 'youaojsdoiajsdoijsado'})
    comm = re.compile("<!--|-->")
    soup = bs4.BeautifulSoup(comm.sub("", res.text), 'lxml')
    dataLink = []
    for link in soup.findAll('a'):
        if link.has_attr('href'):
            allLinks = link.attrs['href']
            dataLink.append(allLinks)
    r = re.compile("/boxes/\w\w\w/\w\w\w\d")  
    specificLink = list(filter(r.match, dataLink))
    dfOfLinks = pd.DataFrame(specificLink, columns=['url'])
    dfOfLinks = dfOfLinks.drop_duplicates()
    urlList = dfOfLinks.values.tolist()
    finalUrlList = ['https://www.baseball-reference.com' + str(i) for i in urlList]
    finalUrlList = [i.replace('[\'','') for i in finalUrlList]
    finalUrlList = [i.replace('\']','') for i in finalUrlList]
    return(finalUrlList)


def getStartingLineupInfo(boxScoreUrl):
    links = []
    res = requests.get(boxScoreUrl)
    comm = re.compile("<!--|-->")
    soup = bs4.BeautifulSoup(comm.sub("", res.text), 'lxml')
    find = soup.find(class_ = "data_grid_group solo")
    data_rows = find.findAll('tr')
    game_data = [[td.getText() for td in data_rows[i].findAll(['th','td'])]
        for i in range(len(data_rows))
        ]
    playerName = [el[1] for el in game_data]
    playerPosition = [el[2] for el in game_data]
    battingOrder = [el[0] for el in game_data]
    df = pd.DataFrame()
    df['playerName'] = playerName
    df['playerPosition'] = playerPosition
    df['battingOrder'] = battingOrder


    findLink = soup.find(class_ = "data_grid_group solo")
    rows = findLink.findAll('tr')
    for tr in rows:
        cols = tr.findAll('td')
        link = cols[1].find('a').get('href')
        links.append(link)
    df['links'] = links
    df['newPlayerName'] = df['links'].str[11:]
    df['newPlayerName'] = df['newPlayerName'].str[:7]
    for i in range(len(df['playerName'])):
        if df['battingOrder'][i] == '':
            df['battingOrder'][i] = '20'
    return df

def getPlayerStatsLink(boxScoreUrl, year): #just get the batting data for every 
    batterGameLogLinks = []
    pitcherGameLogLinks = []
    df = getStartingLineupInfo(boxScoreUrl)
    for i in range(len(df['newPlayerName'])): 
        if df['battingOrder'][i] == '20' and df['playerPosition'][i] == 'P':
            pitcherGameLogLinks.append("https://www.baseball-reference.com/players/gl.fcgi?id=" + df['newPlayerName'][i] + "01&t=p" + "&year=" + year)
        else:
            batterGameLogLinks.append("https://www.baseball-reference.com/players/gl.fcgi?id=" + df['newPlayerName'][i] + "01&t=b" + "&year=" + year)
    return pitcherGameLogLinks, batterGameLogLinks

def pullPitcherData(playerLink):
    df = pullTable(playerLink,"pitching_gamelogs")
    boxScores = boxScoreUrls(playerLink)
    boxScores = boxScores[1:] #one thing you can consider is shifting this by 1 so that you have a new variable "boxScoreOfNextGame" then you just use that to combine
    df = df[df.ERA != "Pit"]
    df.drop(df.tail(1).index,inplace=True)
    df = df.reset_index()
    df['boxScores'] = boxScores
    df = df.drop(['index'],axis=1)
    return df

def pullBatterData(playerLink):
    df = pullTable(playerLink,"batting_gamelogs")
    boxScores = boxScoreUrls(playerLink)
    boxScores = boxScores[1:] #one thing you can consider is shifting this by 1 so that you have a new variable "boxScoreOfNextGame" then you just use that to combine
    df = df[df.Opp != "Rslt"]
    df.drop(df.tail(1).index,inplace=True)
    df = df.reset_index()
    df['boxScores'] = boxScores
    df = df.drop(['index'],axis=1)
    return df


def getListOfAllStarters(scheduleUrl): 
    listOfUniqueStarters = []
    listOfStarters = []
    urls = boxScoreUrls(scheduleUrl)
    for i in range(len(urls)):
        startingLineup = getStartingLineupInfo(urls[i])['newPlayerName'].values.tolist()
        listOfStarters.append(startingLineup)
    for x in listOfStarters:
        for y in x:
            if y not in listOfUniqueStarters:
                listOfUniqueStarters.append(y)
    return listOfUniqueStarters

request = requests.get("https://www.baseball-reference.com/teams/LAD/2022-schedule-scores.shtml")
print(request)  
