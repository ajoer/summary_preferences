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

	demographics:
	1) check for each worker whether they have filled in the demographic information at least once.
	2) check for each worker whether there are any discrepancies in the demographic information.
	3) check whether the age inputs correspond

	task:
	4) check for each worker for each task whether the information is complete
	5) for each worker count how many tasks they have completed.  

"""

class ReviewAssignments():

	def __init__(self, data):
		self.data = data
		self.demographics_dict = {}
		self.justification = """ As mentioned in the instructions, this is grounds for rejection: 'You can complete as many summary rating tasks as you want. You will be paid for the number of tasks you complete. If you leave a question unanswered, the task is incomplete,	and you will not be paid for that task. Afterwards, we will ask you four questions about who you are. If there are discrepancies in your answers to the demographic questions, we will exclude you from the experiment, and you will not be paid.'
		"""

		self.total_assignments = self.data.shape[0]
		self.rejected_assignments = 0
		self.approved_column = []
		self.rejected_column = []
		self.rejections = [["Reason for rejection", "Worker", "Task", "Task duration"]]
		self._get_minimum_worktime()
		self._make_demographics_dict()

	def _demographics_complete(self, worker_data):
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
		
	def _get_worker_demographics(self, worker_data): # race_division = binary or all
		# Make worker demographics dictionary
		demographics = {
			"age": None,
			"agegroup": None,
			"gender": None,
			"race": None
		}
		
		# Age
		demographics["age"] = worker_data['Answer.typed_age']

		if worker_data[f'Answer.age.older']:
			demographics["agegroup"] = "older than 30"
		elif worker_data[f'Answer.age.younger']:
			demographics["agegroup"] = "younger than 30"
		elif worker_data[f'Answer.age.30']:
			demographics["agegroup"] = "30"

		# Gender
		for gender in ['female', 'male', 'other']:
			if worker_data[f'Answer.gender.{gender}']:
				demographics["gender"] = gender

		# Race
		for race in ['white', 'black', 'asian', 'american_indian','hispanic', 'other']:
			if worker_data[f'Answer.race.{race}']:
				demographics["race"] = race
		return demographics

	def _make_demographics_dict(self):
		for index, worker_data in self.data.iterrows():

			demographics = self._get_worker_demographics(worker_data)
			if None in demographics.values(): continue
			self.demographics_dict[worker_data["WorkerId"]] = demographics	

	def _verify_demographics(self, worker_id): #data):
		# Verify that the demographics are complete and have no discrepancies. 
		# Return True (verified) or False (rejected).
		# Reject worker if incomplete demographics
		# complete, reason = self._demographics_complete(worker_data)
		# if not complete:
			
		if worker_id not in self.demographics_dict.keys(): 
			print("Worker not in demographics dict:\t", worker_id)
			return False, f"Incomplete demographics."

		verified = True
		reason = ""

		# Reject worker if discrepancies in age:
		age = self.demographics_dict[worker_id]["age"]
		if age == 3030: age = 30
		agegroup = self.demographics_dict[worker_id]["agegroup"]

		if ( age > 30 and agegroup != "older than 30" or
			 age < 30 and agegroup != "younger than 30" or
			 age == 30 and agegroup != "30" ):
			reason = f"Discrepancies in age. You put that you are {agegroup}, but typed that you are {age}."
			verified = False

		if worker_id == "AYIFHDQSXQJ6B":
			print(self.demographics_dict[worker_id]["age"], self.demographics_dict[worker_id]["agegroup"])

		return verified, reason

	def _verify_task_completion(self, worker_data):
		# Verify whether each task element has an answer, i.e. one True value per element options.
		for task_element in ["informative", "fluent", "useful"]:
			for letter in ["A", "B"]:
				if not True in [worker_data[f'Answer.{task_element}_{letter}.{num}'] for num in range(4)]:
					reason = f"You did not rate the element '{task_element}' for summary {letter}."
					return False, reason

		if not True in [worker_data[f'Answer.summary_preference.{letter}'] for letter in ["a", "b", "non"]]:
			reason = "Missing summary preference entry."
			return False, reason

		return True, ""

	def _get_minimum_worktime(self):
		# Get average normalized worktime, and standard deviation. 
		# Used to exclude workers who spend too little time on task.
		self.normalized_worktimes = {}
		
		for index, worker_data in self.data.iterrows():
			time = worker_data["WorkTimeInSeconds"]
			words = len(worker_data["Input.biography"].split()) #+len(worker_data["Input.summary_A"].split())+len(worker_data["Input.summary_B"].split())
			normalized_worktime = time/words
			self.normalized_worktimes[f"{worker_data['WorkerId']}_{index}"] = normalized_worktime

		average = sum(self.normalized_worktimes.values())/len(self.normalized_worktimes)
		standard_deviation = stdev(list(self.normalized_worktimes.values()))
		self.minimum_worktime = average-(0.75*standard_deviation)

	def _do_rejection(self, reason, worker_id, task_id, worktime, assignment_status):
		if assignment_status == "Submitted":
			self.rejections.append([reason, worker_id, task_id, worktime])
			self.rejected_assignments += 1
		self.rejected_column.append(reason+self.justification)
		self.approved_column.append("")


	def main(self):
		# Review and approve/reject assignments based on time spent on assignment and complete demographics.

		for index, worker_data in self.data.iterrows():

			worker_id = worker_data["WorkerId"]
			task_id = worker_data["HITId"]
			worktime = worker_data["WorkTimeInSeconds"]

			# Too short time spent
			if self.normalized_worktimes[f"{worker_id}_{index}"] < self.minimum_worktime:
				reason = f"You spent an unreasonably short amount of time on the task ({worktime} seconds) compared to other workers and the length of the texts."
				self._do_rejection(reason, worker_id, task_id, worktime, worker_data["AssignmentStatus"])

			else:
				# Reject based on demographics
				verification, reason = self._verify_demographics(worker_id)
				if not verification:
					self._do_rejection(reason, worker_id, task_id, worktime, worker_data["AssignmentStatus"])
					
				# Reject based on task incompletion
				else:
					verification, reason = self._verify_task_completion(worker_data)
					if not verification:
						self._do_rejection(reason, worker_id, task_id, worktime, worker_data["AssignmentStatus"])
					else:
						# Approve the rest
						reason = ""
						self.data.loc[index,"AssignmentStatus"] = "Approved"
						self.rejected_column.append("")
						self.approved_column.append("x")

		self.data["Approve"] = self.approved_column
		self.data["Reject"] = self.rejected_column
		self.data.to_csv(f"data/mturk/output/reviewed/{sys.argv[1]}.csv", index=False)

		print()
		print(tabulate(self.rejections))
		print(f"Number of rejected assignments:\t{self.rejected_assignments} ({self.rejected_assignments/self.total_assignments})")
		print()

if __name__ == "__main__":
	data = pd.read_csv(f"data/mturk/output/raw/{sys.argv[1]}.csv", sep=",")
	ReviewAssignments(data).main()
