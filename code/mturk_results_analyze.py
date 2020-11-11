import argparse
import copy
import json
import matplotlib.pyplot as plt
import pandas as pd
import statistics as stats
from collections import Counter
from scipy.stats import ttest_ind
from tabulate import tabulate
"""
	Analyze the data from MTurk experiments and get preference distributions. 

	Input: csv file outputted from code/review_mturk_results.py (with approve/reject rating)

	This code does the following:
		- get demographics
		- get preferences

		Compute:
			- preference distribution across demographics for:
				- all biographies
				- women biographies
				- men biographies
			- informativeness, fluency and usefulness distribution across demographics for:
				- all biographies
				- women biographies
				- men biographies

"""

class AnalyzeMTurkData():

	def __init__(self, mturk_data, race_division):
		self.data = mturk_data[mturk_data.Approve == "x"]
		self.biography_representations = {}
		self.race_division = race_division

		self.demographics_distribution = {
			"agegroup": {},
			"gender": {},
			"race": {},
			"gender_race": {},
			"gender_agegroup": {},
			"race_agegroup": {},
			"gender_race_agegroup": {}
		}
		self.ratings = copy.deepcopy(self.demographics_distribution)
		self.preferences = copy.deepcopy(self.demographics_distribution)
		
		self.demographics_dict = {}
		self.workers_per_demo = Counter()
		self.tasks_per_race = Counter()
		self.ages = Counter()

		self.make_demographics_dict()

		if args.gender != "both": self.get_gendered_data(args.gender)

		total = len(self.data)
		self.main()
		

	def get_worker_demographics(self, worker_data): # race_division = binary or all
		# Make worker demographics dictionary
		demographics = {
			"agegroup": None,
			"gender": None,
			"race": None
		}
		
		# Age
		#demographics["age"] = worker_data['Answer.typed_age']

		if worker_data[f'Answer.age.older']:
			demographics["agegroup"] = "over30"
		else:
			demographics["agegroup"] = "under30"

		# Gender
		for gender in ['female', 'male', 'other']:
			if worker_data[f'Answer.gender.{gender}']:
				demographics["gender"] = gender

		# Race
		if self.race_division == "binary":
			if worker_data[f'Answer.race.white']:
				demographics["race"] = "white"
			else:
				demographics["race"] = "nonwhite"

		elif self.race_division == "all":
			for race in ['white', 'black', 'asian', 'american_indian','hispanic', 'other']:
				if worker_data[f'Answer.race.{race}']:
					demographics["race"] = race
		return demographics

	def make_demographics_dict(self):
		# Make dictionary of demographics for workers.
		
		worker_counter = Counter()
		done = []
		
		for index, worker_data in self.data.iterrows():

			worker_counter[worker_data["WorkerId"]] += 1
			demographics = self.get_worker_demographics(worker_data)
			if None in demographics.values(): continue
			self.demographics_dict[worker_data["WorkerId"]] = demographics

		# Add worker demographics to workers_per_demo overview (making sure there are a good number of Turkers per demographic group and get an average # of tasks for each worker)
		for worker_id in self.demographics_dict:

			#self.ages[self.demographics_dict[worker_id]["age"]] += 1

			for demo_variable in self.demographics_dict[worker_id]:
				if demo_variable == "age": continue
				self.workers_per_demo[self.demographics_dict[worker_id][demo_variable]] += 1
				self.tasks_per_race[self.demographics_dict[worker_id][demo_variable]] += worker_counter[worker_id]

				for demo_variable2 in self.demographics_dict[worker_id]:

					if demo_variable2 == "age": continue
					if demo_variable2 == demo_variable: continue
					if (demo_variable, demo_variable2) in done: continue
					done.append((demo_variable, demo_variable2))

					self.workers_per_demo[f"{self.demographics_dict[worker_id][demo_variable]}/{self.demographics_dict[worker_id][demo_variable2]}"] += 1
					self.tasks_per_race[f"{self.demographics_dict[worker_id][demo_variable]}/{self.demographics_dict[worker_id][demo_variable2]}"] += worker_counter[worker_id]

			self.workers_per_demo[f"{self.demographics_dict[worker_id]['race']}/{self.demographics_dict[worker_id]['gender']}/{self.demographics_dict[worker_id]['agegroup']}"] += 1
			self.tasks_per_race[f"{self.demographics_dict[worker_id]['race']}/{self.demographics_dict[worker_id]['gender']}/{self.demographics_dict[worker_id]['agegroup']}"] += worker_counter[worker_id]

		# table = []
		# for i in workers_per_demo:
		# 	table.append([i, workers_per_demo[i], tasks_per_race[i], tasks_per_race[i]/workers_per_demo[i]])
		# print(tabulate(table, tablefmt="latex"))

	def get_gendered_data(self, gender):
		# Make a subset of biographies that are just of one gender.
		genders = ["women", "men"]
		genders.remove(gender)
		gender_biographies = json.load(open(f"data/wikipedia_raw/en_{genders[0]}_summaries.json"))
		wrong_gendered_people = set(gender_biographies.keys())

		self.data = mturk_data[~mturk_data["Input.person"].isin(wrong_gendered_people)]

	def get_preferences(self, worker_data):
		# Make worker preference dictionary
		preferences = {
			"summary": None,
			"informative": {},
			"fluent": {},
			"useful": {}
		}

		# Get summary preference (model)
		if worker_data['Answer.summary_preference.a']:
			preferences["summary"] = worker_data['Input.summary_A_model']

		elif worker_data['Answer.summary_preference.b']:
			preferences["summary"] = worker_data['Input.summary_B_model']
		else:
			preferences["summary"] = "neither"

		# Get rating of summaries
		for summary in ["A", "B"]:
			system_name = worker_data[f'Input.summary_{summary}_model']
			for element in preferences:
				if element == "summary": continue
				for i in range(4):
					if worker_data[f"Answer.{element}_{summary}.{i}"]:
						preferences[f"{element}"][f"{system_name}"] = i
		return preferences


	def make_percentages_ratings(self):
		self.percentage_ratings = copy.deepcopy(self.ratings)
		for demographic_class in self.ratings:
			for representation in self.ratings[demographic_class]:
				if representation == "all": 
					del self.percentage_ratings[demographic_class][representation] 
					continue
				for system in self.ratings[demographic_class][representation]:
					for element in self.ratings[demographic_class][representation][system]:
						total = sum(self.ratings[demographic_class][representation][system][element].values())
						for value in self.ratings[demographic_class][representation][system][element]:
							self.percentage_ratings[demographic_class][representation][system][element][value] = round(self.ratings[demographic_class][representation][system][element][value]/total,2)
							if int(value) < 2: 
								self.percentage_ratings[demographic_class][representation][system][element]["agree"] += self.ratings[demographic_class][representation][system][element][value]
							else:
								self.percentage_ratings[demographic_class][representation][system][element]["disagree"] += self.ratings[demographic_class][representation][system][element][value]
						self.percentage_ratings[demographic_class][representation][system][element]["agree"] = round(self.percentage_ratings[demographic_class][representation][system][element]["agree"]/total,2)
						self.percentage_ratings[demographic_class][representation][system][element]["disagree"] = round(self.percentage_ratings[demographic_class][representation][system][element]["disagree"]/total,2)
	

	def get_demographic_representation(self, demographics, demographic_class):
		elements = demographic_class.split("_")
		if len(elements) == 1:
			representation = demographics[elements[0]]
		elif len(elements) == 2:
			representation = "/".join([demographics[elements[0]], demographics[elements[1]]])
		else:
			representation = "/".join([demographics["gender"], demographics["race"], demographics["agegroup"]])
		
		return representation

	def add_annotations(self, demographics, annotations):
		# Make representation of demographic distribution (e.g. white/female):
		for demographic_class in self.demographics_distribution:
			representation = self.get_demographic_representation(demographics, demographic_class)
			if "other" in representation: continue

			if representation not in self.ratings[demographic_class]:
				self.ratings[demographic_class][representation] = {
					"textrank": {"informative": Counter(), "useful":  Counter(), "fluent":  Counter()}, 
					"matchsum": {"informative":  Counter(), "useful":  Counter(), "fluent":  Counter()}
				}
				self.preferences[demographic_class][representation] = {
					"textrank": 0, "matchsum": 0, "neither": 0
				}

			# Ratings
			for element in annotations:
				if element == "summary": continue
				for system in annotations[element]:
					value = str(annotations[element][system])
					self.ratings[demographic_class][representation][system][element][value] += 1

			# Preferences
			self.preferences[demographic_class][representation][annotations["summary"]] += 1
			

	def get_small_representations(self):
		self.too_small_representations = []

		for demographic_class in self.preferences:
			for representation in self.preferences[demographic_class]:
				total = sum(self.preferences[demographic_class][representation].values())
				
				if total < 20: 
					self.too_small_representations.append(representation)

	def print_preferences(self):
		# Print preferences table
		for demographic_class in self.preferences:
			totals_in_demographic_class = {
				"textrank": 0, 
				"matchsum": 0, 
				"neither": 0
			}
			table = [["Demographics", "TextRank", "%", "MatchSum", "%", "neither", "%"]]

			with open(f'data/analyses/{self.race_division}/preferences_{demographic_class}.txt', 'w') as f:
				for representation in sorted(self.preferences[demographic_class]):
					if representation in self.too_small_representations: continue
					representation_line = [representation]
					representation_total = sum(self.preferences[demographic_class][representation].values())
						
					for system in ["textrank", "matchsum", "neither"]:
						representation_line.append(self.preferences[demographic_class][representation][system])
						representation_line.append(round(100*self.preferences[demographic_class][representation][system]/representation_total,1))
					table.append(representation_line)

				f.write(tabulate(table, tablefmt="latex"))

	def print_ratings(self):
		# Print ratings table
		self.make_percentages_ratings()
		for demographic_class in self.percentage_ratings:
			table = [
				["", "Informative", "", "Useful", "", "Fluent", ""], 
				["Demographics", "TextRank", "MatchSum", "TextRank", "MatchSum", "TextRank", "MatchSum"]
			]

			with open(f'data/analyses/{self.race_division}/ratings_{demographic_class}.txt', 'w') as f:
				for representation in sorted(self.percentage_ratings[demographic_class]):
					representation_data = self.percentage_ratings[demographic_class][representation]
					if representation in self.too_small_representations: continue
					representation_line = [representation]
					for element in representation_data["textrank"]:
						for system in ["textrank", "matchsum"]:
							representation_line.append(representation_data[system][element]['agree'])
					table.append(representation_line)
				f.write(tabulate(table, tablefmt="latex"))
		
		table = [
			["", "Informative", "", "Useful", "", "Fluent", ""], 
			["Demographics", "TextRank", "MatchSum", "TextRank", "MatchSum", "TextRank", "MatchSum"]
		]

		with open(f'data/analyses/{self.race_division}/ratings_total.txt', 'w') as f:
			for value in ["0","1","2","3"]:
				line = [value]
				for element in sorted(self.ratings["gender"]["female"]["textrank"]):
					for system in ["textrank", "matchsum"]:
						total = sum(self.ratings["gender"]["female"][system][element].values())+sum(self.ratings["gender"]["male"][system][element].values())
						line.append(round((self.ratings["gender"]["female"][system][element][value]+self.ratings["gender"]["male"][system][element][value])/total, 2))
				table.append(line)
			f.write(tabulate(table, tablefmt="latex"))

		
	def main(self):
		# Demographic information and stats have been taken out. 
		# Can statistics be made from self.ratings and self.preferences??
		
		for index, worker_data in self.data.iterrows():

			demographics = self.demographics_dict[worker_data["WorkerId"]]
			annotations = self.get_preferences(worker_data)

			# make ratings overviews for all and for each demo group.
			self.add_annotations(demographics, annotations)

			# Make dictionary with demographics of the Turker, and the texts for deeper analysis.
			self.biography_representations[f"{worker_data['Input.person']}_{worker_data['WorkerId']}"] = {
				"person": worker_data['Input.person'],
				"demographics": demographics,
				"summary_preference": annotations["summary"],
				"biography": f"{worker_data['Input.biography']}",
				f"{worker_data['Input.summary_A_model']}": f"{worker_data['Input.summary_A']}",
				f"{worker_data['Input.summary_B_model']}": f"{worker_data['Input.summary_B']}"
			}

		self.get_small_representations()
		self.print_preferences()
		self.print_ratings()

		with open(f"data/analyses/{self.race_division}/biography_representations.json", "w") as outfile:
			json.dump(self.biography_representations, outfile, sort_keys=True, indent=4,)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Process some integers.')
	parser.add_argument('input_file', default="Batch_4235328_batch_results")
	parser.add_argument('--gender', default="both", help='all biographies, only women or only men.')
	args = parser.parse_args()

	mturk_data = pd.read_csv("data/mturk_results/reviewed/Batch_4235328_batch_results_reviewed.csv")

	a = AnalyzeMTurkData(mturk_data, race_division="all")
	a.make_demographics_dict() # race_division = all or binary




