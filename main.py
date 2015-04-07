import argparse
import sys
from scrape import scraper

def main():
	
	parser = argparse.ArgumentParser(description='Scrape general pricing and availability info.')
	parser.add_argument('-n', '--num', type=int, nargs=1, help='Limit the number of links to run to NUM links from beginning.', default=[0])
	parser.add_argument('-p', '--per', type=int, nargs=1, help='Specify the PER-th perspective to use, indexed started from 0.', default=[0])
	parser.add_argument('infile', nargs='?', type=str)
	parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

	args = parser.parse_args()
	sc = scraper("perspectives.yaml", args.infile, args.per[0])
	sc.run(args.num[0])

main()
