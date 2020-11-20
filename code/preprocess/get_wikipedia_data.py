#!/usr/bin/python3
# -*- coding: utf-8 -*-
""" 
Get summaries from Wikipedia (based on an input file with the title of the Wikipedia page. 
This input file is created using "men" and "women" subcategories on Wikidata.
English only. 
For other languages, get title of Wikipedia page, something like this:
	https://www.wikidata.org/w/api.php?action=wbgetentities&format=xml&props=sitelinks&ids=Q19675&sitefilter=frwiki
"""

import argparse
import json
from Wikipedia.wikipedia import wikipedia
from Wikipedia.wikipedia.exceptions import DisambiguationError, PageError

parser = argparse.ArgumentParser(description='''''')
parser.add_argument("language", default="en")
parser.add_argument("gender", default="women")

args = parser.parse_args()

def get_summary(event):
	""" Extract summary from Wikipedia """
	print(event)
	try:
		event = '_'.join(x for x in list(event.strip().split()))	
		try: 
			return wikipedia.summary(event)
		except (DisambiguationError, PageError, KeyError) as e: 
			return None

	except ValueError:
		print("this event is not processed", line)
		return None

def process_line(line):
	""" Process line, and use the article title on Wikipedia extracted from Wikidata """

	line_dict = {}
	if not line.startswith("http://www.wikidata.org/entity/"): return None, None
	event = line.strip().split("\t")[-1]

	summary = get_summary(event)
	if summary is None: return None, None

	# restrict text length?
	text_length = len(summary)

	line_dict["text"] = summary
	line_dict["text_length"] = text_length

	return event, line_dict

def main():
	# NB: the input_data file does not exist and must be re-established.
	input_data = open(f"resources/{args.language}_{args.gender}.tsv").readlines()
	output_dictionary = {}
	wikipedia.set_lang(args.language)

	for line in input_data:
		event, line_rep = process_line(line)
		if line_rep is None: continue
		output_dictionary[event] = line_rep
		
	with open(f"data/summaries/input/wikipedia_raw/{args.language}_{args.gender}_summaries.json", 'w') as outfile:
		json.dump(output_dictionary, outfile, indent=4)

if __name__ == "__main__":
	main()