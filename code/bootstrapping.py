import json
import nltk 
import nltk.data
import numpy as np
import random
import re
import textstat

from collections import Counter
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
"""
	Bootstrapping on MTurk preferences.

"""

class Bootstrapping():
	def __init__(self, biography_representations):
		self.biography_representations = biography_representations
		self.demographic_representations = {
			"agegroup": [],
			"gender": [],
			"race": [],
			"gender_race": [],
			"gender_agegroup": [],
			"race_agegroup": [],
			"gender_race_agegroup": []
		}

	def _get_representations(self, demographics):

		representations = []
		for key in list(self.demographic_representations.keys()):
			elements = key.split("_")

			if len(elements) == 1:
				rep = demographics[key]
			elif len(elements) == 2:
				rep = "/".join([demographics[elements[0]], demographics[elements[1]]])
			else:
				rep = "/".join([demographics["gender"], demographics["race"], demographics["agegroup"]])

			if "other" in rep: continue
			if not rep in self.demographic_representations[key]:
				self.demographic_representations[key].append(rep)
			representations.append(rep)

		return representations
			
	def _get_demographic_groups(self):
		for person in self.biography_representations:
			demographics = self.biography_representations[person]["demographics"]
			representations = self._get_representations(demographics)
			self.biography_representations[person]["demographic_group"] = representations

	def _get_group_preferences(self, demographic_group):
		group_preferences = []
		for person in self.biography_representations:
			if demographic_group in self.biography_representations[person]["demographic_group"]:
				group_preferences.append(self.biography_representations[person]["summary_preference"])
		if len(group_preferences) < 20: 
			return None
		return group_preferences

	def _bootstrap(self, group1_preferences, group2_preferences, group1, group2):
		won_rounds = Counter()
		rounds = 1000
		sample_size = 100
		cut_off = 0.05

		for r in range(rounds):
			group1_set = []
			group2_set = []

			for s in range(sample_size):
				group1_set.append(random.sample(group1_preferences, 1)[0])
				group2_set.append(random.sample(group2_preferences, 1)[0])

			first = Counter(group1_set)
			second = Counter(group2_set)
			if first["textrank"] > second["textrank"]:
				won_rounds[group1] += 1
			else:
				won_rounds[group2] += 1
		won_rounds[group1] = won_rounds[group1]/rounds
		won_rounds[group2] = won_rounds[group2]/rounds

		if cut_off > won_rounds[group1] or won_rounds[group1] > (100-cut_off):
			print(f"Significant result between {group1} and {group2}:\t{won_rounds[group1]}/{won_rounds[group2]}") 


	def compare_demographic_groups(self):
		self._get_demographic_groups()
		for demographic_class in self.demographic_representations:
			done = []
			print(f"\nComparisons within {demographic_class}\n")
			for group1 in self.demographic_representations[demographic_class]:
				group1_preferences = self._get_group_preferences(group1)
				if group1_preferences == None: continue

				for group2 in self.demographic_representations[demographic_class]:
					if group1 == group2: continue
					if (group2, group1) in done: continue
					done.append((group1, group2))

					group2_preferences = self._get_group_preferences(group2)
					if group2_preferences == None: continue

					self._bootstrap(group1_preferences, group2_preferences, group1, group2)

def main(biography_representations):

	Bootstrapping(biography_representations).compare_demographic_groups()
	
if __name__ == "__main__":
   	main(json.load(open("analyses/all/biography_representations.json")))
