
from datetime import date
import requests
import re
import time
import lxml.html as lxml
import sys
from dryscrape import *

last = ''

def parse(input, tries = 1):
	try:
		html = Session(base_url = input)
		html.visit('')
		
	except:
		sys.stderr.write("Connection Failed, try: %d\n" % tries)
		if tries > 3:
			time.sleep(3)
			return parse(input, tries + 1)
		else:
			sys.stderr.write("Connection Failed, Aborting\n")
			return None	
	
	for item in html.xpath("//a[@href]"):

		if "all available" in item.text():
			
			try:
				html.visit(item['href'])
				break
			except:
				sys.stderr.write("Connection Failed, try: %d\n" % tries)
				time.sleep(3)
				if tries > 3:
					return parse(input, tries + 1)
				else:
					sys.stderr.write("Connection Failed, Aborting\n")
					return None
		
	return html

def chunks(l, n):	
	for i in xrange(0, len(l), n):
		yield l[i:i+n]

def pricer(unit, html, scrape = True, times = False):
	"""
	try:
		timestamp = int(time.time())


		IDs = re.findall(r(?<!\\)'(.*?)(?<!\\)', p_range[1])[1:]

		url = "http://units.realtydatatrust.com/Overlay/MonthlyRent.aspx?pid=%s&uid=%s&mid=%s&availdate=%s&timestamp=%d" % \
			(IDs[0], IDs[1], IDs[2], IDs[3], timestamp)
		print url	
		html = lxml.fromstring(requests.get(url).text)

		for tag in html.cssselect("span"):
			
			if "id" in tag.keys():
				if tag.attrib['id'] == 'spRent':
					return tag.text

	except:
		pass
	"""
	
	non_decimal = re.compile(r'[^\d]+') #regex for stripping non-decimal characters
	out = '' #instead of changing the value of unit[]
	flag = False
	try:
		if type(unit['price']) != str:
			
			
			if scrape == True:
				html.eval_script(unit['price'][1])
				time.sleep(1) #needs time to load the javascript in the browser

			text = html.at_xpath('//span[@id="spRent"]').text()
			if text != None:
				out = text
		else: 
			if len(unit['price']) > 8: flag = True #given a range with no javascript (to be starred)
			out = unit['price'][0].text().split(" ")[0]

		if out == '':
			flag = True
			out = unit['price'][0].text().split(" ")[0]

	 	if flag: out = non_decimal.sub('', out) + "*"
			
		else: out = non_decimal.sub('', out)

	except Exception as inst:
		pass
	try:
		"""
		new_page = Session(base_url = unit['button'].children()[0]['href'])
		new_page.visit('')
		text = new_page.at_xpath('//span[@id=spRent"]').text()
		"""
		pass
	except Exception as inst:
		pass

	if out == '' or out == None or len(out) < 2:
		out = non_decimal.sub('', unit['price'][0].text().split(" ")[0]) + "*" #failed javascript
	
	return out


def avail(i_date):
	if "now" in i_date.lower():
		today = date.today()
		return "%s/%s/%s" % (today.month, today.day, today.year)
	else: return i_date

def printer(unit, propID, html, last):
	return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % 	(	propID,
							unit['floorPlan'],
							unit['unit'],
							unit['sqft'],
							unit['bed'],
							unit['bath'],
							pricer(unit, html),
							avail(unit['available'])
						)


def main(input):
	lines = []	
	with open(input, "r") as f:
		lines = [x.split("\t") for x in f.readlines()]

	print "property_id\tfloorplan_name\tunit_name\tsqft\tbed\tbath\tprice\tavailable_date"
	
	classIDs = ['floorPlan', 'bed', 'bath', 'unit', 'sqft', 'price', 'available', 'button']
	count, num = 1, len(lines)
	for line in lines:
		sys.stderr.write("Working on %s: %d of %d\n" % (line[1], count, num))
		html = parse(line[1])

		if html == None:
			count += 1
			continue
		
		units = []
		w_unit = {}
		for tag in html.xpath("//td[@class]"):

			string = tag['class']

			if string in classIDs:
				if w_unit.has_key(string):

					units.append(w_unit)
					w_unit = {}
				children, c_tag = tag.children(), tag
				if len(children) > 0:

					c_tag = children[0]

					if string == 'price':
						href=''						
						try:
							href = children[0]['href']
						except:
							pass
						w_unit[string] = [c_tag, href]

					else: w_unit[string] = c_tag.text()
				
				else:
					w_unit[string] = c_tag.text()


		units.append(w_unit)

		for unit in units:

			try:		

				print printer(unit, line[0], html)

			except:

				pass	
		count +=1

main("csv/Link 8.csv")
