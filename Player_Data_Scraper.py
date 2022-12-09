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
    sleep(randint(5,8))
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

def boxScoreUrls(url): #how to fix box scores issues with last game being included for some, you just search the html for last game. If it is found, you take [2:]. If not, you take [1:]
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
    #dfOfLinks = dfOfLinks.drop_duplicates()
    urlList = dfOfLinks.values.tolist()
    finalUrlList = ['https://www.baseball-reference.com' + str(i) for i in urlList]
    finalUrlList = [i.replace('[\'','') for i in finalUrlList]
    finalUrlList = [i.replace('\']','') for i in finalUrlList]
    return(finalUrlList)


def boxScoreUrlsPlayerData(url): #how to fix box scores issues with last game being included for some, you just search the html for last game. If it is found, you take [2:]. If not, you take [1:]
    res = requests.get(url, headers = {'User-agent': 'youaojsdoiajsdoijsado'})
    comm = re.compile("<!--|-->")
    soup = bs4.BeautifulSoup(comm.sub("", res.text), 'lxml')
    strong = soup.findAll('strong')
    booleanLastGame = False
    for s in strong:
        if str(s) == "<strong>Last Game:</strong>":
            booleanLastGame = True
            break
        else:
            booleanLastGame = False
    dataLink = []
    for link in soup.findAll('a'):
        if link.has_attr('href'):
            allLinks = link.attrs['href']
            dataLink.append(allLinks)
    r = re.compile("/boxes/\w\w\w/\w\w\w\d")  
    specificLink = list(filter(r.match, dataLink))
    dfOfLinks = pd.DataFrame(specificLink, columns=['url'])
    #dfOfLinks = dfOfLinks.drop_duplicates()
    urlList = dfOfLinks.values.tolist()
    finalUrlList = ['https://www.baseball-reference.com' + str(i) for i in urlList]
    finalUrlList = [i.replace('[\'','') for i in finalUrlList]
    finalUrlList = [i.replace('\']','') for i in finalUrlList]
    if booleanLastGame == True:
        finalUrlList = finalUrlList[2:]
    else:
        finalUrlList = finalUrlList[1:]
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
    for url in urls:
        print(url)
        allStarters = getStartingLineupInfo(url, teamAbbreviation)
        startingBatters = allStarters[0]['newPlayerName'].values.tolist()
        startingPitcher = allStarters[1]['newPlayerName'].values.tolist()
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

def pullPitcherData(playerLink):
    df = pullTable(playerLink,"pitching_gamelogs")
    boxScores = boxScoreUrlsPlayerData(playerLink)
    df = df[df.ERA != "Pit"]
    df.drop(df.tail(1).index,inplace=True)
    pattern = "Play\w+"
    filter = df['Tm'].str.contains(pattern)
    df = df[~filter]
    df = df.reset_index()
    df['boxScores'] = boxScores
    df = df.drop(['index'],axis=1)
    return df

def pullBatterData(playerLink):
    df = pullTable(playerLink,"batting_gamelogs")
    boxScores = boxScoreUrlsPlayerData(playerLink)
    df = df[df.Opp != "Rslt"]
    df.drop(df.tail(1).index,inplace=True) #need to account for trades, so also drop 
    pattern = "Play\w+"
    filter = df['Tm'].str.contains(pattern)
    df = df[~filter]
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
    credentials = boto3.client('s3', aws_access_key_id = access_key, 
                          aws_secret_access_key= secret_access_key) 
    for link in links:
        playerName = re.findall("id=\w+&",link)
        playerName = str(playerName)
        playerName= playerName[5:-3]
        print(link)
        data = pullPitcherData(link)
        data.to_csv(year + '_' + playerName + '_Pitching_Logs.csv')
        credentials.upload_file(Filename = year + '_' + playerName + '_Pitching_Logs.csv', Bucket = 'mlbplayerdata', Key = year + '_' + playerName + '_Pitching_Logs.csv')


def uploadStartingBatterData(teamAbbreviation, year):
    links = getStartingPlayerLinks(teamAbbreviation, year)[0]
    credentials = boto3.client('s3', aws_access_key_id = access_key, 
                          aws_secret_access_key= secret_access_key) 
    for link in links:
        playerName = re.findall("id=\w+&",link)
        playerName = str(playerName)
        playerName= playerName[5:-3]
        print(link)
        data = pullBatterData(link)
        data.to_csv(year + '_' + playerName + '_Batting_Logs.csv')
        credentials.upload_file(Filename = year + '_' + playerName + '_Batting_Logs.csv', Bucket = 'mlbplayerdata', Key = year + '_' + playerName + '_Batting_Logs.csv')


uploadStartingPitcherData("ATL","2021")

#pullTable("https://www.baseball-reference.com/players/gl.fcgi?id=youngal01&t=p&year=2021",)
