from bs4 import BeautifulSoup

with open("groups.html", "rb") as groups_file:
    soup = BeautifulSoup(groups_file, "lxml")

div = soup.find("div", class_="divSelection")
groups = div.find_all("div", class_="li")

w_file = open("gru.txt", "w", encoding="utf-8")

for group in groups:
    w_file.write(f"{group.text} {group.attrs["data"]} \n")
    print(group.text, group.attrs["data"])

