import json
import re
from nltk import sent_tokenize, word_tokenize

gender = "women"

input_data = json.load(open(f"data/wikipedia_raw/en_{gender}_summaries.json"))

def save_to_jsonl(output_data, index_data):

	with open(f'data/wikipedia_matchsum/en_{gender}_index.jsonl', 'w') as outfile:		
	    for entry in index_data:
	        json.dump(entry, outfile)
	        outfile.write('\n')

	with open(f'data/wikipedia_matchsum/en_{gender}.jsonl', 'w') as outfile:		
	    for entry in output_data:
	        json.dump(entry, outfile)
	        outfile.write('\n')

def main():

	output_data = []
	index_data = []

	for person in sorted(input_data):
		text = input_data[person]["text"]
		sentences = sent_tokenize(text)

		out_sentences = []
		for s in sentences:
			tok_sent = ' '.join(word_tokenize(s))
			clean_sent = re.sub( r'([,.!])([a-zA-Z])', r'\1 \2', tok_sent)
			out_sentences.append(clean_sent)
		
		n_sentences = len(out_sentences) 
		# Biographies should be 5 sentences long. Summaries should be (2 or) 3 long.
		if n_sentences < 5: continue
		elif n_sentences > 5: out_sentences = out_sentences[:5]

		sent_ids = [x for x in range(len(out_sentences))]

		index_data.append({"person": person, "sent_id": sent_ids})
		output_data.append({
			"person": person, 
			"text": out_sentences,
			"summary": out_sentences[:3]})

	print("Number of biographies:\t", len(output_data))
	save_to_jsonl(output_data, index_data)


if __name__ == "__main__":
	main()
