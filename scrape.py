
from datetime import date
import requests
import re
import time
import lxml.html as lxml
import sys
from paradigm import paradigm

class scraper:
	
	def __init__(self, i_file, links = None, focus = 0):
		self.context = paradigm(i_file, focus)
		self.focus = self.context.focus()
		self.set_links(links)
	
	def set_links(self, links):
		self.links = []
		try:
			with open(links, 'r') as f:
				self.links = [x.split("\t") for x in f.readlines()]
			if self.links == None: self.links = []
		except IOError:
			sys.stderr.write("Link file not found.\n")
	
	def run(self, limit = 0):
		if self.links == None or self.links == []:
			sys.stderr.write("Please set links before running.\n")			
			return		
		
		print "property_id\tfloorplan_name\tunit_name\tsqft\tbed\tbath\tprice\tavailable_date"
		
	
		count, num = 1, len(self.links)
		
		for line in self.links:
			
			sys.stderr.write("Working on %s: %d of %d\n" % (line[1], count, num))
			html = self.load(line[1])

			if html == None:
				count += 1
				continue
		
			units = self.get_units(html)

			for unit in units:
				try:		

					print self.printer(unit, line[0])

				except Exception as inst:
					sys.stderr.write(str(inst) + "\n")
			

			if count == limit: break		
			count +=1

	def sample(self):
		for eye in self.context.jar():
			self.focus = eye
			run(1)
		self.focus = self.context.focus()


	def load(self, url, tries = 1, redirect = True):
		try:
			html = lxml.fromstring(requests.get(url).text)
		
		except:
			sys.stderr.write("Connection Failed, try: %d\n" % tries)
			if tries > 3:
				time.sleep(3)
				return parse(url, tries + 1, redirect)
			else:
				sys.stderr.write("Connection Failed, Aborting\n")
				return None

		if redirect:
			for item in html.xpath('//a'):

		
				if item.text != None and "all available" in item.text:
					if "href" in item.keys():
						try:
							#add dialogue for cleaning links
							return lxml.fromstring(requests.get("http:" + item.attrib['href']).text)
						except:
							sys.stderr.write("Connection Failed, try: %d\n" % tries)
							time.sleep(3)
							if tries > 3:
								return self.load(url, tries + 1, redirect)
							else:
								sys.stderr.write("Connection Failed, Aborting\n")
								return None
					else:
						sys.stderr.write("No Current Availability")
						return None

		return html

	def avail(self, i_date):
		if self.focus['avail']['now'] in i_date.lower():
			today = date.today()
			return "%s/%s/%s" % (today.month, today.day, today.year)
		else: return i_date

	def pricer(self, p_range):
	
		non_decimal = re.compile(self.focus['pricer']['regex'])
		out = flag = ''
	
		try:
			if type(p_range) != str:
				if self.focus['pricer']['r_identifier'] in p_range[1].lower():
					out = p_range[1]
				else:	

					out = p_range[0].split(" ")[0]
					flag = "*"
			else:
				out = p_range
		
		
		 	

		except Exception as inst:
			sys.stderr.write(str(inst))
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
								self.pricer(unit['price']),
								self.avail(unit['available'])
								)

	def link(self, node):
		text, children = '', node.getchildren()
		try:
			if node.text != None:
				text = node.text
		except:
			pass
		if len(children) > 0 and node.attrib['class'] != 'floorPlan':
			href = ''		
			for ch in node.xpath("a[@href]"):
				if ch.attrib['href'] != None:
					href = ch.attrib['href']
				if ch.text != None:
					text = ch.text
				for gch in ch.getchildren():
					if gch.text != None:
						text = gch.text

			return [text, href]
		elif len(children) > 0 and node.attrib['class'] == 'floorPlan':
			for ch in node.xpath("a[@href]"):
				if ch.text != None:
					text = ch.text

			return text
		else: return text
	
	

	def get_units(self, html):
		units = []
		w_unit = {}
		for tag in html.xpath(self.focus['unit']['tag']):
			for subtag in tag.xpath(self.focus['unit']['subtag']):
				string = subtag.attrib[self.focus['unit']['attribute']]
			
				if string in self.focus['classIDs']:
					w_unit[string] = self.link(subtag)

			if len(w_unit) == 8: units.append(w_unit)	
			w_unit = {}

		for unit in units:
			try:	
				p_range, b_title, b_link = unit['price'][0], unit['button'][0], unit['button'][1]	
				if len(p_range) > 8:

					if 'request' in b_title.lower() and b_link != '':
						html = self.load("http:" + b_link, 1, False)
						for tag in html.xpath("//span"):
							text = tag.text
							if text != None and 'rent' in text.lower():
								if '$' in text: unit['price'][1] = text
				else:
					sys.stderr.write(b_title)
					pass
					
			except Exception as inst:
				sys.stderr.write(str(inst))
		return units


def main(links):
	sc = scraper("perspectives.yaml", links)
	sc.run()


main("csv/link 8-1.csv")




