
from datetime import date, datetime
from scrapetools import *
import requests
import re
import time
import lxml.html as lxml
import sys, traceback
import argparse
import json


class scraper:
	
	def __init__(self, para, args):
		self.context = para
		self.focus = self.context.focus()
		self.set_links(args.infile)
		self.output = args.outfile
	 	
	
	def set_links(self, links):
		self.links = []
		try:
			with open(links, 'r') as input_file:
				self.links = [re.split(',|\t', x) for x in input_file.readlines()]

			if self.links == None: self.links = []
		except IOError:
			sys.stderr.write("Link file not found.\n")
	
	def run(self, limit = 0):
		if self.links == None or self.links == []:
			sys.stderr.write("Please set links before running.\n")

			return		
		
		self.output.write("property_id\tfloorplan_name\tunit_name\tsqft\tbed\tbath\tprice\tavailable_date\n")
		
	
		count, num = 1, len(self.links)
		
		for line in self.links:
			sys.stderr.write("Working on %s: %d of %d\n" % (line[1], count, num))
			html = self.load(line[1].strip(), 1, self.focus['unit']['navigate'])

			if html == None:
				count += 1
				continue
		
			units = self.get_units(html)

			for unit in units:
				try:		

					self.output.write(self.printer(unit, line[0]) + "\n")
				
				except KeyboardInterrupt:
					sys.exit()
				except Exception as inst:
					sys.stderr.write("%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args))
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


	def load(self, url, tries = 1, navigate = True):
		if not url.startswith('http'): url = "http:" + url
		try:

			text = requests.get(url)
			if text.status_code == 404:
				sys.stderr.write("Status code %d. Skipping URL\n" % text.status_code)
				return None
			html = lxml.fromstring(text.text)

		except KeyboardInterrupt:
			sys.exit()
		except Exception as inst:
			sys.stderr.write(str(inst) + ": Connection Failed, try: %d\n" % tries)
			if tries > 3:
				time.sleep(3)
				return self.load(url, tries + 1, navigate)
			else:
				sys.stderr.write("Connection Failed, Aborting\n")
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

							return lxml.fromstring(requests.get(goto).text)
						except KeyboardInterrupt:
							sys.exit()						
						except Exception as inst:
							sys.stderr.write(str(inst) + ": Connection Failed, try: %d\n" % tries)
							time.sleep(3)
							if tries > 3:
								return self.load(url, tries + 1, navigate)
							else:
								sys.stderr.write("Connection Failed, Aborting\n")
								return None
					else:
						sys.stderr.write("No Current Availability\n")
						return None

		return html

	def avail(self, i_date):
		if self.focus['avail']['now'] in i_date.lower():
			today = date.today()
			return "%s/%s/%s" % (today.month, today.day, today.year)
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
			sys.stderr.write("%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args))
			traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			flag = '*'
	
		finally:
			return non_decimal.sub('', out) + flag

	def printer(self, unit, propID):
		return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % 	(	propID,
								unit['floorPlan'],
								unit['unit'],
								unit['sqft'],
								unit['bed'],
								unit['bath'],
								self.pricer(unit),
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
			sys.stderr.write("%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args))
			traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])


		if self.focus['unit']['navigate']:
			goto = node.xpath('.//*[@href]')
			if len(goto) != 0 and node.attrib[self.focus['unit']['attribute']] not in self.focus['s_nav']:
				return [text, goto[0].attrib['href']]
			else: return text

		return text
	
	

	def get_units(self, html):
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
			for subtag in tag.xpath(self.focus['unit']['subtag']):
				if len(const) > 0:
					for key, val in dict.iteritems(const): w_unit[key] = val
				if self.focus['unit']['explicit']:
					string = subtag.attrib[self.focus['unit']['attribute']]

					for key in self.focus['classIDs'].keys():
						if key.startswith(string):
							temp = self.link(subtag)
							if len(temp) > 0:

								w_unit[self.focus['classIDs'][key]] = temp
							break
						

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
									print w_unit
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
					b_title = unit['navigate'][0]
					b_link = unit['navigate'][1]	
					if len(p_range) > 8:

						if self.focus['nav']['flag'] in b_title.lower() and b_link != '':
							html = self.load(b_link, 1, False)
							if html != None:
								for tag in html.xpath(self.focus['nav']['location']):
									text = tag.text
									if text != None and self.focus['pricer']['r_identifier'] in text.lower():
										unit['set'] = True
										unit['price'][1] = text
					else:
						if self.focus['nav']['flag'] not in b_title.lower():
							sys.stderr.write(b_title + "\n")
						pass
					
				except Exception as inst:
					sys.stderr.write("%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args))
					traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
		return units

class scrapeJSON(scraper):

	def pricer(self, unit):
		return unit['price']


	def avail(self, date):
		non_decimal = re.compile('[^\d]+')
		date = datetime.fromtimestamp(int(non_decimal.sub('', date))/1000 + 86400).strftime("%m/%d/%Y")
		return date

	def get_units(self, json):
		
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

def main():
	
	parser = argparse.ArgumentParser(description='Scrape general pricing and availability info.')
	parser.add_argument('-n', '--num', type=int, nargs=1, help='Limit the number of links to run to NUM links from beginning.', default=[0])
	parser.add_argument('-p', '--per', type=int, nargs=1, help='Specify the PER-th perspective to use, indexed started from 0.', default=[0])
	parser.add_argument('-l', '--list', action='store_true', help="List the names of all available perspective types and exit.")
	parser.add_argument('infile', nargs='?', type=str)
	parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

	args = parser.parse_args()
	para = paradigm("perspectives.yaml", args.per[0])
	if args.list:
		for index, item in enumerate(para.jar()):
			print index, item['name']
		sys.exit()
	else:
		if para.focus().has_key('json'):

			sc = scrapeJSON(para, args)

		elif False:
			#other subscrape types
			pass
		else:
			sc = scraper(para, args)
	sc.run(args.num[0])


main()

