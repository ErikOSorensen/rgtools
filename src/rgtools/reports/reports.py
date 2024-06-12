
import pandas as pd

import os
import fitz


class Reports:
    def __init__(self,hypotheses_csv="data/1191/1191_G1_VS.xlsx",study_id=1191,base_dir="data/",form_dir=os.path.join("data","04_templates")):
        self.study_id = study_id

        # Directories
        self.template_loc = {"nf_nf": os.path.join(form_dir, "Not Found","Results Reports","allnotfound_postdryrun_fillable.pdf"),
                             "nf_f": os.path.join(form_dir, "Not Found","Results Reports","resultsnotfound_postdryrun_fillable.pdf"),
                             "f_nf": os.path.join(form_dir, "Found","Results Reports","onlyhetnotfound_postdryrun_fillable.pdf"),
                             "f_f": os.path.join(form_dir, "Found","Results Reports","allfound_postdryrun_fillable.pdf")}

        self.front_cover_loc = os.path.join(form_dir, "Front Cover","Results Reports","front_cover.pdf")
        self.found_cover_loc = os.path.join(form_dir, "Found","Results Reports","blank page_found.pdf")
        self.notfound_cover_loc = os.path.join(form_dir, "Not Found","Results Reports","blank page_notfound.pdf")


        # Hypothesis df
        self.hypotheses_df = pd.read_excel(hypotheses_csv, sheet_name="hypothesis")
        self.g0_hypotheses = pd.read_csv("data/1191/1191_G0_VS_csv/hypotheses_df.csv")
        self.g0_heterogeneity = pd.read_csv("data/1191/1191_G0_VS_csv/heterogeneity_df.csv")

        self.main_het_found = None
        self.found_hyp = None
        self.notfound_hyp = None

        # Docs
        self.report_doc = None

        # Coordinates
        self.coords = {"found": {"hypothesis_description": (40.60400390625, 160.193359375, 572, 225),
                                 "hypothesis_num": (118, 142, 130, 162),
                                 "results": (55, 350, 572, 373),
                                 "location": (92.35198974609375, 373, 572, 400)},
                       "notfound": {"hypothesis_num": (118, 128, 130, 128+20),
                                    "hypothesis_description": (35, 147, 572, 147+55),
                                    "results": (55, 350, 572, 373),
                                    "location": (92.35198974609375, 373, 572, 400)}
                          }

    def organize_hypotheses(self):
        '''
        Arrange the hypotheses first by not found and then by found
        :return: self.hypotheses_df
        '''
        self.hypotheses_df = self.g0_heterogeneity.merge(self.hypotheses_df,
                                            left_on=['hypothesis_id', 'subgroups', 'effect_type'],
                                            right_on=["hypothesis_id", "heterogeneity", "separate_different"],
                                            suffixes=("_g0_het", "_g1")) \
            .merge(self.g0_hypotheses,
                   left_on="hypothesis_id",
                   right_on="label",
                   suffixes=("", "_g0_hyp"))

        main_found = self.hypotheses_df.assign(main_found=lambda x: x.comp_found == "yes") \
            .query("heterogeneity=='main'") \
            .groupby("hypothesis_id") \
            .agg(main_found=pd.NamedAgg(column="main_found", aggfunc="all"))

        het_found = self.hypotheses_df.assign(het_found=lambda x: x.comp_found == "yes") \
            .query("heterogeneity!='main'") \
            .groupby("hypothesis_id") \
            .agg(het_found=pd.NamedAgg(column="het_found", aggfunc="any"))

        self.main_het_found = main_found.merge(het_found, left_index=True, right_index=True)
        self.main_het_found = self.main_het_found.sort_values(by=["main_found", "het_found"])
        self.main_het_found['template'] = self.main_het_found \
            .apply(lambda x: 'f_f' if ((x.main_found == True) & (x.het_found == True)) \
            else 'f_nf' if ((x.main_found == True) & (x.het_found == False)) \
            else 'nf_f' if ((x.main_found == False) & (x.het_found == True)) \
            else 'nf_nf', axis=1)

        self.main_het_found['hyp_num'] = range(len(self.main_het_found))
        self.main_het_found['page_num'] = self.main_het_found['hyp_num'] + 3 # Add 3 to account for 2 cover pages and 1-index
        self.main_het_found['template_type'] = self.main_het_found.template.apply(lambda x: x[0])

        unqiue_templates = self.main_het_found['template_type'].unique()
        if len(unqiue_templates)>1:
            self.main_het_found["template_type_lag"] = self.main_het_found.template_type.shift(1, fill_value=
            self.main_het_found.template_type.iloc[0])
            self.main_het_found[
                "template_change"] = self.main_het_found.template_type != self.main_het_found.template_type_lag
            change_page = self.main_het_found.query("template_change==True").hyp_num.iloc[0]
            change_hypotheses = self.main_het_found.iloc[range(change_page, len(self.main_het_found))].index
            self.main_het_found.loc[change_hypotheses, "page_num"] = self.main_het_found.loc[
                                                                         change_hypotheses, "page_num"] + 1


        self.hyp_categories = {
            'nf_nf': self.main_het_found.query("main_found==False & het_found==False"),
            'nf_f': self.main_het_found.query("main_found==False & het_found==True"),
            'f_nf': self.main_het_found.query("main_found==True & het_found==False"),
            'f_f': self.main_het_found.query("main_found==True & het_found==True")
        }

    def get_hypotheses_heterogeneity(self, hyp_id):
        '''
        Get the hypotheses and the associated heterogeneity hypotheses
        :return: self.hypotheses_df
        '''
        main_df = self.hypotheses_df.query("hypothesis_id==@hyp_id & heterogeneity=='main'")
        het_df = self.hypotheses_df.query("hypothesis_id==@hyp_id & heterogeneity!='main'")

        return main_df, het_df

    def assemble_report_pages(self):
        '''
        Create empty pages for the report, one page per hypothesis. Rename the form fields to include the hypothesis number
        :param type:
        :return:
        '''
        multi_doc = fitz.open()
        for type in ["nf_f","nf_nf","f_f","f_nf"]:
            template_loc = self.template_loc[type]
            hyp_list = self.hyp_categories[type].index
            hyp_df = self.hyp_categories[type]
            for doc_index in range(len(hyp_list)):
                page_num = hyp_df.loc[hyp_df.index==hyp_list[doc_index]]['hyp_num'].iloc[0]
                page_num = int(page_num)
                doc = fitz.open(template_loc)
                for widget in doc[0].widgets():
                    widget.field_name = f'{widget.field_name}_{type}_{str(page_num + 1)}'
                    widget.update()
                multi_doc.insert_pdf(doc)
                for widget in doc[0].widgets():
                    multi_doc[page_num].add_widget(widget)
                doc.close()
        return multi_doc

    def add_text(self,page, coords, text):
        rect = fitz.Rect(coords)
        shape = page.new_shape()
        return_val = shape.insert_textbox(rect, text, align="left")
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
        hyp_df = self.hyp_categories[type]
        for doc_index, hyp_id in enumerate(hyp_df.index):
            page_num = hyp_df.hyp_num.iloc[doc_index]
            page = self.report_doc[int(page_num)]

            main_df, het_df = self.get_hypotheses_heterogeneity(hyp_id)

            hypothesis_description = main_df.description.iloc[0]

            coords = self.coords["found" if type in ["f_f","f_nf"] else "notfound"]
            self.add_text(page, coords["hypothesis_num"], str(page_num + 1))
            self.add_text(page, coords["hypothesis_description"] , hypothesis_description)
            if type in ["f_f","nf_f"]:
                results = f'= {main_df["out_units"].iloc[0]}, SE = {main_df["SE"].iloc[0]}'


                p_value = main_df["p_val"].iloc[0]
                p_value = "" if pd.isna(p_value) else str(p_value)
                p_value = f'p_value = {str(p_value)}' if p_value.isnumeric() else p_value
                results = results + f', {p_value}'
                self.add_text(page, coords["results"], results)
                self.add_text(page, coords["location"], str(main_df["location?"].iloc[0]))

            if len(het_df) > 0:
                for index in range(len(het_df)):
                    dim = f'{het_df.iloc[index]["heterogeneity"]} ({het_df.iloc[index]["subgr"]})'
                    eff = het_df.iloc[index]["out_units"] if type in ["f_f","nf_f"] else "Not Found"
                    SE = het_df.iloc[index]["SE"] if type in ["f_f","nf_f"] else "Not Found"

                    field_values = {
                        f'dim {index+1}_' + type+ '_'+ str(page_num + 1): dim,
                        f'eff {index + 1}_' + type+ '_'+ str(page_num + 1): eff,
                        f'SE {index + 1}_' + type+ '_'+ str(page_num + 1): SE
                    }
                    self.update_fields(page,field_values)


    def merge_copy_fields(self,doc1,doc2):
        old_doc1_len = len(doc1)
        doc1.insert_pdf(doc2)
        for doc2_index in range(len(doc2)):
            new_doc_index = old_doc1_len+doc2_index
            for widget in doc2[doc2_index].widgets():
                doc1[new_doc_index].add_widget(widget)
        return doc1

    def run(self):
        self.organize_hypotheses()
        self.report_doc = self.assemble_report_pages()

        if (len(self.hyp_categories["nf_nf"])>0):
            self.insert_hypotheses("nf_nf")
        if (len(self.hyp_categories["nf_f"])>0):
            self.insert_hypotheses("nf_f")
        if (len(self.hyp_categories["f_nf"])>0):
            self.insert_hypotheses("f_nf")
        if (len(self.hyp_categories["f_f"])>0):
            self.insert_hypotheses("f_f")

        # self.report_doc.save(f'data/{self.study_id}/{self.study_id}_report.pdf')
        self.report_doc.save(f'data/results_report.pdf')





# self = Reports()
# self.run()
