from xmlschema import XMLSchema

class XMLToLatex:
	def __init__(self, file_path):
		self.file_path = file_path
		self.trial_schema = None
		self.trial_object = None
		self.latex_lines = []

	def add_to_latex(self,line):
		if isinstance(line,str):
			self.latex_lines.append(line)
		elif isinstance(line,list):
			self.latex_lines += line

	def escape_text(self,text):
		text = text.replace("_","\_")
		return text

	def clean_title(self, title):
		title = title.title()
		title = title.replace("_"," ")
		return title

	def flatten_values(self,value):
		if isinstance(value,list):
			return ', '.join(value)
		else:
			return value

	def itemize_dict(self, dict_to_itemezie, bullet_symbol="-"):
		itemized_list = ["\\begin{itemize}"]
		items = [(self.clean_title(key), self.escape_text(self.flatten_values(value)) ) for key, value in dict_to_itemezie.items() if key!="label"]
		itemized_list += [f'\item[-] \\textbf{{{key}}}: {value}' for key, value in items]
		itemized_list += ["\\end{itemize}"]
		return itemized_list

	def get_trial_schema(self,):
		self.trial_schema = XMLSchema('rg-schema.xsd')

	def get_trial_object(self):
		self.trial_object = self.trial_schema.to_dict(self.file_path)

	def initialize_latex(self):
		self.add_to_latex("\documentclass{article}")
		self.add_to_latex("\\title{AEA RCT Trial Registration}")
		self.add_to_latex(f"\\author{{RCT Trial ID: {self.trial_object['registration_number']}}}")
		self.add_to_latex("\\begin{document}")
		self.add_to_latex("\\maketitle")



	def close_latex(self):
		self.add_to_latex("\end{document}")

	def add_populations(self):
		self.add_to_latex("\section{Populations}")
		for population in self.trial_object['populations']['population']:
			label = population['label']
			self.add_to_latex(f'\subsection{{{self.escape_text(label)}}}')
			self.add_to_latex(self.itemize_dict(population))

	def add_outcomes(self):
		self.add_to_latex("\section{Outcomes}")
		for outcome in self.trial_object['main_outcomes']['main_outcome']:
			label = outcome['label']
			self.add_to_latex(f'\subsection{{{self.escape_text(label)}}}')
			self.add_to_latex(self.itemize_dict(outcome))

	def add_interventions(self):
		self.add_to_latex("\section{Interventions}")
		for intervention in self.trial_object['interventions']['intervention']:
			label = intervention['label']
			self.add_to_latex(f'\subsection{{{self.escape_text(label)}}}')
			self.add_to_latex(self.itemize_dict(intervention))
	def add_arms(self):
		self.add_to_latex("\section{Arms}")
		for arm in self.trial_object['arms']['arm']:
			label = arm['label']
			self.add_to_latex(f'\subsection{{{self.escape_text(label)}}}')
			self.add_to_latex(self.itemize_dict(arm))

	def write_latex(self):
		output_filename = self.file_path.replace(".xml",".latex")
		with open(output_filename, "w") as outfile:
			outfile.write("\n".join(self.latex_lines))

	def generate_latex(self):
		self.initialize_latex()
		self.add_populations()
		self.add_outcomes()
		self.add_interventions()
		self.add_arms()
		self.close_latex()

	def run(self):
		self.get_trial_schema()
		self.get_trial_object()
		self.generate_latex()
		self.write_latex()

# trial_487 = XMLToLatex('data/487_Viviane.xml')
# trial_487.run()

# trial_487.latex_lines
# trial_487.trial_object['arms']['arm']
# from pprint import pprint
# pprint(trial_487.trial_object['arms']['arm'])
