
from datetime import date
import requests
import re
import time
import lxml.html as lxml
import sys
import paradigm

class scraper:
	
	def __init__(self, i_file, focus = 0):
		self.context = paradigm(i_file)

	def run(self, links, limit = 0):
		lines = []	
		with open(links, "r") as f:
			lines = [x.split("\t") for x in f.readlines()]

		print "property_id\tfloorplan_name\tunit_name\tsqft\tbed\tbath\tprice\tavailable_date"
	
	
		count, num = 1, len(lines)
		for line in lines:
			
			sys.stderr.write("Working on %s: %d of %d\n" % (line[1], count, num))
			html = parse(line[1])

			if html == None:
				count += 1
				continue
		
			units = getUnits(html)

			for unit in units:
				try:		

					print printer(unit, line[0])

				except Exception as inst:
					sys.stderr.write(str(inst) + "\n")
			

			if count == limit: break		
			count +=1
	def sample(self, links):
		for eye in self.context.jar():
			

classIDs = ['floorPlan', 'bed', 'bath', 'unit', 'sqft', 'price', 'available', 'button']

def parse(url, tries = 1, redirect = True):
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
						return lxml.fromstring(requests.get("http:" + item.attrib['href']).text)
					except:
						sys.stderr.write("Connection Failed, try: %d\n" % tries)
						time.sleep(3)
						if tries > 3:
							return parse(url, tries + 1, redirect)
						else:
							sys.stderr.write("Connection Failed, Aborting\n")
							return None
				else:
					sys.stderr.write("No Current Availability")
					return None

	return html



 
def pricer(p_range):
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
	
	non_decimal = re.compile(r'[^\d]+')
	out = flag = ''
	
	try:
		if type(p_range) != str:
			"""
			sys.stderr.write(html.base_url())
			sess = dryscape.Session(base_url = p_range[2])
			sess.visit('')
			sess.eval_script(p_range[1])
			time.sleep(3)
			p_range = sess.at_xpath('//span[@id="spRent"]').text()
			"""
			if 'rent' in p_range[1].lower():
				out = p_range[1]
			else:	
				#try the javascript jazz
				out = p_range[0].split(" ")[0]
				flag = "*"
		else:
			out = p_range
		
		
	 	

	except Exception as inst:
		sys.stderr.write(str(inst))
		flag = '*'
	
	finally:
		return non_decimal.sub('', out) + flag
	

def avail(i_date):
	if "now" in i_date.lower():
		today = date.today()
		return "%s/%s/%s" % (today.month, today.day, today.year)
	else: return i_date

def printer(unit, propID):
	return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % 	(	propID,
							unit['floorPlan'],
							unit['unit'],
							unit['sqft'],
							unit['bed'],
							unit['bath'],
							pricer(unit['price']),
							avail(unit['available'])
							)


def link(node):
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
	
	

def getUnits(html):
	units = []
	w_unit = {}
	for tag in html.xpath("//tr"):
		for subtag in tag.xpath("td[@class]"):
			string = subtag.attrib['class']
			
			if string in classIDs:
				w_unit[string] = link(subtag)

		if len(w_unit) == 8: units.append(w_unit)	
		w_unit = {}

	for unit in units:
		try:	
			p_range, b_title, b_link = unit['price'][0], unit['button'][0], unit['button'][1]	
			if len(p_range) > 8:

				if 'request' in b_title.lower() and b_link != '':
					html = parse("http:" + b_link, 1, False)
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

def main(direc):
	lines = []	
	with open(direc, "r") as f:
		lines = [x.split("\t") for x in f.readlines()]

	print "property_id\tfloorplan_name\tunit_name\tsqft\tbed\tbath\tprice\tavailable_date"
	
	
	count, num = 1, len(lines)
	for line in lines:
		sys.stderr.write("Working on %s: %d of %d\n" % (line[1], count, num))
		html = parse(line[1])

		if html == None:
			count += 1
			continue
		
		units = getUnits(html)

		for unit in units:
			
			#try:		
			#print unit
			print printer(unit, line[0])

			#except Exception as inst:
				#sys.stderr.write(str(inst))
				#pass
		count +=1

main("csv/Link 8.csv")




