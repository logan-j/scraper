
from datetime import date, datetime
from scrapetools import *
from colorama import Fore
from sets import Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re
import time
import lxml.html as lxml
import sys, traceback
import argparse
import json
import math


class scraper:
	
	def __init__(self, para, args):
		self.context = para
		self.focus = self.context.focus()
		self.date = args.date
		self.sess = None
		self.set_links(args.infile)
		self.output = args.outfile
	 	
	
	def set_links(self, links):
		self.links = []
		try:
			with open(links, 'r') as input_file:
				self.links = [re.split(',|\t', x) for x in input_file.readlines()]

			if self.links == None: self.links = []
		except IOError:
			sys.stderr.write(Fore.RED + "Link file not found.\n" + Fore.RESET)
			sys.exit()
	
	def run(self, limit = 0):
		if self.links == None or self.links == []:
			sys.stderr.write(Fore.RED + "Please set links before running.\n" + Fore.RESET)
			return		
		
		self.output.write("property_id\tfloorplan_name\tunit_name\tsqft\tbed\tbath\tprice\tavailable_date\n")
		
	
		count, num = 1, len(self.links)
		
		for line in self.links:
			sys.stderr.write("Working on %s: %d of %d\n" % (line[1], count, num))
			html = self.load(line[1].strip(), 1, self.focus['unit']['navigate'], self.focus['unit']['dryscrape'])

			if html == None:
				count += 1
				self.output.write("%s\t***NO CURRENT AVAILABILITY***\n" % line[0])
				continue
			units = []
			try:
				if len(line) == 3:
					units = self.get_units(html, line[2])
				else:
					units = self.get_units(html)
			
			except Exception as inst:
				self.output.write("%s\t***UNKNOWN ERROR***\n" % line[0])
				sys.stderr.write(Fore.RED + "UNKNOWN ERROR PROCESSING UNITS\n" + Fore.RESET)
				sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
				traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
				count += 1
				continue
			
			if len(units) == 0:
				sys.stderr.write(Fore.RED + "NO UNITS FOUND\n" + Fore.RESET)
				self.output.write("%s\t***NO UNITS FOUND***\n" % line[0])
			else:
				for unit in units:
					try:		
						output = self.printer(unit, line[0])
						if output != None:

							self.output.write(output.encode('utf-8') + "\n")
					
					except KeyboardInterrupt:
						sys.exit()
					except Exception as inst:
						sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
						traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])


			

			if count == limit: break		
			count +=1

	"""
	def sample(self):
		for eye in self.context.jar():
			self.focus = eye
			run(1)
		self.focus = self.context.focus()
	"""


	def load(self, url, tries=1, navigate=True, ds=None):
		if not url.startswith('http'): url = "http:" + url
		html = None
		if ds:
			try:
				if self.sess == None:
					self.sess = webdriver.PhantomJS()
				self.sess.get(url)
				try:
					element = WebDriverWait(self.sess, 20).until(
						EC.presence_of_element_located((By.XPATH, ds)))
					time.sleep(2)
				except Exception as inst:
					pass

				source = self.sess.page_source
				html = lxml.fromstring(source, base_url=url)
				if navigate:
					return html
					#click logic, etc
				else:
					return html

			except KeyboardInterrupt:
				self.sess.quit()
				sys.exit()
			except Exception as inst:
				sys.stderr.write(Fore.YELLOW + str(inst) + (": Connection Failed, try: %d\n" % tries) + Fore.RESET)
				if tries > 3:
					time.sleep(3)
					return self.load(url, tries + 1, navigate)
				else:
					sys.stderr.write(Fore.RED + "Connection Failed, Aborting\n" + Fore.RESET)
					return None
			
		else:

			try:
				text = requests.get(url)
				if text.status_code != 200:
					if text.status_code >= 400:

						sys.stderr.write(Fore.RED + ("Status code: %d. PAGE DID NOT LOAD; SKIPPING URL.\n" % text.status_code) + Fore.RESET)
						return None
					else:
						sys.stderr.write(Fore.YELLOW + ("Status code: %d. Attempting to proceed.\n" % text.status_code) + Fore.RESET)
				html = lxml.fromstring(text.text, base_url = text.url)

			except KeyboardInterrupt:
				sys.exit()
			except Exception as inst:
				sys.stderr.write(Fore.YELLOW + str(inst) + (": Connection Failed, try: %d\n" % tries) + Fore.RESET)
				if tries > 3:
					time.sleep(3)
					return self.load(url, tries + 1, navigate)
				else:
					sys.stderr.write(Fore.RED + "Connection Failed, Aborting\n" + Fore.RESET)
					return None

			if navigate:

				for item in html.xpath(self.focus['nav']['links']):

			
					if item.text != None and self.focus['nav']['redirect_on'] in item.text.lower():
						if self.focus.has_key('json'):
							split = re.compile(self.focus['json']['split'])
							loc = split.split(item.text)[self.focus['json']['index']]
							return json.loads(requests.get(self.focus['json']['format'] % loc).text)
						elif "href" in item.keys():
							try:
								goto = item.attrib['href']
								if not goto.startswith('http'):goto = 'http:' + goto
								text = requests.get(goto)
								return lxml.fromstring(text.text, base_url = text.url)
							except KeyboardInterrupt:
								sys.exit()						
							except Exception as inst:
								sys.stderr.write(Fore.YELLOW + (str(inst) + ": Connection Failed, try: %d\n" % tries) + Fore.RESET)
								time.sleep(3)
								if tries > 3:
									return self.load(url, tries + 1, navigate)
								else:
									sys.stderr.write(Fore.RED + "Connection Failed, Aborting\n" + Fore.RESET)
									return None
						else:
							self.output.write("")
							sys.stderr.write(Fore.RED + "No Current Availability\n" + Fore.RESET)
							return None

		return html

	def avail(self, i_date):
		if self.focus['avail']['now'] in i_date.lower():
			today = date.today()
			return "%s/%s/%s" % (today.month, today.day, today.year)
		elif self.focus['avail'].has_key('month'):
			i_date = i_date.strip()
			i_date = i_date.split(" ")
			i_date = " ".join(i_date[:2])
			temp = datetime.strptime(i_date, "%b %d")
			
			year = date.today().year
			if temp.month < date.today().month:
				year += 1
			return "%s/%s/%s" % (temp.month, temp.day, year)
		else: return i_date

	def pricer(self, unit):
		p_range = unit['price']
		non_decimal = re.compile(self.focus['pricer']['regex'])
		out = flag = ''
	
		try:
			if type(p_range) != str:
				if unit['set']:
					out = p_range[1]
				else:	

					out = p_range[0].split(" ")[0]
					flag = "*"
			else:
				out = p_range
		
		
		 	

		except Exception as inst:
			sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
			traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			flag = '*'
	
		finally:
			return non_decimal.sub('', out) + flag

	def printer(self, unit, propID):
		bath = math.floor((float(unit['bath']) * 2.0) + 0.5)/2.0
		if bath % 1 == 0:
			bath = int(bath)
		unit['bath'] = bath
		price = str(self.pricer(unit))

		if price.endswith('*'):
			price = "--"

		return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % 	(	propID,
									unit['floorPlan'],
									unit['unit'],
									unit['sqft'],
									unit['bed'],
									unit['bath'],
									price,
									self.avail(unit['available'])
									)

	def link(self, node):
		text = ''
		try:
			if node.text != None:

				text = node.text.strip()
			if len(text) == 0:
				temp = [x.strip() for x in node.xpath('descendant::*/text()') if len(x.strip()) > 0]
				if len(temp) > 0:
					text = min(temp, key=len)
		except Exception as inst:
			sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
			traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])


		if self.focus['unit']['navigate']:
			if self.focus.has_key('link'):
				
				try:
					goto = node.attrib[self.focus['link']['attribute']]
					if len(goto) != 0:
						return [text, goto]
				except:
					return text
			else:
				goto = node.xpath('.//*[@href]')
				if len(goto) != 0 and node.attrib[self.focus['unit']['attribute']] not in self.focus['s_nav']:
					return [text, goto[0].attrib['href']]


				else: return text

		return text
	
	

	def get_units(self, html, i_date = None):
		units = []
		w_unit = {'set': False}
		for tag in html.xpath(self.focus['unit']['tag']):
			const = {}
			if self.focus['timing'].startswith('pre'):
				if self.focus['pre_build'].has_key('f_root'):
					self.focus['pre_build']['root'] = tag.xpath(self.focus['pre_build']['f_root'])[0].text
					for key, val in tree(self.focus['pre_build']):
						const[key] = val
				elif self.focus['pre_build'].has_key('b_root'):
					for key, val in dict.iteritems(self.focus['pre_build']):
						if 'root' not in key:
							if type(val) == dict:
								text = self.link(tag.xpath(val['find'])[0])
								cleaner = re.compile(val['remove'])
								const[key] = cleaner.sub('', text).strip()

							else:
								const[key] = self.link(tag.xpath(val)[0])
				elif self.focus['pre_build'].has_key('m_root'):
					
					m_root = self.focus['pre_build']['m_root']
					info = [x.strip() for x in tag.xpath(m_root[0])[-1].xpath(m_root[1]) if len(x.strip()) > 0]
					for key, val in dict.iteritems(self.focus['pre_build']):
						if 'root' not in key:
							const[key] = info[val]
					
			for subtag in tag.xpath(self.focus['unit']['subtag']):
				if len(const) > 0:
					for key, val in dict.iteritems(const): w_unit[key] = val
				if self.focus['unit']['explicit']:
					string = subtag.attrib[self.focus['unit']['attribute']]

					if self.focus['classIDs'].has_key(string):
				
						temp = self.link(subtag)
						if len(temp) > 0:
							w_unit[self.focus['classIDs'][string]] = temp


				else:
					if len(self.focus['classIDs']) != 0:
						string = self.focus['classIDs'].pop()

						w_unit[string] = self.link(subtag)
				if len(w_unit) == self.focus['unit']['quan']:
					if self.focus['timing'].endswith('post'):
						for key, val in dict.iteritems(self.focus['post_build']):
							if type(val) == str:
								if val.startswith('&'):
									w_unit[key] = val[1:]
								else:
									cleaner = re.compile(val)
									w_unit[key] = cleaner.sub('', w_unit[key])
							elif type(val) == dict:
								for v_key, v_val in dict.iteritems(val):
									replace = re.compile(v_val)
									w_unit[key] = replace.sub(v_key, w_unit[key]).strip()

							else:
								for item in val:
									if not w_unit.has_key(key):
										w_unit[key] = w_unit[item]
									else:
										w_unit[key] += " " + w_unit[item]
					units.append(w_unit)
					w_unit = {'set': False}
					if not self.focus['unit']['explicit']:
						self.focus['classIDs'] = list(self.focus['reset'])




		if self.focus['unit']['navigate']:
			for unit in units:
				
				try:
					p_range = unit['price'][0]

					if type(unit['navigate']) == str:
						b_title = "No Button Title"
						vals = re.split('[^\d]+', re.split(';', unit['price'][1])[1])
						b_link = unit['navigate'] % ("http://" + re.split('/', html.base_url)[2], vals[1], vals[2])

					else:	
						b_title = unit['navigate'][0]
						b_link = unit['navigate'][1]	
					if len(p_range) > 8:

						if self.focus['nav']['flag'] in b_title.lower() and b_link != '':
							if self.focus['unit'].has_key('s_dryscrape'):
								s_html = self.load(b_link, 1, False, self.focus['unit']['s_dryscrape'])
							else:
								s_html = self.load(b_link, 1, False)
							
							if s_html != None:
								if self.focus['pricer'].has_key('text'):
									prices = s_html.xpath(self.focus['nav']['location'])
									for i, price in enumerate(prices, 0):
										if price != None and self.focus['pricer']['r_identifier'] in price.lower():
											unit['set'] = True
											unit['price'][1] = prices[i + self.focus['pricer']['offset']]
											
								else:
									for tag in s_html.xpath(self.focus['nav']['location']):
										text = tag.text
										if text != None and self.focus['pricer']['r_identifier'] in text.lower():
											unit['set'] = True
											unit['price'][1] = text
					else:
						if self.focus['nav']['flag'] not in b_title.lower():
							sys.stderr.write(Fore.RED + b_title + "\n" + Fore.RESET)
						pass
					
				except Exception as inst:
					sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
					traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
		return units

