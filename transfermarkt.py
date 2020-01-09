import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

class Player:
    def getData(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
        response = requests.get(url, headers=headers)

        # Criando soup
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find("div", {"class": "responsive-table"}).text.replace("\n", "").strip() != 'No information':
            li = []

            # As <div class='box'> são aonde ficam os tabelas com os dados dos jogos.
            for box in soup.find_all('div', {"class": "box"})[1:]:

                '''
                    Adicionando o nome da  liga, que está dentro de <div class="'table-header img-vat">, a linha a ser adicionada ao df
                    O Try: é necessário pois, nem todos os <div class='box'> são utilizados para guardar tabelas com os dados que queremos, então,
                    os que queremos possuem a tag, <div class='table-header img-vat'>, que é aonde fica o nome da liga que estarão os dados
                '''
                try:
                    league = box.find('div', {'class': 'table-header img-vat'}).text.strip()
                except:
                    pass
                else:
                    table = box.find('table')
                    jogosValores = []
                    for jogo in table.find('tbody').find_all('tr'):
                        row = [league]
                        
                        for coluna in jogo.find_all('td'):
                            if ''.join(coluna.text.split()) != '':
                                row.append(coluna.text.strip())
                            else:
                                row.append(str(coluna.find('img')))

                        if len(row) >= 15:
                            jogosValores.append(row)

                    header = ['competition', 'matchday', 'date', 'venue', 'team', 'opponent', 'result', 'position', 'goals', 'assists', 'yellow', 'secondYellow', 'red', 'minutesPlayed']

                    if jogosValores != []:
                        df = pd.DataFrame(jogosValores) 
                        if len(df.columns) == 16:
                            df = df.drop([5, 7], axis = 1)  
                        else:
                            df = df.drop([6], axis = 1)  #Removendo colunas descessárias
                        df.columns = header


                        #Removing games that the player did not play. If columns minutesPlayed is null, means player dont play that match.
                        df = df[pd.notnull(df['minutesPlayed'])]
                        
                        
                        df['date'] = pd.to_datetime(df['date'])
                        
                        #replacing none values with 0 and converting all values from string to number
                        df['goals'].replace('None', 0, inplace=True)
                        df['assists'].replace('None', 0, inplace=True)
                        df['goals'] = pd.to_numeric(df['goals'])
                        df['assists'] = pd.to_numeric(df['assists'])
                        
                        
                        df.replace('None', np.nan, inplace=True)

                        #Sorting values by date columns
                        df.sort_values(by=['date'], inplace=True)
                        
                        #getting name of the teams from a img tag
                        teams = []
                        oponnent = []
                        for index, row in df.iterrows():
                            img = BeautifulSoup(row['team']).find('img')
                            teams.append(img['alt'])
                            img = BeautifulSoup(row['opponent']).find('img')
                            oponnent.append(img['alt'])
                        df['team'] = teams
                        df['opponent'] = oponnent

                        df['minutesPlayed'] = pd.to_numeric(df['minutesPlayed'].str[:-1])
                        
                        li.append(df)


            return pd.concat(li, axis=0, ignore_index=True)
    
    def performance(self, by):
        stats = self.df.groupby(by).sum()
        stats['appearances'] = self.df.groupby(by)[by].count()
        stats = stats[['appearances', 'goals', 'assists', 'minutesPlayed']]
        stats.sort_values('appearances', ascending=False)
        return stats
    
    def matches(self, competition='', opponent='', date=''):
        return self.df.loc[(self.df['competition'].str.contains('^'+competition, na=False)) & 
                            (self.df['opponent'].str.contains('^'+opponent, na=False)) & 
                            (self.df['date'].astype(str).str.contains('^'+str(date), na=False))]
                
    
    def __init__(self, playerId):
        dados = []
        url = 'https://www.transfermarkt.com/-/leistungsdatendetails/spieler/' + str(playerId) + '/plus/0?saison=&verein=&liga=1&wettbewerb=&pos=&trainer_id='
        dados.append(self.getData(url))
        for i in range(8, 14):
            url = 'https://www.transfermarkt.com/-/leistungsdatendetails/spieler/' + str(playerId) + '/plus/0?saison=&verein=&liga=' + str(i) + '&wettbewerb=&pos=&trainer_id='
            dados.append(self.getData(url))
        
        self.df = pd.concat(dados, axis=0, ignore_index=True)

        #Sorting values by date columns
        #self.df.sort_values(by=['date'], inplace=True)