# Summary Preferences 

This repository holds the code and data for the Summary Preferences project (2020).
In the project, we evaluate the performance of two different summarization models in a user study, where the participants also provide their demographic information (gender, race and age). 
The purpose is to study preference differences that are demographically correlated and to explore the reasons for these preference differences. Demographics correlated reference differences is an understudied bias variant that can have wide-reaching consequences for system performance and user satisfaction.  

We conduct the user studies on Mechanical Turk and use texts (biographies) extracted from Wikipedia using the [Wikidata API](https://query.wikidata.org/).
 
The two systems in this project are [TextRank](https://github.com/summanlp/textrank) and [MatchSum](https://github.com/maszhongming/MatchSum). See the githubs for the specific systems for more information on those.

## Repository structure

The repository contains three top directories, **data**, **code** and **analyses**. 
In the *data* directory, all data used in this project is contained, all code used in the project is in the **code** directory, and all analysis outputs are to be found in the **analyses** directory.

### **Data**

The Data directory contains 1) data related to the creation of summaries as well as the summaries themselves and 2) data related to the Mechanical Turk study (as well as the output data from the studies). 

* */summaries* contains two directories: */input* and */output*.
* */mturk* contains two directories: */input* and */output* as well as two files containing the setup for the MTurk experiments (summary_quality_metadata and summary_quality_template).

the input data used to generate summaries using the two systems as well as the input data for the Mechanical Turk user studies. The directory also contains the output summaries from the two systems as well as the output data from the Mechanical Turk studies. 


and the output summaries.
*/input* contains 1) the raw Wikipedia data, 2) the Wikipedia formatted for input into MatchSum, 
3) the summaries from both systems and 4) the input and output of the Mechanical 


### **Code**


### **Analyses**