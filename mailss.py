from urllib.parse import urlparse, urljoin
from urllib3.exceptions import InsecureRequestWarning
import time
from datetime import datetime as dt
import random as rdm
import os

import argparse

import warnings
from bs4.builder import XMLParsedAsHTMLWarning
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import re


warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

# iso-8859-1 windows-1251 latin-1
# lxml html.parser

symbols = "qwertyuiopasdfghjklzxcvbnm1234567890-_.@"
save_folder = "result"

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

ua = UserAgent()

links_list = []
this_link_number = 0

int_url = set()
ext_url = set()
total_int_url = set()
total_ext_url = set()

mail_list = []
total_mail_list = []
total_mail_list_for_save = []

start_time = None

savefile = None # int 0 or 1

comment = ""

log_lvl = None # 0 1 2

filetype = None # .txt .log and more


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-s", "--savefile", type=int, default=1, dest="savefile", help="saves the final file with mails (0 or 1, default:1)")
	parser.add_argument("-l", "--loglvl", type=int, default=2, dest="loglvl", help="which is responsible for mail output to the console (0-does not output, 1-gives the number of mails, 2-gives the number and list of mails, by default 2)")
	parser.add_argument("-f", "--filetype", default=".txt", dest="filetype", help="is responsible for the file type when saving ( enter a value with a dot, the default is(.txt) )")
	arguments = parser.parse_args()
	return arguments

def valid_url(url):
	parsed = urlparse(url)
	return bool(parsed.netloc) and bool(parsed.scheme)

def website_links(url):
	global this_link_number
	try:
		urls = set()
		domain_name = urlparse(url).netloc
		soup = BeautifulSoup(requests.get(url).content, "html.parser", from_encoding="latin-1")  

		for a_tag in soup.findAll("a"):
			try:
				href = a_tag.attrs.get("href")
				if href == "" or href is None:
					continue

				href = urljoin(url, href)

				parsed_href = urlparse(href)
				href = parsed_href.scheme + "://" +  parsed_href.netloc + parsed_href.path

				if not valid_url(href):
					continue
				if href in int_url:
					continue
				if domain_name not in href:
					if href not in ext_url:
						#print(f"[!] External link: {href}")
						ext_url.add(href)
						total_ext_url.add(href)
					continue
				if ".jpg" in href or ".pdf" in href or ".jpeg" in href:
					continue
				#print(f"[*] Internal link: {href}")
				urls.add(href)
				int_url.add(href)
				total_int_url.add(href)
			except:
				pass
		return urls
	except:
		print(f"[-] Couldn't find the links at: {links_list[this_link_number]}")

visited_urls = 0

def crawl(url, max_urls=5):
	try:
		global visited_urls
		visited_urls += 1
		links = website_links(url)

		for link in links:
			if visited_urls > max_urls:
				break
			crawl(link, max_urls = max_urls)
	except:
		pass

def find_emails_on_a_page(link):
	try:
		headers = {
		'user-agent' : ua.random
		}

		page_request = requests.get(link, headers=headers, verify=False)

		page_html = BeautifulSoup(page_request.content, "html.parser", from_encoding="latin-1")

		tag_name_list = []
		all_tags_list = page_html.findAll(True)
		sentences = []
		emails_list = []

		for tag in all_tags_list:
			if tag.name not in tag_name_list:
				tag_name_list.append(tag.name)

		for tag in tag_name_list:
			list_of_all_tags_of_this_type = page_html.find_all(tag)
			for individual_tag in list_of_all_tags_of_this_type:
				if len(individual_tag.findChildren()) <= 1:
					tag_emails = re.findall(r'[\w\.-]+@[\w\.-]+[.]+[\w\.-]+', individual_tag.text)
					for email in tag_emails:
						if email not in emails_list:
							emails_list.append(email)
					tag_emails = re.findall(r'[\w\.-]+[(]+eta+[)]+[\w\.-]+', individual_tag.text)
					for email in tag_emails:
						if email not in emails_list:
							email = email.replace("(eta)","@")
							emails_list.append(email)
		return emails_list
	except:
		pass

def valid_mail(email):
	is_valid = True
	email = email.lower()
	for symbol in email:
		if symbol not in symbols:
			is_valid = False
			break

	return is_valid

