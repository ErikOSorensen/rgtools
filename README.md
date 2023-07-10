# rgtools

Repository with the tooling for capturing data from social science registry trials.

To begin with, there are two main tools: 

1. `rg-schema.xsd` which defines an xml schema to represent data captured from registrations and pre-analysis plans.
2. `AEAtrials.py` which has the beginnings of a small library to read and process the Social Science Registry data. As of now, it can read take a trial number as argument and print out an xml-template with some of the auto filled-in information from the registry.


# Documentation of tools

Preconditions for use:

- The set of trials (`trials.csv` downloaded from Harvard Dataverse) should be in the `data` directory.
- One should install [VS code](https://code.visualstudio.com/) and the XML extension from RedHat or some similar tools to work with xml files.

## Generation of a template for a registration

Running `python3 AEAtrials.py NNNN` will scan through the `data/trials.csv` file and extract many of the
features of the trial numbered NNNN and output a template to the stdout. From there it can be redirected
to an `.xml` file,

> python3 AEAtrials.py 487 > AEARCTR-0000487.xml 

This will extract details from trial 487 and pipe the template-xml into the named file on the right hand
side. The features of the trial that are easy to mechanically extract from the `trials.csv` file will
be then not have to be filled out.

## The elements

The metadata schema aims to extend the schema of [A Metadata Schema for Data from Experiments in the Social Sciences](http://documents.worldbank.org/curated/en/099945502062327217/IDU081c960a8049b504197099ff0d12be0b95375). For the most part, Appendix A of that
document is informative with respect to documentation and how to use our schema. 

The main elements that need filling in after the pre-populated set is done is the five empty elements
that are the provided at the bottom of the output of the `AEAtrials.py` program:

```xml
<populations>  </populations>
<main_outcomes> </main_outcomes>
<interventions> </interventions>
<arms> </arms>
<hypotheses> </hypotheses>
```

Note that they are all plural. The intention is to fill in these with lists of the singular version of each
of these names, and there are special data types defined for each of these.

### population

There are 5 elements to a population all of them mandatory. 

| Element | type | Mandatory? |
|---------|------|------------|
| label   | string | yes    |
| country | 3-letter ISO 3166 code | yes |
| coverage | string | yes |
| unit_of_randomization | string | yes |
| target_sample_size | string | yes |

This is slightly different from the Cavenagh et al, in that they seem to only
expect a single population per trial, while we allow for a list of populations per trial.


#### label

Each of the populations must get a unique label such that it can be referenced from other elements.
It needs to be unique *within* a trial, not necessarily across trials.

#### country

Which country is this population in? We want to use the ISO 3166 3-letter code (authoritative
list available at the [ISO website](https://www.iso.org/obp/ui).
The schema will test that there are 3 letters provided, but not for validity against the standard.

#### coverage

A description that says something about what part of the national population is targeted. Example: "All adults".

#### unit_of_randomization

What is the sub-unit of the population that randomization is implemented at? Often this will be "individual", but sometimes
there will be clustering an the unit might be "school", "village", "neighborhood" or something similar.

#### target_sample_size

How many are intended to be sampled from this population? A string, since for
clustered studies there will often be targets at different levels. There might
also be stratification goals such that "1000 females and 1000 males" is a relevant
response. 

#### Example of a population

This is taken from study 1009:
```xml
<population>
    <country>TZA</country>
    <label>TZA</label>
    <coverage>Students in government primary schools. The sample of 
      180 schools was taken from a previous RCT.</coverage>
    <unit_of_randomization>schools</unit_of_randomization>
    <target_sample_size>80 schools; 7,200 students (40 per school, 10 students
      from Grades 1, 2, 3, and 4); 1,800 teachers (8-12 per school); 2,700
       households (15 per school)</target_sample_size>
</population>
```





