class scrapeJSON(scraper):

	def pricer(self, unit):
		return unit['price']


	def avail(self, date):
		non_decimal = re.compile('[^\d]+')
		date = datetime.fromtimestamp(int(non_decimal.sub('', date))/1000 + 86400).strftime("%m/%d/%Y")
		return date

	def get_units(self, json, i_date = None):
		
		units = []
		for available in json['results']['availableFloorPlanTypes']:
			for package in available['availableFloorPlans']:
				const = {}
				for key, val in dict.iteritems(self.focus['pre_build']):
					const[val] = package[key]
				for finish in package['finishPackages']:

					for apartment in finish['apartments']:
						w_unit = dict(const)
						w_unit['unit'] = apartment['apartmentNumber']
						w_unit['sqft'] = apartment['apartmentSize']
						w_unit['price'] = apartment['pricing']['effectiveRent']
						w_unit['available'] = apartment['pricing']['availableDate']
						if 'studio' in w_unit['bed'].lower():
							w_unit['bed'] = '0'
						else:
							w_unit['bed'] = re.sub('[^\d.]+', '', w_unit['bed'])
						w_unit['bath'] = re.sub('[^\d.]+', '', w_unit['bath'])
						units.append(w_unit)
		return units

class scrapeExplicit(scraper):

	def set_links(self, links):
		self.links = []

		checked, mapping = Set(), {}
		
		try:
			with open(links, 'r') as input_file:
				
				lines = [re.split(',|\t', x) for x in input_file.readlines()]

				for line in lines:
					
					mapping[line[2]] = line[0]
		except IOError:
			sys.stderr.write(Fore.RED + "Link file not found.\n" + Fore.RESET)
			sys.exit()

		self.mapping = fuzzyDic(mapping, 90)


		for i, dates in enumerate(iter_dates(self.date[0]), 1):
			sys.stderr.write(Fore.YELLOW + "Gathering Date: %s\n" % dates + Fore.RESET)
			url = self.focus['base_url'] % (self.focus['fuzzer'], dates)
			html = None
			try:
				if self.sess == None:
					self.sess = webdriver.PhantomJS()
				self.sess.get(url)
				try:
					element = WebDriverWait(self.sess, 10).until(
						EC.presence_of_element_located((By.XPATH, self.focus['unit']['tag'])))
					time.sleep(2)
				except Exception as inst:
					pass

				source = self.sess.page_source
				html = lxml.fromstring(source)
			except KeyboardInterrupt:
				self.sess.quit()
				sys.exit()	
			except Exception as inst:
				sys.stderr.write(Fore.RED + "Unexpected Error Attempting to Load Page. Please Try Again.\n" + Fore.RESET)
				sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
				traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			

			if html != None:
				for tag in html.xpath("//div[@class='unit-block']"):
					t_url = re.split('[?]', tag.xpath("a[@href]")[0].attrib["href"])[0]
					if t_url not in checked:
						checked.add(t_url)
						self.links.append(['', t_url, dates])
		
	def filter_empty(self, i_list, val = None):
		o_list = [x.strip() for x in i_list if len(x.strip()) > 0]
		if val != None:
			return o_list[val]
		else: return o_list


	def get_units(self, html, i_date = 'now'):
		w_unit = {'available': i_date}

		text = html.xpath("//div[@class='property-details pull-left']")[0].xpath("*/text()")
		
		w_unit['unit'] = re.split('\s+', text[0])[1]
		bb = re.sub('studio', '0', text[1].lower())
		bb = re.split('[^\d.]+', bb)
		w_unit['bed'] = bb[0]
		w_unit['bath'] = bb[1]
			
		try:
			w_unit['sqft'] = re.sub('[^\d]+', '', html.xpath("//span[@class='pull-right']")[0].text)
		except Exception as inst:
			w_unit['sqft'] = '--'


		text = html.xpath("//address[@class='no-spacing']")[0].xpath(".//text()")

		w_unit['location'] = self.filter_empty(text, 0)

		#price
		is_set = False
		for tag in html.xpath("//table[@id='unit-price-table']"):
			prices = self.filter_empty(tag.xpath(".//text()"))
			w_unit['price'] = prices[9]




		w_unit['floorPlan'] = "%s Bed %s Bath" % (w_unit['bed'], w_unit['bath'])

		return [w_unit]

	def printer(self, unit, propID):
		propID, sqft = '--', unit['sqft']
		if len(sqft) < 3:
			sqft = '--'
		try:
			propID = self.mapping[unit['location']]
		except:
			return None
		price = str(self.pricer(unit))
		return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % 	(	propID,
									unit['floorPlan'],
									unit['unit'],
									sqft,
									unit['bed'],
									unit['bath'],
									price,
									self.avail(unit['available'])
									)



