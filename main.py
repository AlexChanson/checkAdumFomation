import requests
import random, string
from urllib3 import encode_multipart_formdata
import pandas as pd
from discord_webhook import DiscordWebhook, DiscordEmbed

def chunkify(txt, limit=2000):
    chunks = []
    roll_over = ""
    current = ""
    for line in txt.split("\n"):
        line = line.strip()
        if len(roll_over) > 0:
            current = current + roll_over
            roll_over = ""
        if len(line) + len(current) > limit - 1:
            chunks.append(current)
            current = ""
            roll_over = line
        else:
            current = current + "\n" + line
    chunks.append(current)
    if len(roll_over) > 0:
        chunks.append(roll_over)
    return chunks


s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'})


getLogin = s.get('https://adum.fr/')
print(getLogin.status_code, getLogin.headers)

with open("secrets.txt") as f:
    email = f.readline().strip()
    password = f.readline().strip()
    discord_url = f.readline().strip()


payload = {'action': "login", 'email':email,'password':password, "matFormation":"",  "anneeEnCours":"2022"}
boundary = '----WebKitFormBoundary' \
           + ''.join(random.sample(string.ascii_letters + string.digits, 16))
body, header = encode_multipart_formdata(payload, boundary=boundary)
#print(header)
#print("-----------------------------")
#print(str(body, encoding='utf-8'))
#print("-----------------------------")

s.headers.update({"Content-Type": header})

postLogin = s.post("https://adum.fr/", data=body)
print(postLogin.status_code, postLogin.headers)
#print(postLogin.text)


payload = {'action': "enterAccount|0"}
boundary = '----WebKitFormBoundary' \
           + ''.join(random.sample(string.ascii_letters + string.digits, 16))
body, header = encode_multipart_formdata(payload, boundary=boundary)
s.headers.update({"Content-Type": header})

postAcc = s.post("https://adum.fr/", data=body)
print(postAcc.status_code, postAcc.headers)

getCatalog = s.get("https://adum.fr/phd/formation/catalogue.pl")
print(getCatalog.status_code, getCatalog.headers)

dfs = pd.read_html(getCatalog.text)
dfs = dfs[:-1]

merged = pd.concat(dfs)
merged.columns = ["titre", "ville", "date", "modalite", "status", "places"]

merged = merged[~((merged['modalite'] == "Présentiel") & (merged['ville'] == "Orléans"))]

is_open = merged['status'] == "Ouvert"
opened = merged[is_open]
opened["date"] = opened["date"].apply(lambda x: x.replace("&nbsp", " "))

opened.to_csv("data/out.csv")

txt = opened[["titre", "ville", "date", "modalite"]].to_markdown(showindex=False)
#chunks = [txt[i:i+n] for i in range(0, len(txt), 1990)]
chunks = chunkify(txt, 1999)

for chunk in chunks:
    webhook = DiscordWebhook(url=discord_url, content=chunk)
    response = webhook.execute()





