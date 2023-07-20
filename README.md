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

This is slightly different from the Cavanagh et al, in that they seem to only
expect a single population per trial (one population consisting of potentially many countries),
while we allow for a list of populations per trial.


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

### main outcomes

There are 4 elements to an outcome:

| Element | type | Mandatory? |
|---------|------|------------|
| label   | string | yes    |
| description | string | yes |
| unit_original | string | yes |
| unit_analytical | string | yes |


#### label


Each of the outcomes must get a unique label such that it can be referenced from
other elements. It needs to be unique *within* a trial, not necessarily across
trials.

#### description

A free-text description of how what the outcome is intended to represent and maybe
how it is collected.

#### unit_original

Is the outcome in some numeric currency? Is it a binary outcome? Categories? 

#### unit_analytical

Possible transformations of the original collection format provided in the
registration or the pre-analysis plan. Examples might be "Z-normalized", or
"Coded binary as above the median" or "coded numerically 1-5". If no information
is provided on such transformation, write "none provided".

#### Example of a main outcome

This is taken from study 1009:

```xml
<main_outcome>
    <label>testscore</label>
    <description>Students will be tested at the end of the first year and at the end of the second year. 
    Grade 1 students will be tested at the beginning of the first and second years, to provide 
    baseline scores to evaluate their initial learning levels. For some analysis we will 
    also aggregate test scores across subjects by summing them and the re-normalizing (dividing by the 
    standard deviation of the test scores in the control group).
    </description>
    <unit_original>Grades</unit-original>
    <unit_analytical>Z-standardized</unit-analytical>
</main_outcome>
```


### Interventions

Often papers will refer to "treatments", which in the schema of Cavanagh et al
(2023) often combinations of the "intervention" and possibly also "arms". We
adopt Cavanagh et als usage, and an interventions is a basic unit that might
be combined with others in practice. 

An example would be a trial that has both an "information" intervention and an
"incentives" intervention and full factorial designs. Often registrations report
this as 4 different treatments: "Control", "Information", "Incentives", and
"Information and Incentives". In our schema there are just two **interventions**, 
and these will be combined in the related concepts of **arms** (defined below). 

There are just two elements to defining an intervention:

| Element | type | Mandatory? |
|---------|------|------------|
| label   | string | yes    |
| description | string | yes |

#### label


Each of the interventions must get a unique label such that it can be referenced
from other elements. It needs to be unique *within* a trial, not necessarily
across trials.

#### description

A free-text description of what the intervention involves.

#### Example of an intervention

This is taken from study 1009:

```xml
<intervention>
    <label>levels</label>
    <description> "levels" incentive that provides teachers
      and head teachers with bonus payments conditional on the skills that each
      student is able to demonstrate in a basic literacy and numeracy
      tests
    </description>
</intervention>
```

### Arms

An **arm** combines the concept of a **population** with a possible list of
**interventions**.

There are three elements to an arm:

| Element | type | Mandatory? | May repeat? |
|---------|------|------------|------------|
| label   | string | yes    | no |
| population | string | yes | yes |
| intervention | string | no | yes

#### label

Each of the arms must get a unique label such that it can be referenced from
other elements. It needs to be unique *within* a trial, not necessarily across
trials.

#### population

An arm must contain one or more **populations**. These are referenced by their population labels.

#### intervention

An arm has zero, one, or more **interventions**. These are referenced by their intervention labels.

#### Example of an arm

This is taken from study 1009:

```xml
<arm>
  <label>levels</label>
  <population>TZA</population>
  <intervention>levels</intervention>
</arm>
```

### Hypothesis

This is an element that has not got a counterpart in Cavanagh et al (2023) but
is essential to our purpose. An hypothesis is, in general, a claim about some
features of the outcomes vary by populations and interventions (or how the
outcomes vary by arms). These hypotheses can be simple or complicated, and we
expect substantial variety. Our intent is to have a schema that can account
for different types of hypotheses. 

In our setting, an **hypothesis** always refer to the null hypothesis that would 
be subject to statistical testing.

All this creates a need for more complex types. An hypothesis is defined by the
following elements:

| Element | type | Mandatory? |
|---------|------|------------|
| label  | string | yes |
| description | string | yes |
| LHS | Houtcome | yes |
| RHS | Houtcome | yes |
| detailed | binary | yes |
| det_exp | string | yes |
| test_heterogeneity | subgrouptest | no |
|test_feature | string | yes |
|test_type | string | yes |
|control_variables | string | yes |
|mht_family | string | no |
|howto | string | no |
|comment | string |no |

#### label 

Each of the hypotheses must get a unique label such that it can be referenced from
other elements. It needs to be unique *within* a trial, not necessarily across
trials.

#### description

A free-text description of what the hypothesis entails. Often this can be lifted in
a sentence from the paper. Note that the hypothesis as stated in the paper often
will be a statement of the *alternative hypothesis* instead of the null hypothesis
that we aim to encode. That is fine and you can enter the alternative hypothesis here.

#### LHS and RHS

Each of these will contain one or more `Houtcome`s. These can be of different 
types since hypotheses sometimes vary. But the main structure is that a
hypothesis should be of the form 
$$LHS = RHS$$.

Written in terms of math, the simplest and most common hypothesis we expect to
see is of the form
$$E[Y|A_1, X] - E[Y|A_2, X] = 0,$$
saying that the expected outcome ($Y$) should be the same in arm $A_1$ and $A_2$
(allowing for the control variables in $X$). This is an example where both
the left hand side (LHS) and the right hand side (RHS) is of length 1, but the
*types* of the LHS and the RHS are different.

