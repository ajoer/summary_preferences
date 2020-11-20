# Summary Preferences 

This repository holds the code and data for the Summary Preferences project (2020).
In the project, we evaluate the performance of two different summarization models in a user study, where the participants also provide their demographic information (gender, race and age). 
The purpose is to study preference differences that are demographically correlated and to explore the reasons for these preference differences. Demographics correlated reference differences is an understudied bias variant that can have wide-reaching consequences for system performance and user satisfaction.  

We conduct the user studies on Mechanical Turk and use texts (biographies) extracted from Wikipedia using the [Wikidata API](https://query.wikidata.org/).
 
The two systems in this project are [TextRank](https://github.com/summanlp/textrank) and [MatchSum](https://github.com/maszhongming/MatchSum). See the githubs for the specific systems for more information on those.

## Repository structure

The repository is structured as follows. There are three top directories, **data**, **code** and **analyses**. 

In the *data* directory, all data used in this project is contained, all code used in the project is in the **code** directory, and all analysis outputs are to be found in the **analyses** directory.

### **Data**

The Data directory contains 1) data related to the creation of summaries as well as the summaries themselves and 2) data related to the Mechanical Turk study as well as the output data from the studies. 

#### */summaries* 
*/summaries* contains two directories: */input* and */output*. 
* The input subdirectory contains the raw Wikipedia biographies as well as the formatted biographies for input into the MatchSum get_candidate.py code. This latter is necessary for the MatchSum candidate selection preprocess. 
* The output subdirectory contains the generated summaries from the two systems. 


#### */mturk* 
*/mturk* contains two directories: */input* and */output* as well as two files containing the setup for the MTurk experiments, the summary_quality_metadata and summary_quality_template.

* The input subdirectory contains the input file for the Mechanical Turk experiments.
* The output subdirectory contains the raw data files from the Mechanical Turk experiments as well as the reviewed data file. This latter is used for analyses and is also uploaded to MTurk to approve and reject assignments. The raw output data from Mechanical Turk is only used to approve and reject assignments. 

### **Code**

The Code directory contains 1) preprocessing scripts for summary generation and for creating Mechanical Turk input data and 2) scripts for approving and analysing MTurk output data.

#### */preprocessing* 
*/preprocessing* contains five files.

* get_wikipedia_data extracts the raw wikipedia biography data in data/summaries/input/wikipedia_raw/. NB: this input for this script no longer exists. It should contain the links to the Wikipedia pages of the persons about whom the biographies are written. This needs to be re-established.  

* get_textrank_summaries creates the textrank summary files in data/summaries/output

* preprocess_matchsum preprocesses the raw Wikipedia biographies for input into MatchSum.

* make_matchsum_MTurk_data reformats the MatchSum data to making the MTurk input csv.

* make_MTurk_csv creates the input csv file for the Mechanical Turk experiments in data/mturk/input.

Once the Mechanical Turk data is in (data/mturk/output/raw), the following scripts are used for assignment approval/rejection and data analysis.

* mturk_results_approve reads in the raw MTurk data and outputs the same csv file with data for approval and rejections along with reasons for rejections.

* mturk_results_analyse reads in the reviewed MTurk data file(s) and creates latex tables for the preferences and ratings of each demographic group. This can be done on the full race-division (each race its own) or on a binary split (white/non-white) as well as on the full biographical data ("both") or on a gendered biography data split (e.g. only women's biographies). 
These are saved to analyses/<race_division>/<gender>/.
This script also generates the biography_representations files, which is stored in the same location.

* bootstrapping reads in the biography_representations file  created by mturk_results_analyse and conducts significance testing on all demographic group within each race-divide split (all, white/non-white). 
The script outputs a file with the demographic groups with significant scores (after Bonferroni correction), which is stored in analyses/<race_division>/<gender>/bonferroni.txt.
* feature_extraction reads in the biography_representations file  created by mturk_results_analyse as well as the bonferroni file created by bootstrapping and runs logistic regression on the demographic groups with significant results in the bonferroni file. 
The vector representation is 2*149 (TextRank+MatchSum) where the 145 first features for each system is a one-hot vector of stopwords in the summary and the last 4 features are task specific features such as average word length and type/token ratio. 
The script outputs the top 20 most important features for the demographic group, which are stored in analyses/<race_division>/<gender>/top20_features.json.

### **Analyses**

The analyses directory contains all analyses outputs from the code and data in this repository.

The directory has two folders, one per race-divide (all races or white/non-white), and each of these has three folders: both, men and women, which reflects the split of the biography/summary data. 
For "women", only biographies about women are included in the analyses and statistical testing. 

Each of these folders contain the same files.
* the preferences_/ratings_ files contain latex tables with information about the preferences and ratings distributions of each demographic group. For instance preferences_agegroup.txt contains the preference distributions for the two summary models for the two agegroups "under30" and "over30".

* biography_representation is a JSON file, which contains the most important information about each biography, the summaries and the evaluation of the summaries. It also contains the demographic information associated with the evaluation of that biography. For instance, the evaluation of Ada Lovelace was conducted by a white female Turker over the age of 30, and she preferred the TextRank summary of this biography. This file is used for feature extraction (feature_extraction) and significance testing (bootstrapping).

* bonferroni contains the demographic groups, which have significant results from the bootstrapping testing in bootstrapping under the Bonferroni correction. The p-value for these demographic groups are also provided along witht he Bonferroni cut-off for that significance testing scheme.

* top20_features contains the extracted 20 most important features for each demographic group with significant results from the bootstrapping testing. 

## **To do**

* Re-establish the input file for get_wikipedia_data. It should contain the links to the Wikipedia pages of the persons about whom the biographies are written.