def mail_parser():
	try:
		total_mail_list_for_save.append(f"\n[*] Emails: {links_list[this_link_number]}")
		for link in int_url:
			try:
				emails = find_emails_on_a_page(link)
				for email in emails:
					email = email.lower().replace(" ","")
					if email[-1:] == ".": email = email[:-1]
					if email not in mail_list:
						is_valid = valid_mail(email)
						if is_valid == False: continue

						
					
						mail_list.append(email)
						total_mail_list.append(email)
						total_mail_list_for_save.append(email)
			except:
				pass
		total_mail_list_for_save.append("\n")
		mail_print()
	except:
		pass

def mail_print():
	global this_link_number
	global log_lvl

	if log_lvl == 0: return print()

	print(f"[*] Emails [{len(mail_list)}] : {links_list[this_link_number]} [{this_link_number+1}/{len(links_list)}]")

	if log_lvl == 1: return print()

	for mail in mail_list:
		print(mail)
	print()

def mail_save():
	global total_mail_list
	global comment
	global filetype

	if not os.path.isdir(save_folder):
		os.mkdir(save_folder)

	os.chdir(save_folder)

	file = open(f"emails_{len(total_mail_list)}_{dt.now().date().replace("-","")}_r{rdm.randint(1, 19385)}{filetype}", "w", encoding='utf-8')

	fmd = "$$ email parser $$ fmd $$ with <3 from russia $$\n\n"
	file.write(fmd)
	if comment != "":
		comment_ = f"[*] Comment: {comment}\n"
		file.write(comment_)
	mail_count = f"[!] Total emails: {len(total_mail_list)}\n"
	file.write(mail_count)
	file.write(f"[{len(links_list)}] ")
	for link in links_list:
		file.write(link + ", ")
	file.write("\n\n")
	for mail in total_mail_list_for_save:
		file.write(mail + "\n")
	file.close()

def crawling():
	global start_time
	global this_link_number
	global savefile
	global comment
	global log_lvl

	start_time = time.time()

	for link in links_list:
		crawl(link)
		mail_parser()

		mail_list.clear()
		int_url.clear()
		ext_url.clear()
		this_link_number += 1

	end_time = int(time.time() - start_time)

	print(f"\n[*] Total links: {len(links_list)} -> {len(total_ext_url) +  len(total_int_url)} [{len(total_int_url)}|{len(total_ext_url)}]")
	print("[*] Total emails: ", len(total_mail_list))
	print(f"[*] Execution time: {end_time//60}min {end_time%60}sec")
	if comment != "": print(f"[*] Comment: {comment}")
	print(f"[*] Log level: {log_lvl}")
	try:
		if savefile == 1:
			mail_save()
		elif savefile == 0:
			print("[!] File with mails will not be saved because -s parameter has a value of 0")
	except:
		print("[!] Save file with emails is failed")

def get_set_options():
	global savefile
	global log_lvl
	global filetype

	options = get_args()
	_savefile = options.savefile
	_loglvl = options.loglvl
	_filetype = options.filetype

	if _savefile != 0 and _savefile != 1:
		_savefile = 1

	savefile = _savefile

	if _loglvl != 0 and _loglvl != 1 and _loglvl != 2:
		_loglvl = 2

	filetype = _filetype

	log_lvl = _loglvl

	if savefile == 0: print("[!] Attention, the final file will not be saved!\n")
	elif savefile == 1: print("[!] Attention, the final file will be saved!\n")

def get_comment():
	global comment
	print("[*] Write a comment if required: ", end='')
	_comment = input()
	print()
	if _comment.replace(" ","") == "": _comment = ""
	comment = _comment

def add_links():
	try:
		get_set_options()
		get_comment()

		links_count = 0

		while True:
			print(f"[{links_count}] Write link | 0 for continue: ", end = '')
			link = input().replace(" ","")
			if link == "0":
				break
			elif link == "":
				continue
			else:
				if link not in links_list:
					links_list.append(link)
					links_count += 1

		print()

		if len(links_list) < 1:
			print("[!] No Links")
		else:
			crawling()
	except KeyboardInterrupt:
		print("\n[-] ctrl + c\n")


if __name__ == "__main__":
	add_links()