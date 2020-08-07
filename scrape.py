import json
import re
import requests
from bs4 import BeautifulSoup

MIN_ID, MAX_ID = 1, 27633

def scrape(skip=False):
    outfile = open("nber-data.json", "w")
    errors = {}
    for i in range(MIN_ID, MAX_ID):
        print(i, end=" ")
        try:
            d, e = get_text(i)
            outfile.write(json.dumps(d) + "\n")
            errors[i] = e
            print("y" if e else "n")
        except RuntimeError:
            errors[i] = ["bad_request"]
            print("n")
    outfile.close()
    with open("errors.json", "w") as f:
        json.dump(errors, f)

def get(i):
    out = {}
    out["id"] = i
    errors = []

    url = "https://www.nber.org/papers/w" + str(i)
    r = requests.get(url)
    if r.status_code != 200:
        raise RuntimeError(f"Status Code: {r.status_code}")
    soup = BeautifulSoup(r.text, features="html5lib")

    title = soup.find("h1", class_="title citation_title")
    out["title"] = title.text.strip()

    authors = soup.find("h2", class_="bibtop citation_author")
    out["author_str"] = authors.text.split(", ")
    out["author_id"] = [a['href'][8:] for a in authors.find_all("a")]
    if len(out["author_str"]) != len(out["author_id"]):
        errors.append("author_len")

    bibtop = soup.find("p", class_="bibtop")
    lines = bibtop.find_all("b")
    if lines[0].string[23:] != str(i):
        errors.append("id_mismatch")
    dates = lines[1].text
    out["issue_date"] = dates.split(", ")[0][10:] if ',' in dates else dates[10:]
    out["revise_date"] = dates.split(", ")[1][11:] if ',' in dates else None
    if len(out["issue_date"].split()) != 2:
        errors.append("issuedate_fail")
    if out["revise_date"] is not None and len(out["revise_date"].split()) != 2:
        errors.append("revisedate_fail")
    if len(lines) > 2:
        out["programs"] = [a["href"][34:-5] for a in lines[2].find_all("a")]
        if any(len(s) != 2 for s in out["programs"]):
            errors.append("programs_fail")
    else:
        out["programs"] = []
        errors.append("programs_empty")
    
    out["abstract"] = bibtop.next_sibling.next_sibling.text.strip()

    return out, errors

if __name__ == "__main__":
    scrape()
