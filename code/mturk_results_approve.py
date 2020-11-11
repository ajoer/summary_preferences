import pandas as pd
import sys
from collections import Counter
from statistics import stdev
from tabulate import tabulate
"""
	Review the data from MTurk experiments to approve and reject work. 

	Input: csv file from MTurk results page
	Output: csv file with approve/reject for each task/worker. This can be directly uploaded to MTurk for approval/rejection.


	Checks the following:

	ID:
	0) check that all workers are unique

	demographics:
	1) check for each worker whether they have filled in the demographic information at least once.
	2) check for each worker whether there are any discrepancies in the demographic information.
	3) check whether the age inputs correspond

	task:
	4) check for each worker for each task whether the information is complete
	5) for each worker count how many tasks they have completed.  

"""

input_data = pd.read_csv(f"data/mturk_results/{sys.argv[1]}.csv") # "data/mturk_results/Batch_4209166_batch_results.csv")

# Unique worker IDs:
def check_unique_IDs():
	# Use this to check the distribution of tasks across workers.
	worker_ids = input_data['WorkerId']
	if len(worker_ids) != len(set(worker_ids)):
		print("The same worker did more than one task")
		print(Counter(worker_ids))

def demographics_complete(worker_data):
	# Verify whether each demographic element has an answer, i.e. one True value per element options.
	
	demographic_columns = {
		"age": ['Answer.age.30', 'Answer.age.older', 'Answer.age.younger'], #, 
		"gender": ['Answer.gender.female', 'Answer.gender.male', 'Answer.gender.other'],
		"race": ['Answer.race.american_indian','Answer.race.asian', 'Answer.race.black', 
			'Answer.race.hispanic', 'Answer.race.other', 'Answer.race.white']
	}

	for demographic_element in demographic_columns:
		if not True in [worker_data[column] for column in demographic_columns[demographic_element]]:
			reason = f"missing {demographic_element}"
			return False, reason
	
	if not worker_data["Answer.typed_age"]:
		reason = "missing typed age"
		return False, reason

	return True, ""
			
def verify_demographics(worker_data):
	# Verify that the demographics are complete and have no discrepancies. 
	# Return True (verified) or False (rejected).
	# Reject worker if incomplete demographics
	complete, reason = demographics_complete(worker_data)
	if not complete:
		return False, f"Incomplete demographics ({reason})"

	verified = True
	reason = ""

	# Reject worker if discrepancies in age:
	age = worker_data["Answer.typed_age"]
	if worker_data["Answer.age.younger"] == True:
		if age >= 30:
			reason = f"Discrepancies in age. You put that you are younger than 30, but typed that you are {age}. As mentioned in the instructions, this is grounds for rejection."
			verified = False
	elif worker_data["Answer.age.older"] == True:
		if worker_data["Answer.typed_age"] <= 30:
			reason = f"Discrepancies in age. You put that you are older than 30, but typed that you are {age}. As mentioned in the instructions, this is grounds for rejection."
			verified = False
	elif worker_data["Answer.age.30"] == True:
		if worker_data["Answer.typed_age"] != 30:
			reason = f"Discrepancies in age. You put that you are 30, but typed that you are {age}. As mentioned in the instructions, this is grounds for rejection."
			verified = False

	# if worker_data["WorkerId"] in double_check:
	# 	print(worker_data["WorkerId"], race)
	return verified, reason

def verify_task_completion(worker_data):
	# Verify whether each task element has an answer, i.e. one True value per element options.
	for task_element in ["informative", "fluent", "useful"]:
		for letter in ["A", "B"]:
			if not True in [worker_data[f'Answer.{task_element}_{letter}.{num}'] for num in range(4)]:
				reason = f"You did not rate the element '{task_element}' for summary {letter}. As mentioned in the instructions, this is grounds for rejection."
				return False, reason

	if not True in [worker_data[f'Answer.summary_preference.{letter}'] for letter in ["a", "b", "non"]]:
		reason = "Missing summary preference entry. As mentioned in the instructions, this is grounds for rejection."
		return False, reason

	return True, ""

