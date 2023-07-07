import csv
import re
import sys
from string import Template
from xml.sax.saxutils import quoteattr


def read_trials(fname='data/trials.csv'):
    with open(fname, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        trials = {}
        for row in reader:
            trials[row['RCT_ID']] = row
    return trials

def format_trial_id(x):
    RCT_ID = "AEARCTR-{:07d}".format(x)
    return RCT_ID

def get_trial_from_number(trials, x):
    rct_id = format_trial_id(x)
    return trials[rct_id]

def get_trial_number_from_trial(trial):
    aea_id = trial['RCT_ID']
    match = re.search(r"\d+$", aea_id)
    if match:
        numval = int(match.group())
    else:
        numval = None
    return numval



def split_pi_field(s):
    match = re.search(r'(\()?([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})(?(1)\))', s)
    if match:
        non_email_part_before = s[:match.start()].strip()
        email_address = match.group(2)
        non_email_part_after = s[match.end():].strip()
        return (non_email_part_before, email_address, non_email_part_after)
    else:
        return (s, None, None)

def get_main_pi(trial):
    name, email, affiliation = split_pi_field(trial['Primary Investigator'])
    main_pi = {'name': name.strip()}
    if email:
        main_pi['email'] = email.strip()
    if affiliation:
        main_pi['affiliation'] = affiliation.strip()
    return main_pi

def get_other_pis(trial):
    pis = trial['Other Primary Investigators'].split(";")
    if len(pis)==1 and pis[0]=='':
        return []
    t1 = [split_pi_field(s) for s in pis]
    t2 = []
    for t in t1:
        pi = {}
        name, email, affiliation = t
        if name:
            pi['name'] = name
        if email:
            pi['email'] = email
        if affiliation:
            pi['affiliation'] = affiliation
        t2.append(pi)
    return t2

def get_keywords(trial):
    keywordstrings = [x.strip('"').strip().strip('"') for x in trial['Keywords'][1:-1].split(",")]
    return keywordstrings


trial_template="""
<trial xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:noNamespaceSchemaLocation="rg-schema.xsd">
<title>$title</title>
<owners>$owners</owners>
<abstract>$abstract</abstract>
<topics>$topics</topics>
<registration_number>$registration_number</registration_number>
<registration_date>$registration_date</registration_date>
<intervention_start_date>$intervention_start_date</intervention_start_date>
<intervention_stop_date>$intervention_stop_date</intervention_stop_date>
<pre_analysis_plan>$pre_analysis_plan</pre_analysis_plan>
<data_publication>$data_publication</data_publication>
<reports_and_materials>$reports_and_materials</reports_and_materials>
<relevant_papers>$relevant_papers</relevant_papers>

<populations>  </populations>

<main_outcomes> </main_outcomes>

<interventions> </interventions>

<arms> </arms>

<hypotheses> </hypotheses>

</trial>



"""

def topics_string_from_trial(trial):
    keywords = get_keywords(trial)
    output = ""
    for keyword in keywords:
        output += f"\n  <keyword>{quoteattr(keyword)}</keyword>"
    if output!="":
        output += "\n"
    return output

def person_from_dct(dct, role):
    dct['role'] = role
    if not dct.get('affiliation'):
        dct['affiliation'] = ""
    string = f"""<researcher><name>{quoteattr(dct['name'])}</name><role>{quoteattr(dct['role'])}</role><affiliation>{quoteattr(dct['affiliation'])}</affiliation><email>{quoteattr(dct['email'])}</email></researcher>"""
    return string



def owners_string_from_trial(trial):
    mainpi = [person_from_dct( get_main_pi(trial), "Main PI")]
    otherpis = [ person_from_dct( x, "Other PI") for x in get_other_pis(trial)]
    allpis = mainpi + otherpis
    return "\n  " + "\n  ".join(allpis) + "\n"



def templatedct_from_trialdct(trial):
    d = {'title': quoteattr(trial['Title']),
     'abstract': quoteattr(trial['Abstract']),
     'registration_number': get_trial_number_from_trial(trial),
     'registration_date': trial['First registered on'],
     'intervention_start_date': trial['Intervention start date'],
     'intervention_stop_date': trial['Intervention end date'],
     'topics': topics_string_from_trial(trial),
     'pre_analysis_plan': "Yes" if trial['Analysis Plan Documents'] else "No",
     'data_publication': "Yes" if trial['Public data'] else "No",
     'owners': owners_string_from_trial(trial),
     }
    return d


def main():
    trials = read_trials()
    assert len(sys.argv)==2, "Should have exactly one argument"
    trialno = int(sys.argv[1])
    trial = get_trial_from_number(trials, trialno)
    tdct = templatedct_from_trialdct(trial)
    t = Template(trial_template)
    # print(str(trial))
    print(t.safe_substitute(tdct))


if __name__ == "__main__":
    main()
