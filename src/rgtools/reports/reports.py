
import pandas as pd

import os
import fitz
import numpy as np

from rgtools.xml_processing.proccess_xml import XMLProcessor

class Study:
    def __init__(self,xml_directory):
        self.xml_directory = xml_directory
        self.trial = XMLProcessor(self.xml_directory)
        self.get_paths()
        self.get_trial_info()


    def get_trial_info(self):
        self.trial.get_trial_schema()
        self.trial.get_trial_object()
        self.author = self.trial.trial_object["owners"]["researcher"][0]["name"].split(" ")[-1]
        self.trial_url = f"https://www.socialscienceregistry.org/trials/{str(self.study_id)}"
        self.g0_url = f"https://go.cega.org/RGPBDetails{str(self.study_id)}"
        self.title = self.trial.trial_object['title']

    def get_paths(self):
        self.study_directory = os.path.dirname(self.xml_directory)
        self.basename = os.path.splitext(os.path.basename(self.xml_directory))[0]
        self.study_id = int(self.basename.split("_")[0])
        self.coder = self.basename.split("_")[2]

class Hypotheses:
    def __init__(self,study_id, meta_path):
        self.study_id = study_id
        self.reference_df = pd.read_csv(meta_path)
        self.reference_df = self.reference_df.query("((study_id==@study_id) & (keep_expansion))")
        self.reference_df['estimate'] = self.reference_df.es.combine_first(self.reference_df.out_units)

        self.organize_hypotheses()

    def organize_hypotheses(self):
        '''
        Arrange the hypotheses first by not found and then by found
        :return: self.hypotheses_df
        '''

        main_found = self.reference_df.assign(main_found=lambda x: x.completely_available) \
            .query("(is_main==True) & (keep_expansion==True)") \
            .groupby(["hypothesis_id", "description"]) \
            .agg(main_found=pd.NamedAgg(column="main_found", aggfunc="all"))\
            .reset_index(level=1)

        het_found = self.reference_df.assign(het_found=lambda x: x.completely_available) \
            .query("(is_main==False) & (keep_expansion==True)") \
            .groupby("hypothesis_id") \
            .agg(het_found=pd.NamedAgg(column="completely_available", aggfunc="all"),
                 het_n=pd.NamedAgg(column="completely_available", aggfunc=len),
                 het_found_n = pd.NamedAgg(column="het_found", aggfunc="sum"))



        self.main_het_found = main_found.merge(het_found, left_index=True, right_index=True, how='left')
        self.main_het_found = self.main_het_found.sort_values(by=["main_found", "het_found"])
        self.main_het_found['template'] = self.main_het_found \
            .apply(lambda x: 'f_f' if ((x.main_found == True) & ((np.isnan(x.het_found)) | (x.het_found == True))) \
            else 'f_nf' if ((x.main_found == True) & ((x.het_found == False))) \
            else 'nf_f' if ((x.main_found == False) & ((np.isnan(x.het_found)) | (x.het_found == True))) \
            else 'nf_nf', axis=1)

        self.main_het_found['hyp_num'] = range(len(self.main_het_found))
        self.main_het_found['page_num'] = self.main_het_found['hyp_num'] + 2 # Add 3 to account for 2 cover pages and 1-index
        self.main_het_found['template_type'] = self.main_het_found.template.apply(lambda x: 'f' if x=='f_f' else 'n')

        unqiue_templates = self.main_het_found['template_type'].unique()
        self.main_het_found['template_change'] = False
        if len(unqiue_templates)>1:
            self.main_het_found["template_type_lag"] = self.main_het_found.template_type.shift(1, fill_value=
            self.main_het_found.template_type.iloc[0])
            self.main_het_found[
                "template_change"] = self.main_het_found.template_type != self.main_het_found.template_type_lag
            change_page = self.main_het_found.query("template_change==True").hyp_num.iloc[0]
            change_hypotheses = self.main_het_found.iloc[range(change_page, len(self.main_het_found))].index
            self.main_het_found.loc[change_hypotheses, "page_num"] = self.main_het_found.loc[
                                                                         change_hypotheses, "page_num"] + 1
        self.main_het_found['extra_heterogeneity'] = self.main_het_found.het_n > 5

        if self.main_het_found.extra_heterogeneity.any():
            self.main_het_found["extra_heterogeneity_cumsum"]=self.main_het_found.extra_heterogeneity.cumsum()
            self.main_het_found["extra_heterogeneity_cumsum_lag"]=self.main_het_found.extra_heterogeneity_cumsum.shift(1, fill_value=0)

            self.main_het_found['page_num']  = self.main_het_found.extra_heterogeneity_cumsum_lag + self.main_het_found.page_num

        self.hyp_categories = {
            'nf_nf': self.main_het_found.query("(main_found==False) & (het_found==False)"),
            'nf_f': self.main_het_found.query("(main_found==False) & (het_found.isna() | het_found==True)"),
            'f_nf': self.main_het_found.query("(main_found==True) & (het_found==False)"),
            'f_f': self.main_het_found.query("(main_found==True) & (het_found.isna() | het_found==True)")
        }

        self.all_hypotheses_n = int(len(self.main_het_found))
        self.found_hypotheses_n = int(len(self.hyp_categories['f_f']) + len(self.hyp_categories['f_nf']))
        self.notfound_hypotheses_n = int(len(self.hyp_categories['nf_f']) + len(self.hyp_categories['nf_nf']))
        self.het_n = int(self.main_het_found.het_n.sum())
        self.het_found_n = int(self.main_het_found.het_found_n.sum())

    def get_hypotheses_heterogeneity(self, hyp_id):
        '''
        Get the hypotheses and the associated heterogeneity hypotheses
        :return: self.hypotheses_df
        '''
        main_df = self.reference_df.query("hypothesis_id==@hyp_id & is_main")
        het_df = self.reference_df.query("hypothesis_id==@hyp_id & ~is_main")
        # self.hypotheses.reference_df.columns
        return main_df, het_df




