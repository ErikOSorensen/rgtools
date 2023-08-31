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

	def get_trial_object(self):
		self.trial_object = self.trial_schema.to_dict(self.file_path)

	def get_trial_schema(self,):
		self.trial_schema = XMLSchema('rg-schema.xsd')

	def parse_interventions(self):
		self.interventions_df = pd.DataFrame(self.trial_object['interventions']['intervention'])

	def parse_outcomes(self):
		self.outcomes_df = pd.DataFrame(self.trial_object['main_outcomes']['main_outcome'])

	def parse_arms(self):
		self.arms_df = pd.DataFrame(self.trial_object['arms']['arm'])
		self.arms_df['population'] = self.arms_df.population.apply(lambda x: "; ".join(x))
		self.arms_df['intervention'] = self.arms_df.intervention.apply(lambda x: "; ".join(x))

	def parse_armgroups(self):
		if 'armgroups' in self.trial_object.keys():
			self.armgroups_df = pd.DataFrame(self.trial_object['armgroups']['armgroup'])
			self.armgroups_df['armlabel'] = self.armgroups_df.armlabel.apply(lambda x: "; ".join(x))

	def parse_hypotheses(self):
		self.hypotheses_df = pd.DataFrame(self.trial_object['hypotheses']['hypothesis'])

	def write_csv(self):
		output_filepath = self.file_path.replace(".xml","")
		if self.interventions_df is not None:
			csv_output = f'{output_filepath}_interventions.csv'
			self.interventions_df.to_csv(csv_output)
		if self.outcomes_df is not None:
			csv_output = f'{output_filepath}_interventions.csv'
			self.interventions_df.to_csv(csv_output)
		if self.arms_df is not None:
			csv_output = f'{output_filepath}_arms.csv'
			self.interventions_df.to_csv(csv_output)
		if self.armgroups_df is not None:
			csv_output = f'{output_filepath}_armgroups.csv'
			self.armgroups_df.to_csv(csv_output)
		if self.hypotheses_df is not None:
			csv_output = f'{output_filepath}_hypotheses_df.csv'
			self.hypotheses_df.to_csv(csv_output)

	def parse_xml(self):
		self.parse_interventions()
		self.parse_outcomes()
		self.parse_arms()
		self.parse_armgroups()
		self.parse_hypotheses()

	def run(self):
		self.get_trial_schema()
		self.get_trial_object()
		self.parse_xml()
		self.write_csv()


xml_processing = XMLProcessor('556_G0_GP.xml')
xml_processing.run()