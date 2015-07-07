from scrapetools import *
from scrape import *
import subprocess
import argparse
import sys
import traceback
import os

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
		help='Specify the PER-th perspective to use, indexed started from 0. Default value will use link type specified in input file',
		default=[-1])

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
	
	elif args.per[0] < 0:
		out = {}
		with open(args.infile, "r") as infile:
			for line in infile.readlines():
				cells = re.split(",|\t", line)
				link_type = cells[3].lower().strip()
				if out.has_key(link_type):
					out[link_type].append(line)
				else:
					out[link_type] = [line]
		try:
			if not os.path.exists("tmp/output"):
				os.makedirs("tmp/output")
		except Exception as inst:
			sys.stderr.write("Cannot create 'tmp' directory. Please try again.\n")

		for key, val in dict.iteritems(out):
			with open('tmp/%s.csv' % key, 'w') as o_file:
				o_file.write("".join(val))


		#subprocess.Popen(['python scrape.py ', shell=True])


		
		
		

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


if __name__ == '__main__':
	main()
