#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Make MatchSum data for making MTurk csv.
Using a lookup file, match the output files from MatchSum to the original names in the Wikipedia data and output a JSON file to input into make_MTurk_csv.py.

Input = all dec files from MatchSum + list of persons (from raw Wikipedia data) + lookup list for names (due to encoding problems on Linux)
Output = json file with persons as keys and summaries as values. One per gender. (like the textrank file)
"""
import glob
import json, jsonlines
import re
import string
from nltk.tokenize import word_tokenize

input_path = "resources/MatchSum/result/MatchSum_cnndm_roberta.ckpt"
output_path = "data/summaries"

def make_person_lookup_dict(gender):
	lookup_dict = {}
	lookup_input = open(f"{input_path}/{gender}/dec/lookup.txt").readlines()
	for line in lookup_input:
		n, name, approximation = line.split("\t")
		lookup_dict[approximation.strip()] = name
	return lookup_dict

def clean_text():
	pass
	#"".join([" "+i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).strip()

def main():
	genders = ["women"] # "men"

	for gender in genders:

		output = {}
		people = set()
		with jsonlines.open(f"data/wikipedia_matchsum/en_{gender}.jsonl") as f:
			for line in f.iter():
				people.add(line["person"])
		input_summaries = glob.glob(f"{input_path}/{gender}/dec/*")

		lookup_dict = make_person_lookup_dict(gender)
		for file_name in input_summaries:
			#text = " ".join(word_tokenize(open(file_name, encoding="utf-8").read()))
			text = open(file_name, encoding="utf-8").read()
			text = "".join([""+i if not i.startswith("'") and i not in string.punctuation else i for i in text]).strip()
			approximated_name = file_name.split("/")[-1]
			if approximated_name in lookup_dict:
				real_name = lookup_dict[approximated_name]
				output[real_name] = text
			else:
				if approximated_name == "lookup.txt": continue
				print("This person is not in the look up dictionary:\t", approximated_name)
		assert(len(output)==len(input_summaries)-1)

		with open(f"{output_path}/en_{gender}_matchsum.json", "w") as outfile:
			json.dump(output, outfile, sort_keys=True, indent=4,)

if __name__ == "__main__":
	main()