class scrapeRedirect(scraper):

	def get_units(self, html):
		links, units = [], []
		for link in html.xpath('//li[@class]'):
			attrib = link.attrib['class']
			if 'grid-item' in attrib and 'mix' in attrib:
				for item in link.xpath('.//*/text()'):
					text = item.lower()
					if 'available' in text and 'not' not in text:
						links.append({'navigate': link.xpath(".//*[@href]")[0].attrib['href']})
		for link in links:
			const = {}
			url = re.split('/', html.base_url[7:])[0]
			w_html = self.load("http://%s%s" % (url, link['navigate']), 1, False)
			for text in w_html.xpath(self.focus['pre_build']['f_root'])[0].xpath('.//text()'):
				if 'sq' in text.lower():
					self.focus['pre_build']['root'] = text.lower().strip()
					break
			for key, val in tree(self.focus['pre_build']):

				const[key] = val
			for tag in w_html.xpath(self.focus['unit']['tag']):
				w_unit = dict(const)
				for subtag in tag.xpath(self.focus['unit']['subtag']):
					if len(self.focus['classIDs']) != 0:
						string = self.focus['classIDs'].pop()

						w_unit[string] = self.link(subtag)

				self.focus['classIDs'] = list(self.focus['reset'])
				for unit in units:
					for key, val in dict.iteritems(unit):
						unit[key] = val.strip()
				units.append(w_unit)
					

		return units

	def avail(self, i_date):
		if self.focus['avail']['now'] in i_date.lower():
			today = date.today()
			return "%s/%s/%s" % (today.month, today.day, today.year)	
		else:
			return re.sub('\(.+\)', '', i_date).strip()




