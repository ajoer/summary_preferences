"""
	Make MTurk input data with biography and two summaries.
	Input:
		- textrank summaries
		- MatchSum summaries
		- original biographies
	Output:
		csv file with the following information per person: 
			"person", "biography", 
			"summary_A", "summary_B", 
			"summary_A_model", "summary_B_model" --> this refers to the order of the summaries to show to Turkers, either "matchsum" or "testrank"
"""
import csv
import json
import random
import string
import tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer

# The exclude list consists of the names of persons, where the extracted biography doesn't match.
# This has been determined through manual inspection.
# These names should be excluded from the experiment.
exclude_women = [
	"Ashoka", "Monika Hunnius", "Pauline Krone", "Ramabai Ranade", "Brenda Strong", "Charlotte Beradt", 
	"Mathilde Raven", "Kirsten Boie", "Riitta Pitkänen", "Rujuta Diwekar", "Livia Ana Tătaru", 
	"Martha Müller-Grählert", "Henriette Richter-Röhl", "Oceana", "Emil Marriot"]
exclude_men = [
	"Mars", "Augustus", "Trajan", "Ramesses III", "Ramesses VI", "Cvijetin Todić", 
	"Marcel Doret", "Boris Kryštufek", "Emperor An of Han", "Saladin", "Rüdiger Skoczowsky", 
	"Dominic Sanz", "Enrique Santos Montejo", "Raimo Ekholm", "Seppo Hannula", "Lassi Huuskonen", 
	"Pekka Hyvärinen", "Akseli Lajunen", "Bernd Baumgartl", "Dietrich Haarer", "Karl-Heinz Vorsatz", 
	"Franz Maciejewski", "Jarkko Saapunki", "Pauli Ukkonen", "Philip  Hurepel", "Scott Koziol", "Asterios", "Cyrus the Great"]
exclude = set(exclude_women + exclude_men)

genders = ["women", "men"]

def get_bios():
	# Make one dict with all biogrtaphies (women and men together).
	biographies = {}
	for gender in genders:
		gender_bios = json.load(open(f"data/wikipedia_raw/en_{gender}_summaries.json")) 
		print(f"there are {len(gender_bios)} people in the {gender} biography file")
		biographies = {**biographies, **gender_bios} 
	return biographies

def detokenize(summary):
	# Remove tokenization for MTurkers.
	untokenized = summary.replace(' ,',',').replace(' .','.').replace(' ;',';').replace(' !','!').replace('`` ','``').replace(" ''","''")  
	untokenized = untokenized.replace(' ?','?').replace(' :',': ').replace(' \'', '\'').replace('( ', '(').replace(' )', ')').replace('\n',' ')  
	return untokenized

def person_data():
	# Combine the biography and summaries for each person.
	summary_models = ["textrank", "matchsum"]
	output = []

	total_number_of_people = 0
	excluded = 0

	for gender in genders:
		biographies = json.load(open(f"data/wikipedia_raw/en_{gender}_summaries.json")) 
		summaries = {
			"textrank_summaries": json.load(open(f"data/summaries/en_{gender}_textrank.json")),
			"matchsum_summaries": json.load(open(f"data/summaries/en_{gender}_matchsum.json")) 
		}
		people = list(biographies.keys())
		number_of_people = len(people)
		total_number_of_people += number_of_people

		for i in range(number_of_people):
			person = random.choice(people)
			people.remove(person)

			if person in exclude: continue
			
			# Person data:
			biography = biographies[person]["text"].strip()
			model_A = random.choice(summary_models)
			model_B = [model for model in summary_models if model is not model_A][0]

			summaries_from_A = summaries[f"{model_A}_summaries"]
			summaries_from_B = summaries[f"{model_B}_summaries"]

			if person in summaries_from_A.keys() and person in summaries_from_B.keys():
				summary_A = detokenize(summaries_from_A[person].strip())
				summary_B = detokenize(summaries_from_B[person].strip())

				person_output = [person, biography, summary_A, summary_B, model_A, model_B]
				output.append(person_output)
			else:
				excluded += 1

	print(f'There are {total_number_of_people} biographies in the input dataset and {len(output)} in the output data.')
	print(f'{excluded} people have been excluded.')
	return output

def write_out():
	header = ["person", "biography", "summary_A", "summary_B", "summary_A_model", "summary_B_model"]
	
	data = person_data()
	output_data = random.sample(data, len(data))
	with open('data/mturk/input/MTurk_input.csv', 'w') as f:
		csv_writer = csv.writer(f)
		csv_writer.writerow(header)

		for n in range(len(output_data)):
			#person_row = random.choice(output_data)
			#print(output_data[n][0])
			csv_writer.writerow(output_data[n])
			#output_data.remove(person_row)

if __name__ == "__main__":
	write_out()