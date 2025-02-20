from bs4 import BeautifulSoup

with open("lecturers.html", "rb") as lecturers_file:
    soup = BeautifulSoup(lecturers_file, "lxml")

div = soup.find("div", class_="divSelection")
lecturers = div.find_next("div", class_="divSelection").find_all("div", class_="li")

w_file = open("prep.txt", "w", encoding="utf-8")

for lecturer in lecturers:
    w_file.write(f"{lecturer.text} {lecturer.attrs["data"]} \n")
    print(lecturer.text, lecturer.attrs["data"])