def get_minimum_worktime():
	# Get average normalized worktime, and standard deviation. 
	# Used to exclude workers who spend too little time on task.
	normalized_worktimes = {}
	remove_workers = []
	
	for index, worker_data in input_data.iterrows():
		time = worker_data["WorkTimeInSeconds"]
		words = len(worker_data["Input.biography"].split())
		normalized_worktime = time/words
		normalized_worktimes[worker_data["WorkerId"]] = normalized_worktime

	average = sum(normalized_worktimes.values())/len(normalized_worktimes)
	standard_deviation = stdev(list(normalized_worktimes.values()))
	minimum_worktime = average-standard_deviation

	return normalized_worktimes, minimum_worktime

def main():

	# These workers have previously been rejected wrongly. Make sure their results are preapproved.
	preapproved_workers = ["A1VRXZADIKWB4S", "A3NYIJYBHAJ74V", "AD82Z4ROMFRU2", "ADLKIX3SBFREV", "A30HK6LL0LCCHF", "A1V3QAZJ9ERJMJ", "A3ANS61F3A656X", "A39ZO6TXOGQLP0"]+["AWCMWOLXMZAAC","A1VRXZADIKWB4S", "AWCMWOLXMZAAC", "A3BDTPHXKVWQRG", "AOEO9ZV81R0I4", "A3559VD53E2JYY", "A2VPVY1PY9H4T4", "AHE1TAVA2UK5F", "AI3LZF99ECT58", "AHE1TAVA2UK5F", "A2VPVY1PY9H4T4", "A3TUNUJES9PQ5Q", "A1XCQTUCGFSG14", "AWCMWOLXMZAAC", "A3BDTPHXKVWQRG", "A3BG20JPQLNKE1", "A13YKCX7SYEXSU", "AI3LZF99ECT58", "AHE1TAVA2UK5F", "A3559VD53E2JYY", "A1LLBT92I9VVCQ", "A20XPARTTWNNK2", "A38IPIPA3T3G4", "A2S591ZMEWMA5C", "A2WQT33K6LD9Z5", "A39VVWV1GHLMFD", "AYIFHDQSXQJ6B", "A2DEYXKCEOJQJU", "A13YTGRLTS80MU", "A5U517WO9A7MD"] # A38IPIPA3T3G4 is white
	rejected_workers = 0
	approved_column = []
	rejected_column = []
	rejections = [["Reason for rejection", "Worker", "Task duration"]]

	normalized_worktimes, minimum_worktime = get_minimum_worktime()
	for index, worker_data in input_data.iterrows():

		worker_id = worker_data["WorkerId"]
		worktime = worker_data["WorkTimeInSeconds"]
		
		# Too short time spent
		if worktime/len(worker_data["Input.biography"].split()) < minimum_worktime:
			reason = f"You spend an unreasonably short amount of time on the task ({worktime} seconds) compared to other workers. As mentioned in the instructions, this is grounds for rejection."
			rejections.append([reason, worker_id, worktime])
			rejected_workers += 1
			rejected_column.append(reason)
			approved_column.append("")

		else:
			# Reject based on demographics
			verification, reason = verify_demographics(worker_data)
			if worker_data["WorkerId"] in preapproved_workers: verification = True
			if not verification:
				rejections.append([reason, worker_id, worktime])
				rejected_workers += 1
				rejected_column.append(reason)
				approved_column.append("")
				
			# Reject based on task incompletion
			else:
				verification, reason = verify_task_completion(worker_data)
				if not verification:
					rejections.append([reason, worker_id, worktime])
					rejected_workers += 1
					rejected_column.append(reason)
					approved_column.append("")
				else:
					# Approve the rest
					reason = ""
					rejected_column.append("")
					approved_column.append("x")
		if worker_id in ["A5U517WO9A7MD"]:
			print(worker_id, reason)

	input_data["Approve"] = approved_column
	input_data["Reject"] = rejected_column
	input_data.to_csv(f"data/mturk_results/reviewed/{sys.argv[1]}_reviewed.csv", index=False)

	#print(tabulate(rejections))
	print("Number of rejected tasks:\t", rejected_workers)

	print("\nBE CAREFUL: the MTurk setup now allows for several results from the same worker and they do not have to fill in demo more than once.")	
if __name__ == "__main__":
	main()
