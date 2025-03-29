import toml, json
import requests
from bs4 import BeautifulSoup

# groups dictionary that will be writed in groups.toml
groups = {
    "groups": {}
}

with open("config.json", 'r') as f:
    cfg = json.load(f)
groups_main_url = cfg["links"]["s_group"]

response = requests.get(groups_main_url)
if response.status_code == 200:
    content = response.content
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find('table', class_='inf')

    for tr in table.find_all('tr'):
        for td in tr.find_all('td'):
            a = td.find('a', class_='z0')
            if a != None:
                # print(a.get('href') + '\t' + a.text)
                groups['groups'][a.text] = a.get('href')
    
    with open('groups.toml', 'w', encoding='utf-8') as file:
        toml.dump(groups, file)
                
else:
    print("[parser] > failed to load page! status code: " + str(response.status_code))
    exit(2)