import json
import nltk 
import nltk.data
import numpy as np
import re
import textstat

from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
"""
	Make vector representations of summaries and do experiment
"""

class MakeVectors():
	def __init__(self, biography_representations):
		self.biography_representations = biography_representations
		self.data = {"X": [], "Y": []}

	# ======================= Vector representation ===============
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

	def _get_average_word_length(self, summary):
		# Returns the average word length of the summary.
		words = summary.split()
		average = sum(len(word) for word in words) / len(words)
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

	def _get_features(self, summary, biography):
		# Returns the features for a summary.
		vector = self._get_onehot_vector(summary)
		average_word_length = self._get_average_word_length(summary)
		first_sentence_included = self._check_first_sentence(summary, biography)
		type_token = self._get_type_token(summary)
		text_complexity = self._get_text_complexity(summary)
		vector = np.append(vector, [average_word_length, first_sentence_included, type_token, text_complexity])

		return vector

	def make_vector_representations(self):
		# Make vector representation for each summary pair.

		for br in self.biography_representations:
			
			biography = self._clean_text(self.biography_representations[br]["biography"])
			textrank = self._clean_text(self.biography_representations[br]["textrank"])
			matchsum = self._clean_text(self.biography_representations[br]["matchsum"])

			# Vector representation:
			textrank_features = self._get_features(textrank, biography)
			matchsum_features = self._get_features(matchsum, biography)
			vector_representation = np.append(textrank_features, matchsum_features)
			self.data["X"].append(vector_representation)

			# Exclude "neither" or include in "other" class?
			#if biography_representations[br]["summary_preference"] == "neither": continue

			# Gold:
			# 1 (= female_under30_nonwhite_textrank)?
			if ( self.biography_representations[br]["summary_preference"] == "textrank" and 
				 self.biography_representations[br]['demographics'] == {"agegroup": "under30", "gender": "female", "race": "nonwhite"}):
				y = 1
			else:
				y = 0

			self.data["Y"].append(y)
		assert(len(self.data["Y"]) == len(self.data["X"]))
		return self.data

			
def main(biography_representations):
	data = MakeVectors(biography_representations).make_vector_representations()
	
if __name__ == "__main__":
   	main(json.load(open("data/analyses/biography_representations_all.json")))
