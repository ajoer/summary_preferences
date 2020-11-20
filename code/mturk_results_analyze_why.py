import csv
import json
import nltk 
import nltk.data
import numpy as np
import operator
import re
import textstat

from matplotlib import pyplot
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
"""
	Make vector representations of summaries and do experiment
"""

class MakeVectors():
	def __init__(self, gender, race_division):
		self.biography_representations = json.load(open(f"analyses/{race_division}/{gender}/biography_representations.json"))
		self.word_lengths = {"matchsum": [], "textrank": []}
		self.data = {}
		self._make_datadict(csv.reader(open(f"analyses/{race_division}/{gender}/bonferroni.tsv"), delimiter="\t"))
		
	def _make_datadict(self, significant_results):
		for n,result in enumerate(significant_results):
			if n == 0: continue
			self.data[result[0]] = {"X": [], "Y": []}

	def _get_representations(self, demographics):

		representations = []
		for element in sorted(demographics):
			first_level = demographics[element]
			if first_level in self.data:
				representations.append(first_level)

			for element2 in sorted(demographics):
				second_level = f"{demographics[element]}/{demographics[element2]}"
				if second_level in self.data:
					representations.append(second_level)

		third_level = f"{demographics['gender']}/{demographics['race']}/{demographics['agegroup']}"
		if third_level in self.data:
			representations.append(third_level)

		return representations


	def _clean_text(self, text):
		# remove additional spaces:
		text = re.sub(' +', ' ', text)
		return text
		
	def _get_onehot_vector(self, summary):
		# make one-hot vector representation of stop words in summaries.
		vectorizer = CountVectorizer()
		vocab = stopwords.words('english') 
		vectorizer.fit(sorted(vocab))
		vector = vectorizer.transform([summary])
		return vector.toarray()[0]

	def _get_average_word_length(self, summary, system):
		# Returns the average word length of the summary.
		words = summary.split()
		average = sum(len(word) for word in words) / len(words)
		self.word_lengths[system].append(average)
		return average

	def _check_first_sentence(self, summary, biography):
		# Returns 1 if biography's first sentence is also the first sentence in summary, else 0.
		sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
		summary_first = sent_detector.tokenize(summary.strip())[0]
		biography_first = sent_detector.tokenize(biography.strip())[0]
		if summary_first == biography_first:
			return 1
		else: 
			return 0

	def _get_type_token(self, summary):
		# Returns the type/token ratio
		words = nltk.tokenize.word_tokenize(summary)
		return len(set(words)) / len(words)

	def _get_text_complexity(self, summary):
		complexity = textstat.text_standard(summary, float_output=True)
		return(complexity)

	def _get_features(self, summary, biography, system):
		# Returns the features for a summary.
		vector = self._get_onehot_vector(summary)
		average_word_length = self._get_average_word_length(summary, system)
		first_sentence_included = self._check_first_sentence(summary, biography)
		type_token = self._get_type_token(summary)
		text_complexity = self._get_text_complexity(summary)
		vector = np.append(vector, [average_word_length, first_sentence_included, type_token, text_complexity])

		return vector


	def make_vector_representations(self):
		# Make vector representation for each summary pair.

		print("Making vector representations")
		for br in self.biography_representations:
			demographics = self.biography_representations[br]["demographics"]

			representations = self._get_representations(demographics)
			
			biography = self._clean_text(self.biography_representations[br]["biography"])
			textrank = self._clean_text(self.biography_representations[br]["textrank"])
			matchsum = self._clean_text(self.biography_representations[br]["matchsum"])

			# Vector representation:
			textrank_features = self._get_features(textrank, biography, "matchsum")
			matchsum_features = self._get_features(matchsum, biography, "textrank")
			vector_representation = np.append(textrank_features, matchsum_features)
			
			if self.biography_representations[br]["summary_preference"] == "textrank":
				y = 1
			elif self.biography_representations[br]["summary_preference"] == "matchsum":
				y = 0

			else: continue # if preference == 'neither'

			for rep in representations:
				self.data[rep]["Y"].append(y)
				self.data[rep]["X"].append(vector_representation)

		for rep in self.data:
			assert(len(self.data[rep]["Y"]) == len(self.data[rep]["X"]))

		print("average word length MatchSum:", sum(self.word_lengths["matchsum"])/len(self.word_lengths["matchsum"]))
		print("average word length TextRank:", sum(self.word_lengths["textrank"])/len(self.word_lengths["textrank"]))
		return self.data

class TextClassification():
	def __init__(self, gender, race_division):

		print("Starting text classification")
		self.gender = gender
		self.race_division = race_division
		self.input_data = MakeVectors(self.gender, self.race_division).make_vector_representations()
		self.main()

	def _split_data(self, data):

		scaler = StandardScaler()
		data["X"] = scaler.fit_transform(data["X"])

		split = int(round(len(data["X"])*0.2,0))
		classification_data = {
			"train_X": data["X"][split:], 
			"train_Y": data["Y"][split:], 
			"test_X": data["X"][:split], 
			"test_Y": data["Y"][:split]
		}
		return classification_data

	def main(self):
		
		top20_dict = {}
		for rep in self.input_data:
			print(f"--------- {rep} ---------")
			top20_dict[rep] = {
				"score": 0, 
				"top20_features": []
			}

			classification_data = self._split_data(self.input_data[rep])
			clf = LogisticRegression(random_state=0, max_iter=1000).fit(classification_data["train_X"], classification_data["train_Y"])
			top20_dict[rep]["score"] = clf.score(classification_data["test_X"], classification_data["test_Y"])

			importance = clf.coef_
			indexed = list(enumerate(importance[0])) # attach indices to the list
			top_20 = list(reversed([i for i, v in sorted(indexed, key=operator.itemgetter(1))[:20]]))
			top20_features = []
			non_stop_words = {
				"146": "average_word_length",
				"147": "first_sentence_included",
				"148": "type_token",
				"149": "text_complexity"
			}

			vocab = stopwords.words('english')
		
			for index in top_20:
				if index > 150: model = "m"
				else: model = "t"

				index=index-149

				if str(index) in non_stop_words: feature = f"{model}_{non_stop_words[str(index)]}"
				else: feature = f"{model}_{vocab[index]}"				
				top20_features.append(feature)
			top20_dict[rep]["top20_features"] = top20_features

		with open(f"analyses/{self.race_division}/{self.gender}/top20_features.json", "w") as outfile:
			json.dump(top20_dict, outfile, sort_keys=True, indent=4,)
		
if __name__ == "__main__":
	for gender in ['both', 'men','women']: # both, men or women
		for race_division in ['all', 'binary']: # all or binary (white/rest)
			print(f"\nRunning for {race_division} race division on {gender} gendered biographies")
			TextClassification(gender, race_division)
