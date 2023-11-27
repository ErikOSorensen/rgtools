import os.path

import pandas as pd
from xmlschema import XMLSchema

class XMLProcessor:
	def __init__(self, file_path):
		self.file_path = file_path
		self.trial_schema = None
		self.trial_object = None

		self.interventions_df = None
		self.outcomes_df = None
		self.arms_df = None
		self.armgroups_df = None
		self.hypotheses_df = None
		self.heterogeneity_df = pd.DataFrame(columns=["subgroups", "hypothesis_id",	"effect_type"])
		self.judgmentcalls_df = None


	def get_trial_object(self):
		self.trial_object = self.trial_schema.to_dict(self.file_path)

	def get_trial_schema(self,):
		self.trial_schema = XMLSchema('rg-schema.xsd')


	def parse_populations(self):
		self.populations_df = pd.DataFrame(self.trial_object['populations']['population'])


	def parse_interventions(self):
		self.interventions_df = pd.DataFrame(self.trial_object['interventions']['intervention'])

	def parse_outcomes(self):
		self.outcomes_df = pd.DataFrame(self.trial_object['main_outcomes']['main_outcome'])

	def parse_arms(self):
		self.arms_df = pd.DataFrame(self.trial_object['arms']['arm'])
		self.arms_df['population'] = self.arms_df.population.apply(lambda x: x if not isinstance(x,list) else  "; ".join(x))
		self.arms_df['intervention'] = self.arms_df.intervention.apply(lambda x: x if not isinstance(x,list) else "; ".join(x))

	def parse_armgroups(self):
		if 'armgroups' in self.trial_object.keys():
			self.armgroups_df = pd.DataFrame(self.trial_object['armgroups']['armgroup'])
			self.armgroups_df['armlabel'] = self.armgroups_df.armlabel.apply(lambda x: "; ".join(x))

	def parse_heterogeneity(self):
		heterogeneity_df_list = []
		hypotheses = self.trial_object['hypotheses']['hypothesis']
		for i, hypothesis in enumerate(hypotheses):
			hypothesis = hypotheses[i]
			hypothesis_label = hypothesis['label']
			if 'test_heterogeneity' in hypothesis.keys():
				heterogeneity_df = pd.DataFrame(hypothesis['test_heterogeneity']['subgrouptest'])
				heterogeneity_df['hypothesis_id'] = hypothesis_label
				heterogeneity_df_list.append(heterogeneity_df)
		if len(heterogeneity_df_list)>0:
			heterogeneity_df = pd.concat(heterogeneity_df_list)
			heterogeneity_df = heterogeneity_df.melt(id_vars=['subgroups','hypothesis_id'],var_name='effect_type')
			self.heterogeneity_df = heterogeneity_df[heterogeneity_df.value].drop('value',axis=1)
		hypotheses_df = self.hypotheses_df
		main_df = (hypotheses_df[['label']]).copy().rename({'label': 'hypothesis_id'}, axis=1)
		main_df['subgroups'] = 'main'
		main_df['effect_type'] = ''
		self.heterogeneity_df = pd.concat([main_df, self.heterogeneity_df])

	def parse_hypotheses(self):
		self.hypotheses_df = pd.DataFrame(self.trial_object['hypotheses']['hypothesis'])
		self.hypotheses_df['h_type'] = ""
		self.hypotheses_df['expr_string'] = ""
		self.hypotheses_df['expr_desc'] = ""
		for h_num, row in self.hypotheses_df.iterrows():
			h_processor = HypothesesProcessor(self.trial_object['hypotheses'], h_num)
			self.hypotheses_df.loc[h_num,['h_type', 'expr_string', 'expr_desc', 'outcomes', 'arms']] = h_processor.extract_hypothesis()
	def parse_judgementcalls(self):
		if 'judgmentcalls' in self.trial_object.keys():
			self.judgmentcalls_df = pd.DataFrame(self.trial_object['judgmentcalls']['judgment'])

	def write_csv(self):
		output_filepath = self.file_path.replace(".xml","")+"_csv"
		# output_filepath = os.path.join(output_filepath,"G0_csv")
		os.makedirs(output_filepath,exist_ok=True)
		if self.interventions_df is not None:
			csv_output = f'{output_filepath}/interventions.csv'
			self.interventions_df.to_csv(csv_output)
		if self.outcomes_df is not None:
			csv_output = f'{output_filepath}/outcomes_df.csv'
			self.outcomes_df.to_csv(csv_output)
		if self.arms_df is not None:
			csv_output = f'{output_filepath}/arms.csv'
			self.arms_df.to_csv(csv_output)
		if self.armgroups_df is not None:
			csv_output = f'{output_filepath}/armgroups.csv'
			self.armgroups_df.to_csv(csv_output)
		if self.hypotheses_df is not None:
			csv_output = f'{output_filepath}/hypotheses_df.csv'
			self.hypotheses_df.to_csv(csv_output)
		if self.heterogeneity_df.shape[0]>0:
			csv_output = f'{output_filepath}/heterogeneity_df.csv'
			self.heterogeneity_df.to_csv(csv_output)
		if self.judgmentcalls_df is not None:
			csv_output = f'{output_filepath}/judgementcalls_df.csv'
			self.judgmentcalls_df.to_csv(csv_output)


	def parse_xml(self):
		self.parse_populations()
		self.parse_interventions()
		self.parse_outcomes()
		self.parse_arms()
		self.parse_armgroups()
		self.parse_hypotheses()
		self.parse_heterogeneity()
		self.parse_judgementcalls()

	def run(self):
		self.get_trial_schema()
		self.get_trial_object()
		self.parse_xml()
		self.write_csv()


