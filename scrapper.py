import requests
from bs4 import BeautifulSoup
import io
import json
import re

#TODO Make the database refresh every 24 hours

def getYear(url):
	r = requests.get(url)
	year_soup = BeautifulSoup(r.text, "html.parser")
	year_tag = str(year_soup.find("div", {"class": "content two-col"}).find_all("p")[2])
	expr = "((19|20)\d{2})"
	year_match = re.search(expr, year_tag)
	if not year_match:
		year_tag = str(year_soup.find("div", {"class": "content two-col"}).find_all("p")[3])
		year_match = re.search(expr, year_tag)

		if not year_match:
			return year_match

	return year_match.group()

def getFilms():
	url = "http://www.filmotecamurcia.es"
	filmaffinity = "https://www.filmaffinity.com"
	filmaffinity_search = filmaffinity+ "/es/search.php?stext="
	r = requests.get(url)

	filmoteca_soup = BeautifulSoup(r.text, "html.parser")
	prog_url = url+filmoteca_soup.find(id="main-menu").find_all("a")[2].get("href")
	final_list = {"list":[]}

	identifier = 0

	while True:
		#print(prog_url)
		r = requests.get(prog_url)

		filmoteca_soup = BeautifulSoup(r.text, "html.parser")
		films = filmoteca_soup.find(id="events-container")

		for f in films.find_all("a"):
			info = {}
			info["id"] = identifier
			identifier += 1
			info["title"] = f.find("h3").string
			info["day"] = f.find_all("p")[0].string
			info["hour"] = f.find_all("p")[1].string.replace(" ", "")

			info["url"] = url+f.get("href")
			year = getYear(info["url"])
			if year:
				info["year"] = year

			img_tag = f.find("div", {"class", "thumb-container"}).find("div").get("style")
			info["img"] = url+img_tag[img_tag.find("(")+1:img_tag.find(")")]


			#-------------------Filmaffinity-------------------

			r = requests.get(filmaffinity_search+info["title"])
			#print(r.text)
			filmaffinity_soup = BeautifulSoup(r.text, "html.parser")
			
			title = None

			if "year" in info:
				film_slots = filmaffinity_soup.find_all("div", {"class": "se-it mt "})
				for slot in film_slots:
					film_year = slot.find("div", {"class": "ye-w"}).string
					if film_year == info["year"]:
						title = slot.find("div", {"class": "mc-title"})
			else:
				title = filmaffinity_soup.find("div", {"class": "mc-title"})

			if title:
				film_url = filmaffinity+title.find("a").get("href")
				#print("Direccion: ", film_url)
				r = requests.get(film_url)
				filmaffinity_soup = BeautifulSoup(r.text, "html.parser")

				#-------------------Film page-------------------
			film_info = filmaffinity_soup.find("dl", {"class": "movie-info"})
			if film_info:
				info["year"] = film_info.find("dd", {"itemprop": "datePublished"}).string.strip()
				directors = ""
				for i, d in enumerate(film_info.find("dd", {"class": "directors"}).find_all("span", {"itemprop": "name"})):
					if i != 0:
						directors += ", "
					directors += d.string
				info["directors"] = directors
				info["avg"] = "-"
				avgTag = filmaffinity_soup.find("div", {"itemprop": "ratingValue"})
				if avgTag:
					info["avg"] = avgTag["content"]

			final_list["list"].append(info)

		next_tag = filmoteca_soup.find(id="Siguiente")
		if not next_tag:
			break
		prog_url = url+next_tag.get("href")


	with io.open("Cartelera.json", mode="w", encoding="utf-8") as file:
		file.write(json.dumps(final_list, indent=2, ensure_ascii=False))
		file.close()