def main():
	
	parser = argparse.ArgumentParser(description='Scrape general pricing and availability info.')
	
	parser.add_argument('-n', '--num', 
		type=int, 
		nargs=1, 
		help='Limit the number of links to run to NUM links from beginning.', 
		default=[0])

	parser.add_argument('-p', '--per',
		type=int,
		nargs=1,
		help='Specify the PER-th perspective to use, indexed started from 0.',
		default=[0])

	parser.add_argument('-l', '--list',
		action='store_true',
		help="List the names of all available perspective types and exit.")

	parser.add_argument('infile',
		nargs='?',
		type=str)

	parser.add_argument('outfile',
		nargs='?',
		type=argparse.FileType('w'),
		default=sys.stdout)
	today = date.today()
	d_date = "%s/%s/%s" % (today.month, today.day, today.year)
	parser.add_argument('-d', '--date',
		type=str,
		nargs=1,
		help='Specify a DATE between today and the given input to check for availabilty.',
		default=[d_date])

	args = parser.parse_args()
	para = paradigm("perspectives.yaml", args.per[0])
	if args.list:
		for index, item in enumerate(para.jar()):
			print index, item['name']
		sys.exit()
	else:
		if para.focus().has_key('json'): 		#AVALON BAY

			sc = scrapeJSON(para, args)

		elif para.focus().has_key('redirect'): 	#LINK 53
			
			sc = scrapeRedirect(para, args)

		elif para.focus().has_key('base_url'): 	#MAC

			sc = scrapeExplicit(para, args)

		else:									#LINK 8, LINK 55, LINK 96, AIMCO
			sc = scraper(para, args)
	sc.run(args.num[0])


main()

