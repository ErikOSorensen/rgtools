import os.path

from xmlschema import XMLSchema
from rgtools.xml_processing.proccess_xml import XMLProcessor
import subprocess

class XMLToLatex:
	def __init__(self, file_path):
		self.file_path = file_path
		self.trial_schema = None
		self.trial_object = None
		self.latex_lines = []
		self.xml_processor = XMLProcessor(file_path=file_path)

	def add_to_latex(self,line):
		if isinstance(line,str):
			self.latex_lines.append(line)
		elif isinstance(line,list):
			self.latex_lines += line

	def escape_text(self,text):
		if not text:
			return text
		text = str(text).replace("_","\_")
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
		self.add_to_latex("\documentclass[6pt]{article}")
		self.add_to_latex("\\usepackage{booktabs}")
		self.add_to_latex("\\usepackage{multirow}")
		self.add_to_latex("\\usepackage{multicol}")
		self.add_to_latex("\\usepackage{tabularx}")
		self.add_to_latex("\\usepackage[left=1cm, right=1cm,top=1cm,bottom=1cm]{geometry}")
		self.add_to_latex("\\begin{document}")
		self.add_to_latex("\\noindent\\textbox{\Large AEA RCT Trial Registration Summary\hfill}\\textbox{\hfill \# 487}\\\\[6pt]")
		self.add_to_latex("\\textbf{Title:} "+self.xml_processor.trial_object['title'].strip())
		trial_id = self.xml_processor.trial_object['registration_number']
		pi = self.xml_processor.trial_object['owners']['researcher'][0]['name']
		url_author="\\\\[6pt] \\noindent\\textbox{\small https://www.socialscienceregistry.org/trials/"+trial_id+"\hfill}\\textbox{\hfil  \hfil}\\textbox{\hfill \small Contact: "+pi+" }"
		self.add_to_latex(url_author)


		# self.add_to_latex("\\title{AEA RCT Trial Registration}")
		# self.add_to_latex(f"\\author{{RCT Trial ID: {self.trial_object['registration_number']}}}")
		# self.add_to_latex("\\begin{document}")
		# self.add_to_latex("\\maketitle")



	def close_latex(self):
		self.add_to_latex("\end{document}")

	# def add_populations(self):
	# 	self.add_to_latex("\section{Populations}")
	# 	for population in self.trial_object['populations']['population']:
	# 		label = population['label']
	# 		self.add_to_latex(f'\subsection{{{self.escape_text(label)}}}')
	# 		self.add_to_latex(self.itemize_dict(population))

	def pandas_to_latex(self,df,label_col=None,column_format=None,caption=None):
		# if label_col:
		# 	df[label_col] = df[label_col].apply(self.escape_text)
		df.index = df.index+1
		# populations_df.index.names = ["#"]
		self.add_to_latex("\\footnotesize")
		latex = df.to_latex(escape=True,column_format=column_format)
		latex = latex.replace("tabular","tabularx")
		latex = latex.replace("\\begin{tabularx}","\\begin{tabularx}{\\textwidth}")
		self.add_to_latex("\section{"+caption+"}")
		self.add_to_latex(latex)

	def add_populations(self):
		populations_df = self.xml_processor.populations_df[['label','country','unit_of_randomization','target_sample_size','coverage']]
		populations_df = populations_df.rename(columns={'target_sample_size':'N','unit_of_randomization':'Randomization'})
		self.pandas_to_latex(populations_df,
							 label_col="label",
							 column_format="p{0.1cm}p{1cm}p{1cm}p{2cm}p{3cm}X",
							 caption="Populations")


	def add_outcomes(self):
		outcomes_df = self.xml_processor.outcomes_df[['label','unit_original', 'unit_analytical','description']]
		self.pandas_to_latex(outcomes_df,
							 label_col="label",
							 column_format="p{0.1cm}p{3.5cm}p{2cm}p{2cm}X",
							 caption="Outcomes")
		# self.add_to_latex("\section{Outcomes}")
		# for outcome in self.trial_object['main_outcomes']['main_outcome']:
		# 	label = outcome['label']
		# 	self.add_to_latex(f'\subsection{{{self.escape_text(label)}}}')
		# 	self.add_to_latex(self.itemize_dict(outcome))

	def add_interventions(self):
		self.pandas_to_latex(self.xml_processor.interventions_df,
							 label_col="label",
							 column_format="p{0.1cm}p{3.5cm}X",
							 caption="Interventions")
		# self.add_to_latex("\section{Interventions}")
		# for intervention in self.trial_object['interventions']['intervention']:
		# 	label = intervention['label']
		# 	self.add_to_latex(f'\subsection{{{self.escape_text(label)}}}')
		# 	self.add_to_latex(self.itemize_dict(intervention))

	def add_arms(self):
		self.pandas_to_latex(self.xml_processor.arms_df,
							 label_col="label",
							 column_format="p{0.1cm}p{3.5cm}p{3cm}X",
							 caption="Arms")
		# self.add_to_latex("\section{Arms}")
		# for arm in self.trial_object['arms']['arm']:
		# 	label = arm['label']
		# 	self.add_to_latex(f'\subsection{{{self.escape_text(label)}}}')
		# 	self.add_to_latex(self.itemize_dict(arm))

	def generate_latex(self):
		self.initialize_latex()
		self.add_populations()
		self.add_outcomes()
		self.add_interventions()
		self.add_arms()
		self.close_latex()

	def write_latex(self):
		output_filename = self.file_path.replace(".xml",".tex")
		with open(output_filename, "w") as outfile:
			outfile.write("\n".join(self.latex_lines))

	def tex_to_pdf(self):
		absolute_path = os.path.abspath(self.file_path).replace("\\","/")
		tex_filename = absolute_path.replace(".xml",".tex")
		subprocess.call(['pdflatex','-interaction','nonstopmode',"-output-directory",os.path.dirname(tex_filename),tex_filename])




	def run(self):
		self.xml_processor.run()
		self.get_trial_schema()
		self.get_trial_object()
		self.generate_latex()
		self.write_latex()
		self.tex_to_pdf()

# xml_processing = XMLToLatex('556_G0_GP.xml')
# xml_processing.run()
# # xml_processing.xml_processor.populations_df.to_latex()
# xml_processing.xml_processor.trial_object['owners']['researcher'][0]['name']