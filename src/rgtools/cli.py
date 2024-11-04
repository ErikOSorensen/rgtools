from argparse import ArgumentParser

import pandas as pd
import logging

from .aea_rct_registry.AEAtrials import read_trials, get_trial_from_number, templatedct_from_trialdct, Template, trial_template
from .xml_processing.generate_latex import XMLToLatex
from .reports.reports import Reports

parser = ArgumentParser(prog='rgtools')
subparsers = parser.add_subparsers(dest="command", required=True)

get_trials_parser = subparsers.add_parser("get_trials", help="Get Trial Template from AEA RCT Registry")
get_trials_parser.add_argument('-t', '--trial_id', help="Registration ID from the AEA RCT Registry")

generate_latex_parser = subparsers.add_parser("generate_latex_parser", help="Generate Latex of the coding of AEA RCT Registry")
generate_latex_parser.add_argument('-x', '--xml_path', help="Path to XML File")
generate_latex_parser.add_argument('-a', '--all',  action='store_true', help="Process G0 for all files")
generate_latex_parser.add_argument('-d', '--dir', required=False , default="data/01_Production/", help="Process G0 for all files")


generate_report_parser = subparsers.add_parser("generate_report", help="Generate Filled-in Report of the study")
generate_report_parser.add_argument('-m', '--meta_path', help="Path to Hypothesis Analytical Dataset", required=True)

generate_report_parser.add_argument('-x', '--xml_path', help="Path to XML File")

generate_report_parser.add_argument('-a', '--all',  action='store_true', help="Generate report for all files")
generate_report_parser.add_argument('-a', '--all',  action='store_true', help="Generate report for all files")
generate_report_parser.add_argument('-t', '--tracker_path', help="Path to Tracker")



logging.basicConfig(level=logging.INFO)

def get_trials(args):
    trials = read_trials()
    trialno = int(args.trial_id)
    trial = get_trial_from_number(trials, trialno)
    tdct = templatedct_from_trialdct(trial)
    t = Template(trial_template)
    # print(str(trial))
    print(t.safe_substitute(tdct))



def main(args=None):
    args = parser.parse_args(args=args)
    if args.command=='get_trials':
        get_trials(args)

    elif args.command=="generate_latex_parser":
        if not args.all:
            XMLToLatex(args.xml_path).run()
        else:
            # df = pd.read_csv('data/RGPB FY24 Workplan - Study Progress Tracker.csv')
            # df = df.loc[df['Meets Goal?']=="Yes",]
            df = pd.read_csv(args.tracker_path)
            df = df.loc[df['Study Status']=="Complete",]
            rct_ids = df.copy()
            rct_ids['study_id'] = rct_ids['RCT_ID'].str.replace("AEARCTR-","").astype(int)
            rct_ids['author'] = ""
            rct_ids.loc[rct_ids.Assignee=="Gufran",'author'] = "GP"
            rct_ids.loc[rct_ids.Assignee=="Viviane",'author'] = "VS"
            rct_ids.loc[(rct_ids.Assignee=="Both"),'author'] = "Both"
            base_dir = "data/01_Production/"
            rct_ids['path'] = base_dir + rct_ids.study_id.astype(str) + "/" + rct_ids.study_id.astype(str)+"_G0_" + rct_ids.author +".xml"
            xml_list = rct_ids.path.tolist()
            failed_xml = []
            for xml_path in xml_list:
                try:
                    XMLToLatex(xml_path).run()
                    logging.info(f'Completed succesfully: {xml_path}')
                except:
                    failed_xml.append(xml_path)
                    logging.warning(f'Failed: {xml_path}')
            if len(failed_xml)>0:
                logging.warning(f'The following XML failed: {", ".join(failed_xml)}')

    elif args.command == "generate_report":
        if not args.all:
            Reports(args.xml_path, args.meta_path).run()
        else:
            df = pd.read_csv(args.tracker_path)
            # df = df.loc[df['Meets Goal?']=="Yes",]
            df = df.loc[df['Study Status']=="Complete",]
            rct_ids = df.copy()
            rct_ids['study_id'] = rct_ids['RCT_ID'].str.replace("AEARCTR-","").astype(int)
            rct_ids['author'] = ""
            rct_ids.loc[rct_ids.Assignee=="Gufran",'author'] = "GP"
            rct_ids.loc[rct_ids.Assignee=="Viviane",'author'] = "VS"
            rct_ids.loc[(rct_ids.Assignee=="Both"),'author'] = "Both"
            base_dir = "data/01_Production/"
            rct_ids['path'] = base_dir + rct_ids.study_id.astype(str) + "/" + rct_ids.study_id.astype(str)+"_G0_" + rct_ids.author +".xml"
            xml_list = rct_ids.path.tolist()
            failed_xml = []
            for xml_path in xml_list:
                try:
                    Reports(xml_path, args.meta_path).run()
                    logging.info(f'Completed succesfully: {xml_path}')
                except:
                    failed_xml.append(xml_path)
                    logging.warning(f'Failed: {xml_path}')
            if len(failed_xml)>0:
                logging.warning(f'The following XML failed: {", ".join(failed_xml)}')






