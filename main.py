#----------------------------------
# Developer: Digital Entropy
# Program: Telegram-based Smart Home
# (c) Digital Entropy 2016
# License: Proprietary Software
#-----------------------------------
from __future__ import unicode_literals
import logging

import vlc
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC, WPUB, WOAF, WOAR, WOAS, WORS, TENC, TPUB, TRSN, USLT, TYER, TOPE, TOAL, TCOM, WCOM
from mutagen.easyid3 import EasyID3
from random import randint
import time
import urllib.request
from uuid import uuid4
from time import sleep
from subprocess import call

import gc
import requests
import datetime

from telegram import Emoji, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ReplyKeyboardMarkup, KeyboardButton, InlineQueryResultArticle, InlineQueryResultPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler, Filters
from telegram.ext.dispatcher import run_async

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
						   '%(message)s',
					level=logging.INFO)

superusers = [47571378] #Admin user_id
playkeyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅", callback_data = '⬅'), InlineKeyboardButton("Pause", callback_data = 'Pause'), InlineKeyboardButton("➡", callback_data = '➡')], [InlineKeyboardButton("-", callback_data = '-'), InlineKeyboardButton("Stop", callback_data = 'Stop'), InlineKeyboardButton("+", callback_data = '+')], [InlineKeyboardButton("Random", callback_data = 'Random')]])
stockkeyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅", callback_data = '⬅'), InlineKeyboardButton("Play", callback_data = 'Play'), InlineKeyboardButton("➡", callback_data = '➡')], [InlineKeyboardButton("-", callback_data = '-'), InlineKeyboardButton("Random", callback_data = 'Random'), InlineKeyboardButton("+", callback_data = '+')]])
pausekeyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Resume", callback_data = 'Resume')], [InlineKeyboardButton("-", callback_data = '-'), InlineKeyboardButton("Stop", callback_data = 'Stop'), InlineKeyboardButton("+", callback_data = '+')], [InlineKeyboardButton("Random", callback_data = 'Random')]])

volume = round(((int(os.popen("osascript -e 'set ovol to output volume of (get volume settings)'").read())) / 10)) #Get current volume (macOS)
print(volume)

gc.enable() #Garbage collector

def random():
	global track_id
	track_id = randint(1, 23)

def track():
	global track_id
	global file
	global p
	try:
		file = "tracks/%i.mp3" % track_id
	except:
		try:
			track_id -= 1
			file = "tracks/%i.mp3" % track_id
		except:
			track_id += 1
			file = "tracks/%i.mp3" % track_id
	p = vlc.MediaPlayer(file)

@run_async
def player(bot, update, chat_id = None, message_id = None):
	global artist
	global title
	if chat_id == None:
		chat_id = update.message.chat_id
		rmark = stockkeyboard
	else:
		rmark = None
		message_id -= 1
	if chat_id in superusers:

		filename = file
		mp3info = EasyID3(filename)
		data = mp3info.items()
		artist = replaceData(data, 'artist')
		title = replaceData(data, 'title')
		bot.sendMessage(chat_id, text = 'Hey!\n `Creator:`@ev3rest\n\n*%s. %s* - %s' % (str(track_id), str(artist), str(title)), reply_markup = rmark, parse_mode = ParseMode.MARKDOWN)
	else:
		bot.sendMessage(chat_id, text = 'You are not `sudo`. Contact @ev3rest', parse_mode = ParseMode.MARKDOWN)

@run_async
def edit(bot, update, chat_id = None, message_id = None):
	global artist
	global title
	rmark=playkeyboard
	filename = file
	mp3info = EasyID3(filename)
	data = mp3info.items()
	artist = replaceData(data, 'artist')
	title = replaceData(data, 'title')
	try:
		bot.editMessageText(message_id = message_id, chat_id = chat_id, text = 'Hey!\n `Creator:`@ev3rest\n\n*%s. %s* - %s' % (str(track_id), str(artist), str(title)), reply_markup = rmark, parse_mode = ParseMode.MARKDOWN)
	except:
		pass
	p.play()

@run_async
def nextt(bot, update, chat_id = None, message_id = None):
	global track_id
	track_id += 1
	p.stop()
	track()
	edit(bot, update, chat_id, message_id)

@run_async
def prev(bot, update, chat_id = None, message_id = None):
	global track_id
	track_id -= 1
	p.stop()
	track()
	edit(bot, update, chat_id, message_id)

