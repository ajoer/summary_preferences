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
	Bootstrapping on MTurk preferences for significance testing. 
	Bonferroni cutoff is implemented to take several testing settings into account. 

"""

class Bootstrapping():
	def __init__(self, biography_representations, gender, race_division):
		self.biography_representations = biography_representations
		self.gender = gender
		self.race_division = race_division
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
		interest_group_preferences = []
		rest_preferences = []

		for person in self.biography_representations:
			if demographic_group in self.biography_representations[person]["demographic_group"]:
				interest_group_preferences.append(self.biography_representations[person]["summary_preference"])
			else:
				rest_preferences.append(self.biography_representations[person]["summary_preference"])
		if len(interest_group_preferences) < 20: 
			return None, None
		return interest_group_preferences, rest_preferences

	def _bootstrap(self, comparison_data, interest_group, total_comparisons):
		rounds = 1000
		sample_size = len(comparison_data["interest_group_preferences"])+len(comparison_data["rest_preferences"])
		bonferroni_cutoff = 0.05/total_comparisons

		won_rounds = Counter()
		
		for r in range(rounds):
			interest_group_set = []
			rest_set = []

			for s in range(sample_size):
				interest_group_set.append(random.sample(comparison_data["interest_group_preferences"], 1)[0])
				rest_set.append(random.sample(comparison_data["rest_preferences"], 1)[0])

			interest_group_counter = Counter(interest_group_set)
			rest_counter = Counter(rest_set)

			if interest_group_counter["textrank"] > rest_counter["textrank"]:
				won_rounds[interest_group] += 1
			else:
				won_rounds["rest"] += 1

		for group in won_rounds:
			won_rounds[group] = won_rounds[group]/rounds


		if bonferroni_cutoff > won_rounds[interest_group] or won_rounds[interest_group] > (100-bonferroni_cutoff):
			score = won_rounds[interest_group]/won_rounds['rest']
			return True, score, bonferroni_cutoff
		else:
			return False, 0, 0

	def compare_demographic_groups(self):
		self._get_demographic_groups()

		with open(f'analyses/{self.race_division}/{self.gender}/bonferroni.tsv', 'w') as f:

			f.write("demographic_group\tpvalue\tbonferroni_cutoff\t#comparisons\n")

			for demographic_class in self.demographic_representations:
				
				comparison_data = {}

				for interest_group in self.demographic_representations[demographic_class]:
					interest_group_preferences, rest_preferences = self._get_group_preferences(interest_group)
					if interest_group_preferences == None: 
						continue
					comparison_data[interest_group] = {
						"interest_group_preferences": interest_group_preferences,
						"rest_preferences": rest_preferences
					}

				total_comparisons = sum(list(range(1, len(comparison_data.keys()))))
				for interest_group in comparison_data:
					result, score, bonferroni_cutoff = self._bootstrap(comparison_data[interest_group], interest_group, total_comparisons)
					if result == True:
						f.write(f"{interest_group}\t{score}\t{bonferroni_cutoff}\t{total_comparisons}\n")

if __name__ == "__main__":
	for gender in ['both', 'men', 'women']: # both, men or women
		for race_division in ['all', 'binary']: # all or binary (white/rest)
			print(f"\nRunning bootstrapping for {gender}")
			biography_representations = json.load(open(f"analyses/{race_division}/{gender}/biography_representations.json"))
			Bootstrapping(biography_representations, gender, race_division).compare_demographic_groups()
