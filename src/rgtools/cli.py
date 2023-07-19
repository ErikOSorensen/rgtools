from argparse import ArgumentParser
from .aea_rct_registry.AEAtrials import read_trials, get_trial_from_number, templatedct_from_trialdct, Template, trial_template
from .xml_processing.generate_latex import XMLToLatex

parser = ArgumentParser(prog='rgtools')
subparsers = parser.add_subparsers(dest="command", required=True)

get_trials_parser = subparsers.add_parser("get_trials", help="Get Trial Template from AEA RCT Registry")
get_trials_parser.add_argument('-t', '--trial_id', help="Registration ID from the AEA RCT Registry")

generate_latex_parser = subparsers.add_parser("generate_latex_parser", help="Generate Latex of the coding of AEA RCT Registry")
generate_latex_parser.add_argument('-x', '--xml_path', help="Path to XML File")


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
        XMLToLatex(args.xml_path).run()
