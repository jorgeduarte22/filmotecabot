import io
import json
import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler
from telegram.ext import Updater
from scrapper import getFilms
import datetime
import os

#TODO Handle exceptions
#TODO Sort the imported json by id
#TODO Use mutual exclusion to update the database

BOT_TOKEN = os.environ["FILMOTECABOT_KEY"]
NUMBER_OF_RESULTS = 50
CACHE_TIME = 60*60
UPDATE_TIME = 6*60*60
film_db = []

print(BOT_TOKEN)

def open_database():
	db = io.open("Cartelera.json", mode="r", encoding="utf-8")
	content = json.loads(db.read())
	db.close()
	return content

def findString(query, f):
	s = query.lower()
	if not s:
		return True

	if s in f["title"].lower():
		return True
	if s in f["day"].lower():
		return True
	if s in f["hour"].lower():
		return True
	if "year" in f and s in f["year"].lower():
		return True
	if "directors" in f and s in f["directors"].lower():
		return True
	return False

def inline_catalog(bot, update):
	print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), " - Request from ", update.effective_user.id)

	query = update.inline_query.query
	results = list()

	for i, f in enumerate(film_db["list"]):
		if findString(query, f):

			#print("VALIDO ", f["title"])

			title = f["title"]
			if "year" in f:
				title += " ("+f["year"]+")"
			if "directors" in f:
				title += " - "+f["directors"]

			message_content = "<b>"+title+"</b>\nFecha: "+f["day"]+", "+f["hour"]+"\nNota filmaffinity: "
			
			if "avg" in f:
				message_content += f["avg"]
			else:
				message_content += "-"

			message_content += "\nMás información: "+f["url"]

			#print("ID: ", f["id"], " ", int(f["id"]))

			results.append(
				InlineQueryResultArticle(
					id=int(f["id"]),
					title=title,
					input_message_content=InputTextMessageContent(message_content, parse_mode="html"),#TODO Refinar el mensaje y dar informacion interesante como la url del evento en la filmoteca
					description=(f["day"]+", "+f["hour"]),
					thumb_url=f["img"]
				)
			)

		if len(results) == NUMBER_OF_RESULTS:
			break
	if(len(results) == 0):
		results.append(
			InlineQueryResultArticle(
				id=1,
				input_message_content=InputTextMessageContent("Ninguna película encontrada"),
				title="No hay resultados"
			)
		)
	bot.answer_inline_query(update.inline_query.id, results, cache_time=CACHE_TIME)

film_db = open_database()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher

dispatcher.add_handler(InlineQueryHandler(inline_catalog))

def uploadDatabase(bot, job):
	print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), " - Scrapping...")
	getFilms()
	film_db = open_database()
	print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), " - Database loaded.")

job_q = updater.job_queue
job_q.run_repeating(uploadDatabase, interval=UPDATE_TIME, first=datetime.time(13,0,0,0))
job_q.start()

updater.start_polling()
updater.idle()

job_q.stop()