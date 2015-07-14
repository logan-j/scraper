from scrapetools import *
from scrape import *
from glob import glob
from sets import Set
import re
import subprocess
import argparse
import sys
import traceback
import os
import shutil

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

	parser.add_argument('-c', '--conglomerate',
		action='store_true',
		help='After the combined input file finishes, it cleans the temporary directory and combines the outputs',
		default=False)

	parser.add_argument('infile',
		nargs='?',
		type=str)

	parser.add_argument('outfile',
		nargs='?',
		type=argparse.FileType('w+'),
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
		print "Reading infile..."
		time.sleep(1)
		try:
			with open(args.infile, "r") as infile:
				for line in infile.readlines():
					cells = re.split(",|\t", line)
					link_type = re.sub("\W", '', cells[3].lower().strip())
					if out.has_key(link_type):
						out[link_type].append(line)
					else:
						out[link_type] = [line]
		except Exception as inst:
			sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
			traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
		print "Making directories..."
		time.sleep(1)

		try:
			if not os.path.exists("tmp/output"):
				os.makedirs("tmp/output")
		except Exception as inst:
			sys.stderr.write("Cannot create 'tmp' directory. Please try again.\n")
		print "Making temporary files..."
		time.sleep(1)

		for key, val in dict.iteritems(out):
			try:
				with open('tmp/%s.csv' % key, 'w') as o_file:
					o_file.write("".join(val))
			except Exception as inst:
				sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
				traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
		print "Reading temporary files..."
		time.sleep(1)

		files = glob("tmp/*.csv")
		mapping = 	{
					"link8": 0, "link55": 1, 
					"link96": 2, "avalonbay": 3, 
					"link53": 4, "link 97": 5, 
					"mac": 5, "aimco": 6
					}

		processes = []
		print "Formulating temp file names..."
		time.sleep(1)

		for f in files:
			name = re.split("/|\.|\\\\", f)[1]
			persp = mapping.get(name)
			print "Spawning process..."
			time.sleep(1)

			if persp != None:
				try:
					processes.append(subprocess.Popen(['python main.py -p %d %s %s' % (persp, f, 'tmp/output/%s.csv' % name)], shell=True))
				except Exception as inst:
					sys.stderr.write(Fore.RED + "%s, %s, %s\n" % (sys.exc_info()[0], inst, inst.args) + Fore.RESET)
					traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			else:
				sys.stderr.write("Unsupported Link Type: %s.\nIf this is in Error, please check link type name.\n" % name)
		print "Attempting conglomeration..."
		time.sleep(1)

		if args.conglomerate:
			try:
				while(list(Set([x.poll() for x in processes])) != [0]):
					time.sleep(5)
				outputs = glob("tmp/output/*.csv")
				args.outfile.write("property_id\tfloorplan_name\tunit_name\tsqft\tbed\tbath\tprice\tavailable_date\n")

				for out in outputs:
					with open(f, 'r') as o_file:
						for line in o_file.readlines()[1:]:

							args.outfile.write(line)
				shutil.rmtree('tmp')
			except Exception as inst:
				sys.stderr.write("Error while processing output: %s." % str(inst))
			
		
		

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