@run_async
def play(bot, update, chat_id = None, message_id = None):
	try:
		bot.editMessageReplyMarkup(chat_id, message_id, reply_markup = playkeyboard)
	except:
		bot.editMessageReplyMarkup(chat_id, message_id + 1, reply_markup = playkeyboard)
	p.play()

@run_async
def pause(bot, update, chat_id = None, message_id = None):
	bot.editMessageReplyMarkup(chat_id, message_id, reply_markup = pausekeyboard)
	p.pause()

@run_async
def resume(bot, update, chat_id = None, message_id = None):
	bot.editMessageReplyMarkup(chat_id, message_id, reply_markup = playkeyboard)
	p.pause()

@run_async
def stop(bot, update, chat_id = None, message_id = None):
	bot.editMessageReplyMarkup(chat_id, message_id, reply_markup = stockkeyboard)
	p.stop()

@run_async
def volumeup(bot, update, chat_id = None, query_id = None): #This will only work on macOS
	global volume
	if volume < 10:
		volume += 1
	os.system('osascript -e "set Volume %s"' % volume)
	bot.answerCallbackQuery(callback_query_id = query_id, chat_id = chat_id, show_alert = False, text = "Volume: " + str(volume * 10) + "%")

@run_async
def volumedown(bot, update, chat_id = None, query_id = None): #This will only work on macOS
	global volume
	if volume < 10:
		volume -= 1
	os.system('osascript -e "set Volume %s"' % volume)
	bot.answerCallbackQuery(callback_query_id = query_id, chat_id = chat_id, show_alert = False, text = "Volume: " + str(volume * 10) + "%")


@run_async
def text(bot, update):
	global track_id
	if int(update.message.text) > 0: #Keyboard handler
		track_id = int(update.message.text)
		p.stop()
		track()
		player(bot, update, message_id = update.message.message_id)
		play(bot, update, chat_id = update.message.chat_id, message_id = update.message.message_id)
	else:
		print('Nope')

@run_async
def callback(bot, update): #Callback handler
	query = update.callback_query
	if query.data == "Play":
		play(bot, update, chat_id = query.message.chat_id, message_id = query.message.message_id - 1)
	elif query.data == "Stop":
		stop(bot, update, chat_id = query.message.chat_id, message_id = query.message.message_id)
	elif query.data == "Pause":
		pause(bot, update, chat_id = query.message.chat_id, message_id = query.message.message_id)
	elif query.data == "Resume":
		resume(bot, update, chat_id = query.message.chat_id, message_id = query.message.message_id)
	elif query.data == "➡":
		nextt(bot, update, chat_id = query.message.chat_id, message_id = query.message.message_id)
	elif query.data == "⬅":
		prev(bot, update, chat_id = query.message.chat_id, message_id = query.message.message_id)
	elif query.data == "Random":
		random()
		p.stop()
		track()
		edit(bot, update, chat_id = query.message.chat_id, message_id = query.message.message_id)
	elif query.data == "-":
		volumedown(bot, update, query_id = query.id)
	elif query.data == "+":
		volumeup(bot, update, query_id = query.id)

@run_async
def error(bot, update, error):
	logging.warning('Update "%s" caused error "%s"' % (update, error))

def main():
	random()
	track()
	token = "TOKEN"
	updater = Updater(token, workers = 5)

	updater.dispatcher.add_handler(CommandHandler('player', player))
	updater.dispatcher.add_handler(CommandHandler('play', play))
	updater.dispatcher.add_handler(CommandHandler('pause', pause))
	updater.dispatcher.add_handler(CommandHandler('stop', stop))
	updater.dispatcher.add_handler(CommandHandler('next', nextt))
	updater.dispatcher.add_handler(CommandHandler('previous', prev))

	updater.dispatcher.add_handler(CommandHandler('volumeup', volumeup))
	updater.dispatcher.add_handler(CommandHandler('volumedown', volumedown))

	updater.dispatcher.add_handler(CallbackQueryHandler(callback))
	updater.dispatcher.add_handler(MessageHandler(Filters.text, text))

	updater.dispatcher.add_error_handler(error)
	updater.start_polling(bootstrap_retries = 4, clean = True)
	


	updater.idle()

def replaceData(data, name):
	replaced = str(data).split("('%s' % name, ['", 1)[1]
	replaced = replaced.split("']), ('", 1)[0]
	replaced = replaced.replace("'", "")
	replaced = replaced.replace("(", "")
	replaced = replaced.replace(")", "")
	replaced = replaced.replace("[", "")
	replaced = replaced.replace("]", "")

	return replaced

if __name__ == '__main__':
	main()