This is implemented by the `Houtcome` (the shared type of LHS and RHS) being
able to contain one of three different types:

1. `OutcomeDifference` intended to capture expressions such as $E[Y|A_1, X] - E[Y|A_2, X]$ ).
2. `HypothesizedValue` intended to capture simple expressions, such as constant numbers.
3. `Estimate` intended to capture general features to be estimated.

##### OutcomeDifference

An `OutcomeDifference` contains the idea of arm comparisons out outcomes. It is defined
with three elements:

| Element | type | Mandatory? |
|---------|------|------------|
| first   | OutcomeInArmType | Yes |
| reference | OutcomeInArmType | Yes |
| comment | string | No |

This reference a structure (in either the LHS or the RHS) of
$$\mathrm{first} - \mathrm{reference}.$$

The comment field can be given free-text to indicate if this
was unclear or difficult to encode - possibly also an interpretation
by the coder.

The main definition is that of an `OutcomeInArm` which itself is defined
by its elements:


| Element | type | Mandatory? |
|---------|------|------------|
| outcome | string | Yes |
| arm     | string | Yes |
| time    | int    | No  |
| comment | string | No  |

In such an `OutcomeInArm`, the two mandatory elements reference the labels given to
outcomes and arms. The optional argument `time` allows one to enter a number for a logical
time at which the outcome is recorded, such that one doesn't need to enter the same type
of outcome at different points in time as different outcomes.

Again, the comment field can be given free-text to indicate if this
was unclear or difficult to encode - possibly also an interpretation
by the coder.

##### Hypothesized value

This is a very simple type intended to encode simple 
hypotheses:

| Element | type | Mandatory? |
|---------|------|------------|
| number  | decimal | Yes |
| comment | string | No |

Often the number will simply be zero.

##### Estimate

This is supposed to be a catch-all type for outcomes that
cannot easily be put in the most common forms. It might
be a regression coefficient, or it might be a structural
parameter from a complicated model. The elements are

| Element | type | Mandatory? |
|---------|------|------------|
| feature | string | Yes |
| comment | string | No  |

The `feature` should include a full description of what the estimate entails (including
free form reference to arms that provide data).

#### detail  
Binary variable, takes the value of one if the hypothesis is deemed to be presented with sufficient detail to be tested one specific way. Zero if one or more elements of the hypothesis lack sufficient detail such that it can be implemented in two or more ways. 

##### det_exp
String variable, conditional on the hypothesis not being detailed enough (`detail = 0`). Paste here any description in the registration/PAP that it is deemed ambiguos enough such two or more implementations can be consistent with the hypothesis.  

#### test_heterogeneity

Sometimes it is specified that hypotheses should also be broken down and estimated by a number of
different subgroups. Instead of coding separate hypotheses for each subgroup, it is possible
to add an (optional) element with free text `xml <subgroups>` elements,  such as in this
example, which should test income groups separately and for difference, and education groups
for difference between them:

```xml
<test_heterogeneity>
  <subgrouptest>
      <subgroups>Below and above median household income</subgroups>
      <separate_effects>true</separate_effects>
      <different_effects>true</different_effects>
  </subgrouptest>
      <subgrouptest>
      <subgroups>At or above highschool education</subgroups>
      <separate_effects>false</separate_effects>
      <different_effects>true</different_effects>
  </subgrouptest>
</test_heterogeneity>
```

#### test_feature

What feature of the outcomes is involved? Most of the time this will be *mean* (which
would include the conditional mean), but sometimes *variance* or *distribution* will
also be relevant.

#### test_type

A short description of relevance to the test. Might be "two-sided", "one-sided", or possibly
the name of a test such as "Mann-Whitney" or "Kolmogorov-Smirnov".

#### control_variables

Should the main test of the hypothesis control for background characteristics? Yes or No,
or possibly "Not specified".

#### mht_family

Sometimes the registration or a pre-analysis plan will specify that the authors
will correct for testing a number of similar hypothesis, *multiple hypothesis
testing corrections*. In this case, they should specify which hypothesis belongs
together and should be corrected together. This is known as a *family* of tests,
and we record a label that specifies this family. The family will be indicated
by using the same `mht_family` label for all the hypotheses that belong in a single
family.

#### howto

Sometimes contextual details are provided about how tests should be done. That
might be "In an OLS framework", or it might be that standard errors should be
calculated in a particular way, or possibly the name of a procedure for
correcting for multiple testing.


#### comment

This is a field for the coder to provide free-text comments if they believe that
they might be wrong because of particularly complicated or under-specified
hypotheses in the registration.

Note that it is also allowed to add any number of "comment" fields directly
to the `xml <hypotheses>` (plural) element.

#### Example of an hypothesis

```xml
<hypothesis>
  <description>levels treatment has (no) positive impact on test scores.</description>
  <label>H1</label>
  <control_variables>Yes</control_variables>
  <test_feature>Mean</test_feature>
  <test_type>two-sided</test_type>
  <howto>In an OLS framweork</howto>
  <LHS>
    <Houtcome>
      <OutcomeDifference>
        <first>
          <outcome>testscore</outcome>
          <arm>levels</arm>
        </first>
        <reference>
          <outcome>testscore</outcome>
          <arm>control</arm>
        </reference>
      </OutcomeDifference>
    </Houtcome>
  </LHS>
  <RHS>
    <Houtcome>
      <HypothesizedValue>
        <number>0</number>
      </HypothesizedValue>
    </Houtcome>
  </RHS>
</hypothesis>
```
