import requests
import random, string
from urllib3 import encode_multipart_formdata
import pandas as pd
from discord_webhook import DiscordWebhook, DiscordEmbed


def shorten(x, maxLen=75):
    if len(x) <= maxLen:
        return x
    else:
        return x[:maxLen-4] + " ..."


short_month = {"janvier": "jan",
               "fevrier": "fev",
               "février": "fev",
               "mars": "mar",
               "avril": "avr",
               "mai": "mai",
               "juin": "jun",
               "juillet": "jui",
               "aout": "aou",
               "août": "aou",
               "septembre": "sep",
               "octobre": "oct",
               "novembre": "nov",
               "decembre": "dec",
               "décembre": "dec"}


def format_date(d):
    date = d.replace("&nbsp", " ").split(" ")
    j = date[0]
    m = date[1]
    a = date[2]

    if m.lower() in short_month.keys():
        m = short_month[m.lower()]
    else:
        m = m[:3]

    return j + " " + m + " " + a[2:]

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


s.headers.update({"Content-Type": header})

postLogin = s.post("https://adum.fr/", data=body)
print(postLogin.status_code, postLogin.headers)


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

merged = merged[~((merged['modalite'].str.lower() == "présentiel") & (merged['ville'].str.lower() == "orléans"))]

is_open = merged['status'].str.lower() == "ouvert"
opened = merged[is_open]

opened = opened[~opened['titre'].str.contains("module master", case=False)]

# Formatting
opened["titre"] = opened["titre"].apply(shorten)
opened["ville"] = opened["ville"].apply(lambda x: shorten(x, maxLen=14))
opened["date"] = opened["date"].apply(format_date)

#opened.to_csv("data/out.csv")

txt = opened[["titre", "ville", "date", "modalite"]].to_markdown(showindex=False)
chunks = chunkify(txt, 1990)

for chunk in chunks:
    if len(chunk) > 0:
        webhook = DiscordWebhook(url=discord_url, content="```"+chunk+"```")
        response = webhook.execute()