class HypothesesProcessor:
	def __init__(self, hypotheses_object, h_num):
		self.h_num = h_num
		self.hypotheses_object = hypotheses_object
		self.lhs = self.hypotheses_object['hypothesis'][self.h_num]['LHS']
		self.rhs = self.hypotheses_object['hypothesis'][self.h_num]['RHS']
		self.lhoutcome = self.lhs['Houtcome']
		self.rhoutcome = self.rhs['Houtcome']

		self.ltype = self.rtype = self.lexp = self.rexp = self.rhval = self.expr_desc = None

	def extract_single_exp(self, houtcome):
		first_outcome = houtcome[0]['OutcomeDifference']['first']['outcome']
		first_arm = houtcome[0]['OutcomeDifference']['first']['arm']
		ref_outcome = houtcome[0]['OutcomeDifference']['reference']['outcome']
		ref_arm = houtcome[0]['OutcomeDifference']['reference']['arm']
		expectation_string = f'E[{first_outcome} | {first_arm}] - E[{ref_outcome} | {ref_arm}]'
		return expectation_string, list(set([first_outcome,ref_outcome])), list(set([first_arm,ref_arm]))

	def extract_num_val(self, houtcome):
		return int(houtcome[0]['HypothesizedValue']['number'])

	def extract_feature(self, houtcome):
		feature = houtcome[0]['Estimate']['feature']
		feature = feature.rstrip().rstrip('.')
		arms = "" if not 'arm' in houtcome[0]['Estimate'].keys() else ", ".join(houtcome[0]['Estimate']['arm'])
		outcome = "" if not 'main_outcome' in houtcome[0]['Estimate'].keys() else ", ".join(houtcome[0]['Estimate']['main_outcome'])
		expr_desc = f'Coefficient: {feature}. Arm(s): {arms}. Outcome: {outcome}'
		return expr_desc, outcome, arms

	def get_hypothesis_type(self, houtcome):
		is_single = len(houtcome) == 1
		is_out_diff = "OutcomeDifference" in houtcome[0].keys()
		is_estimate = "Estimate" in houtcome[0].keys()
		is_hval = "HypothesizedValue" in houtcome[0].keys()
		return is_single, is_out_diff, is_estimate, is_hval

	def extract_hypothesis(self):
		l_is_single, l_is_out_diff, l_is_estimate, l_is_hval = self.get_hypothesis_type(self.lhoutcome)
		r_is_single, r_is_out_diff, r_is_estimate, r_is_hval = self.get_hypothesis_type(self.rhoutcome)

		# E[outcome | T1] - E[outcome | T0] = 0
		if l_is_single and r_is_single and l_is_out_diff and r_is_hval:
			lexp, outcome_list, arm_list = self.extract_single_exp(self.lhoutcome)
			rhval = self.extract_num_val(self.rhoutcome)
			return 'single_exp_diff', f'{lexp} = {rhval}', "", ", ".join(outcome_list), ", ".join(arm_list)

		# E[outcome | T1] - E[outcome | T0] = E[outcome | T3] - E[outcome | T2]
		elif l_is_single and r_is_single and l_is_out_diff and r_is_out_diff:
			lexp, outcome_list1, arm_list1 = self.extract_single_exp(self.lhoutcome)
			rexp, outcome_list2, arm_list2 = self.extract_single_exp(self.rhoutcome)
			outcome_list = list(set([outcome_list1, outcome_list2]))
			arm_list = list(set([arm_list1, arm_list2]))
			return 'double_exp_diff', f'{lexp} = {rexp}', "", ", ".join(outcome_list), ", ".join(arm_list)

		# Beta = 0
		elif l_is_single and r_is_single and l_is_estimate and r_is_hval:
			expr_desc, outcome, arms = self.extract_feature(self.lhoutcome)
			rhval = self.extract_num_val(self.rhoutcome)
			return 'feature', f'Coefficient = {rhval}', expr_desc, outcome, arms

		# E[outcome | T1] - E[outcome | T0] = E[outcome | T2] - E[outcome | T0] = 0
		elif not l_is_single and not r_is_single and l_is_out_diff and r_is_hval:
			lexp_list = []
			outcome_list = []
			arm_list = []
			for index, houtcome in enumerate(self.lhoutcome):
				lexp, outcomes, arms = self.extract_single_exp([houtcome])
				lexp_list.append(lexp)
				outcome_list = outcome_list + outcomes
				arm_list = arm_list + arms
			lexp = " = ".join(lexp_list)
			outcome_list = list(set(outcome_list))
			arm_list = list(set(arm_list))
			rhval = self.extract_num_val(self.rhoutcome)
			return 'joint-test', f'{lexp} = {rhval}', "", ", ".join(outcome_list), ", ".join(arm_list)




# 633: joint-test, 641: feature & heterogeneity, 610: interaction
# xml_processing = XMLProcessor('633_G0_GP.xml')
# xml_processing.run()
# heterogeneity_df = xml_processing.heterogeneity_df
#
# zz = heterogeneity_df.groupby('subgroups', as_index=False)['hypothesis_id'].apply(lambda x: ', '.join(x))

# pd.DataFrame(xml_processing.trial_object['hypotheses']['hypothesis'][0]['test_heterogeneity']['subgrouptest'])
# h_object = HypothesesProcessor( xml_processing.trial_object['hypotheses'], 0)
# a = xml_processing.hypotheses_df

# xml_processing.run()
# xml_processing.populations_df
# xml_processing.arms_df.to_latex()
#
# xml_processing.trial_object['populations']['population']