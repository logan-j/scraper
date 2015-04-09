
from datetime import date
import requests
import re
import time
import lxml.html as lxml
import sys
import dryscrape
import argparse
from paradigm import paradigm

class scraper:
	
	def __init__(self, i_file, args):
		self.context = paradigm(i_file, args.per[0])
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
			html = self.load(line[1])

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
		
		except KeyboardInterrupt:
			sys.exit()
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
						except KeyboardInterrupt:
							sys.exit()						
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
				
				if self.focus['unit']['explicit']:
					string = subtag.attrib[self.focus['unit']['attribute']]
					if string in self.focus['classIDs']:
						w_unit[string] = self.link(subtag)
				else:
					string = 
					w_unit[string] = self.link(subtag)

			if len(w_unit) == 8: units.append(w_unit)	
			w_unit = {}

		if self.focus['unit']['navigate']:
			for unit in units:
				try:	
					p_range = unit['price'][0]
					b_title = unit['button'][0]
					b_link = unit['button'][1]	
					if len(p_range) > 8:

						if 'request' in b_title.lower() and b_link != '':
							html = self.load("http:" + b_link, 1, False)
							for tag in html.xpath("//span"):
								text = tag.text
								if text != None and 'rent' in text.lower():
									if '$' in text: unit['price'][1] = text
					else:
						if 'request' not in b_title.lower():
							sys.stderr.write(b_title + "\n")
						pass
					
				except Exception as inst:
					sys.stderr.write(str(inst))
		return units


def main():
	
	parser = argparse.ArgumentParser(description='Scrape general pricing and availability info.')
	parser.add_argument('-n', '--num', type=int, nargs=1, help='Limit the number of links to run to NUM links from beginning.', default=[0])
	parser.add_argument('-p', '--per', type=int, nargs=1, help='Specify the PER-th perspective to use, indexed started from 0.', default=[0])
	parser.add_argument('infile', nargs='?', type=str)
	parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

	args = parser.parse_args()
	sc = scraper("perspectives.yaml", args)
	sc.run(args.num[0])

main()