class Reports:
    def __init__(self,xml_directory,meta_path,form_dir=os.path.join("data","04_templates")):
        self.xml_directory = xml_directory
        self.study = Study(xml_directory)
        self.hypotheses = Hypotheses(self.study.study_id,meta_path)

        # Directories
        self.template_loc = {"nf_nf": os.path.join(form_dir, "Not Found","Results Reports","allnotfound_fillable.pdf"),
                             "nf_f": os.path.join(form_dir, "Not Found","Results Reports","resultsnotfound_fillable.pdf"),
                             "f_nf": os.path.join(form_dir, "Found","Results Reports","onlyhetnotfound_fillable.pdf"),
                             "f_f": os.path.join(form_dir, "Found","Results Reports","allfound_fillable.pdf")}

        self.front_cover_loc = os.path.join(form_dir,"Cover letters","RCT Registry Results Report _ Cover page_T2 and T3.pdf")
        self.found_cover_loc = os.path.join(form_dir, "Found","Results Reports","blank page_found.pdf")
        self.notfound_cover_loc = os.path.join(form_dir, "Not Found","Results Reports","blank page_notfound.pdf")
        self.extra_heterogeneity_loc = os.path.join(form_dir, "Supplement","supplement_fillable.pdf")


        # Hypothesis df
        # self.hypotheses_df = pd.read_excel(self.g1_hypotheses_loc , sheet_name="hypothesis")
        # self.g0_hypotheses = pd.read_csv(self.g0_hypotheses_loc)
        # self.g0_heterogeneity = pd.read_csv(self.g0_heterogeneity_loc)

        # Docs
        self.report_doc = None

        # Coordinates
        self.coords = {"found": {"hypothesis_description": (40.60400390625, 160.193359375, 572, 160+90),
                                 "hypothesis_num": (118, 142, 118+30, 162),
                                 "results": (55, 350, 572, 373),
                                 "location": (92.35198974609375, 373, 572, 400),
                                 "header_constant": (120, 97, 572, 97+20),
                                 "header":(40, 113, 572, 113+50)},
                       "notfound": {"hypothesis_num": (118, 128, 118+30, 128+20),
                                    "hypothesis_description": (35, 147, 572, 147+90),
                                    "results": (55, 350, 572, 373),
                                    "location": (92.35198974609375, 373, 572, 400),
                                    "header_constant": (120, 90, 572, 90+20),
                                    "header":(40, 105, 572, 105+50)},
                       "cover": {"title": (70, 225, 70 + 475, 225 + 200),
                                "summary": (70, 385, 70 + 475, 385 + 200)
                                 }
                          }

        # texts
        self.header_constant_text = f'Questions about how to fill in this report? See this <a href="https://go.cega.org/RGPBExplainers">brief explainer</a> and this <a href="https://go.cega.org/RGPBFilledExample">pre-filled example</a>.'
        self.header_text = f'<a href="{self.study.trial_url}">Here</a> is your original registration, and the attachment <a href="{self.study.g0_url}">details_{self.study.author}.pdf</a> contains the details of how your registration was encoded.'

    def assemble_report_pages(self):
        '''
        Create empty pages for the report, one page per hypothesis. Rename the form fields to include the hypothesis number
        :param type:
        :return:
        '''
        multi_doc = fitz.open(self.front_cover_loc)
        first_cover_loc = self.notfound_cover_loc if self.hypotheses.main_het_found.template_type.iloc[0]=="n" else self.found_cover_loc
        first_cover = fitz.open(first_cover_loc)
        multi_doc.insert_pdf(first_cover)
        for type in ["nf_nf", "nf_f","f_nf","f_f"]:
            template_loc = self.template_loc[type]
            hyp_list = self.hypotheses.hyp_categories[type].index
            hyp_df = self.hypotheses.hyp_categories[type]
            for doc_index in range(len(hyp_list)):
                page_num = hyp_df.loc[hyp_df.index==hyp_list[doc_index]]['page_num'].iloc[0]
                page_num = int(page_num)
                if hyp_df.loc[hyp_df.index==hyp_list[doc_index]]['template_change'].iloc[0]:
                    multi_doc.insert_pdf(fitz.open(self.found_cover_loc))
                doc = fitz.open(template_loc)
                for widget in doc[0].widgets():
                    widget.field_name = f'{widget.field_name}_{type}_{str(page_num + 1)}'
                    widget.update()
                multi_doc.insert_pdf(doc)
                for widget in doc[0].widgets():
                    multi_doc[page_num].add_widget(widget)
                doc.close()
                if hyp_df.loc[hyp_df.index==hyp_list[doc_index]]['extra_heterogeneity'].iloc[0]:
                    doc = fitz.open(self.extra_heterogeneity_loc)
                    page_num += 1 # Extra heterogeneity page is on the next page
                    for widget in doc[0].widgets():
                        widget.field_name = f'{widget.field_name}_{type}_{str(page_num + 1)}'
                        widget.update()
                    multi_doc.insert_pdf(doc)
                    for widget in doc[0].widgets():
                        multi_doc[page_num].add_widget(widget)
                    doc.close()

        return multi_doc

    def add_text(self,page, coords, text,type="text",fontname='helv',fontsize=11,align=0, render_mode=0, border_width=1):
        rect = fitz.Rect(coords)
        shape = page.new_shape()
        texbox_function = page.insert_htmlbox if type=="html" else shape.insert_textbox
        if type=="html":
            return_val = page.insert_htmlbox(rect, text, css="* {font-family:sans-serif;font-size:8px;}")
        elif type=="text":
            return_val = shape.insert_textbox(rect, text,align=align,fontname=fontname, fontsize=fontsize, render_mode=render_mode, border_width=border_width)
        shape.commit()

    def update_fields(self,page,field_values):
        widgets = list(page.widgets())
        widget_labels = [widget.field_name for widget in widgets]
        # print(widget_labels)

        for widget_label in field_values:
            widget_index = widget_labels.index(widget_label)
            widget = widgets[widget_index]
            widget_value = field_values[widget_label]
            widget.field_value = str(widget_value)
            widget.update()


    def insert_hypotheses(self,type="nf_nf"):
        hyp_df = self.hypotheses.hyp_categories[type]

        # Insert Hypotheses summary in cover page
        hypotheses_summary = f'We extracted {self.hypotheses.all_hypotheses_n} main hypotheses'
        if self.hypotheses.het_n>0:
            hypotheses_summary += f' and {self.hypotheses.het_n} heterogeneity tests'
        hypotheses_summary += f' from the registration. We found results for {self.hypotheses.found_hypotheses_n} main hypotheses'
        if self.hypotheses.het_n>0:
            hypotheses_summary += f' and {self.hypotheses.het_found_n} heterogeneity tests.'
        # hypotheses_summary += f'. We were unable to find results for {self.hypotheses.notfound_hypotheses_n} main hypothesis'
        # if self.hypotheses.het_n>0:
        #     hypotheses_summary += f' and {self.hypotheses.het_n - self.hypotheses.het_found_n} heterogeneity tests'
        # hypotheses_summary += f'.'
        self.add_text(self.report_doc[0], self.coords['cover']['title'], self.study.title,align=1,fontsize=12, fontname="helvetica-bold")
        self.add_text(self.report_doc[0], self.coords['cover']['summary'], hypotheses_summary)




        for doc_index, hyp_id in enumerate(hyp_df.index):
            page_num = int(hyp_df.page_num.iloc[doc_index])
            hyp_num = hyp_df.hyp_num.iloc[doc_index]
            page = self.report_doc[page_num]

            main_df, het_df = self.hypotheses.get_hypotheses_heterogeneity(hyp_id)
            # main_df, het_df = self.hypotheses.get_hypotheses_heterogeneity('letter_effect')

            hypothesis_description = main_df.description.iloc[0][0:300]

            coords = self.coords["found" if type in ["f_f","f_nf"] else "notfound"]
            self.add_text(page, coords["hypothesis_num"], str(hyp_num + 1))
            self.add_text(page, coords["hypothesis_description"] , hypothesis_description)
            self.add_text(page, coords["header_constant"], self.header_constant_text,fontsize=8, type="html")
            self.add_text(page, coords["header"], self.header_text,fontsize=8, type="html")
            if type in ["f_f","f_nf"]:
                results = f'= {main_df["estimate"].iloc[0]}, SE = {main_df["SE"].iloc[0]}'


                p_value = main_df["p_val"].iloc[0]
                p_value = "" if pd.isna(p_value) else str(p_value)
                p_value = f'p-value: p = {str(p_value)}' if p_value.replace('.','',1).isdigit() else f'p-value: {p_value}'
                results = results + f', {p_value}' if p_value != "p-value: " else results
                self.add_text(page, coords["results"], results)
                self.add_text(page, coords["location"], str(main_df["location"].iloc[0]))

            het_n = len(het_df)
            if het_n>0:
                min_het_n = min(5,het_n)
                for index in range(min_het_n):
                    # print("In main")
                    dim = f'{het_df.iloc[index]["heterogeneity"]}'
                    subgr = f'({het_df.iloc[index]["subgr"]})'
                    dim = dim + subgr if subgr != "(nan)" else dim
                    # print(f'Index: {index} hyp_id: {hyp_id} dim: {dim}')
                    eff = het_df.iloc[index]["estimate"] if het_df.iloc[index]["completely_available"] else "Not Found"
                    SE = het_df.iloc[index]["SE"] if het_df.iloc[index]["completely_available"] else "Not Found"


                    field_values = {
                        f'dim {index+1}_' + type+ '_'+ str(page_num + 1): dim,
                        f'eff {index + 1}_' + type+ '_'+ str(page_num + 1): eff,
                        f'SE {index + 1}_' + type+ '_'+ str(page_num + 1): SE
                    }

                    if np.isnan(het_df.iloc[index]["estimate"]) and np.isnan(het_df.iloc[index]["SE"]) and het_df.iloc[index]["completely_available"]:
                        field_values[f'other {index + 1}_' + type + '_' + str(
                            page_num + 1)] = "The estimates were found in some form but in a format that doesn’t fit this results report"

                    self.update_fields(page,field_values)
                if het_n>5:
                    page_num += 1
                    page = self.report_doc[page_num]
                    for index in range(5, het_n):
                        # print("In extra")
                        dim = f'{het_df.iloc[index]["heterogeneity"]}'
                        subgr = f'({het_df.iloc[index]["subgr"]})'
                        dim = dim + subgr if subgr != "(nan)" else dim
                        # print(f'Index: {index} hyp_id: {hyp_id} dim: {dim}')
                        eff = het_df.iloc[index]["estimate"] if type in ["f_f", "nf_f"] else "Not Found"
                        SE = het_df.iloc[index]["SE"] if type in ["f_f", "nf_f"] else "Not Found"

                        field_values = {
                            f'hyp #_' + type + '_' + str(page_num + 1): hyp_num + 1,
                            f'dim {index + 1 - 5}_' + type + '_' + str(page_num + 1): dim,
                            f'eff {index + 1 - 5}_' + type + '_' + str(page_num + 1): eff,
                            f'SE {index + 1 - 5}_' + type + '_' + str(page_num + 1): SE
                        }
                        if np.isnan(het_df.iloc[index]["estimate"]) and np.isnan(het_df.iloc[index]["SE"]) and het_df.iloc[index]["completely_available"]:
                            field_values[f'other {index + 1}_' + type + '_' + str(
                                page_num + 1)] = "The estimates were found in some form but in a format that doesn’t fit this results report"

                        self.update_fields(page, field_values)

    def run(self):
        self.report_doc = self.assemble_report_pages()

        for type in ["nf_nf", "nf_f","f_nf","f_f"]:
            if (len(self.hypotheses.hyp_categories[type])>0):
                self.insert_hypotheses(type)

        # self.report_doc.save(f'data/{self.study_id}/{self.study_id}_report.pdf')
        self.report_doc.save(os.path.join(self.study.study_directory,f'ResultsReport_{self.study.study_id}.pdf'))
        self.hypotheses.main_het_found.to_csv(os.path.join(self.study.study_directory,f'{self.study.study_id}_report_metadata.csv'))


# self = Reports(xml_directory="data/01_Production/291/291_G0_GP.xml",meta_path="data/06_analytical/01_batch1/to_keep_expansions_0a2258971d55d3850c85cc88bcba04d8.csv")
# self.run()
# Reports(xml_directory="data/01_Production/291/291_G0_GP.xml").run()
# Reports(xml_directory="data/01_Production/604/604_G0_GP.xml").run()
# Reports(xml_directory="data/01_Production/558/558_G0_GP.xml").run()
# Reports(xml_directory="data/01_Production/569/569_G0_VS.xml").run()
# Reports(xml_directory="data/01_Production/633/633_G0_GP.xml").run()
# Reports(xml_directory="data/01_Production/634/634_G0_GP.xml").run()
# Reports(xml_directory="data/01_Production/543/543_G0_VS.xml").run()
# Reports(xml_directory="data/01_Production/641/641_G0_GP.xml").run()
# Reports(xml_directory="data/01_Production/643/643_G0_GP.xml").run()
# Reports(xml_directory="data/01_Production/630/630_G0_VS.xml").run()

