import requests
import bs4
import pandas as pd
import re
from time import sleep
from random import randint
import boto3
from access_keys import access_key, secret_access_key
import io

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

def getStartingLineupInfo(boxScoreUrl, teamAbbreviation):
    sleep(randint(5,10))
    links = []
    res = requests.get(boxScoreUrl)
    comm = re.compile("<!--|-->")
    soup = bs4.BeautifulSoup(comm.sub("", res.text), 'lxml')
    homeTeamAbbreviation = boxScoreUrl[45:48]
    if teamAbbreviation == homeTeamAbbreviation:
        divs = soup.find('div', id = "lineups_2")
    else:
        divs = soup.find('div', id = "lineups_1")
    
    data_rows = divs.findAll('tr')
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

    for tr in data_rows:
        cols = tr.findAll('td')
        link = cols[1].find('a').get('href')
        links.append(link)
    df['links'] = links
    newPlayerName = []
    for i in range(len(df['links'])):
        regex = re.findall("/\w/\w{3,}",df['links'][i])
        newPlayerName.append(regex)
    df['newPlayerName'] = newPlayerName
    df['newPlayerName'] = df['newPlayerName'].astype(str)
    df['newPlayerName'] = df['newPlayerName'].str[5:-2]
    for i in range(len(df['playerName'])):
        if df['battingOrder'][i] == '':
            df['battingOrder'][i] = '20'
    dfBatters = df.head(9)
    dfPitcher = df.loc[(df['playerPosition'] == 'P')]
    return dfBatters, dfPitcher

def getListOfAllStarters(scheduleUrl, teamAbbreviation): 
    listOfUniqueBatters = []
    listOfUniquePitchers = []
    listOfBatters = []
    listOfPitchers = []
    urls = boxScoreUrls(scheduleUrl) #https://www.baseball-reference.com/boxes/COL/COL202207280.shtml this one doesn't have a pitcher
    #urls = urls[:10]
    for url in urls:
        print(url)
        startingBatters = getStartingLineupInfo(url, teamAbbreviation)[0]['newPlayerName'].values.tolist()
        startingPitcher = getStartingLineupInfo(url, teamAbbreviation)[1]['newPlayerName'].values.tolist()
        listOfBatters.append(startingBatters)
        listOfPitchers.append(startingPitcher)
    for x in listOfBatters:
        for batter in x:
            if batter not in listOfUniqueBatters:
                listOfUniqueBatters.append(batter)

    for z in listOfPitchers:
        for pitcher in z:
            if pitcher not in listOfUniquePitchers:
                listOfUniquePitchers.append(pitcher)


    return listOfUniqueBatters, listOfUniquePitchers



def uploadStarterList(scheduleUrl, teamAbbreviation, year):
    uniqueStarters = getListOfAllStarters(scheduleUrl, teamAbbreviation)
    uniqueBatters = uniqueStarters[0]
    uniquePitchers = uniqueStarters[1]
    dfBatters = pd.DataFrame()
    dfPitchers= pd.DataFrame()
    dfBatters['Batters'] = uniqueBatters
    dfPitchers['Pitchers'] = uniquePitchers
    dfBatters.to_csv(year + '_' + teamAbbreviation + "_Batters.csv")
    dfPitchers.to_csv(year + '_' + teamAbbreviation + "_Pitchers.csv")
    dfBatters = pd.read_csv(year + '_' + teamAbbreviation + "_Batters.csv")
    dfPitchers = pd.read_csv(year + '_' + teamAbbreviation + "_Pitchers.csv")
    credentials = boto3.client('s3', aws_access_key_id = access_key, 
                          aws_secret_access_key= secret_access_key) 
    credentials.upload_file(Filename = year + '_' + teamAbbreviation + '_Batters.csv', Bucket = 'mlbplayerdata', Key = year + '_' + teamAbbreviation + '_Batters.csv')
    credentials.upload_file(Filename = year + '_' + teamAbbreviation + '_Pitchers.csv', Bucket = 'mlbplayerdata', Key = year + '_' + teamAbbreviation + '_Pitchers.csv')


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
    sleep(randint(4,8))
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

def getStartingPlayerLinks(teamAbbreviation, year):
    batterGameLogLinks = []
    pitcherGameLogLinks = []
    credentials = boto3.client('s3', aws_access_key_id = access_key, 
                          aws_secret_access_key= secret_access_key) 
    batters = credentials.get_object(Bucket='mlbplayerdata', Key= year + '_' + teamAbbreviation + '_Batters.csv')
    dfBatters = pd.read_csv(io.BytesIO(batters['Body'].read()))
    pitchers = credentials.get_object(Bucket='mlbplayerdata', Key= year + '_' + teamAbbreviation + '_Pitchers.csv')
    dfPitchers = pd.read_csv(io.BytesIO(pitchers['Body'].read()))
    for i in range(len(dfBatters)):
        batterGameLogLinks.append("https://www.baseball-reference.com/players/gl.fcgi?id=" + dfBatters['Batters'][i] + "&t=b" + "&year=" + year)
    for i in range(len(dfPitchers)):
        pitcherGameLogLinks.append("https://www.baseball-reference.com/players/gl.fcgi?id=" + dfPitchers['Pitchers'][i] + "&t=p" + "&year=" + year)
    return batterGameLogLinks, pitcherGameLogLinks

def uploadStartingPitcherData(teamAbbreviation, year):
    links = getStartingPlayerLinks(teamAbbreviation, year)[1]
    links = links[:3]
    for link in links:
        data = pullPitcherData(link)
        print(data)

#print(getStartingPlayerLinks("ARI","2021")[1])
print(uploadStartingPitcherData("ARI","2021"))
#uploadStarterList("https://www.baseball-reference.com/teams/ARI/2021-schedule-scores.shtml","ARI", "2021")
#request = requests.get("https://www.baseball-reference.com/teams/LAD/2022-schedule-scores.shtml")
#print(request)  
