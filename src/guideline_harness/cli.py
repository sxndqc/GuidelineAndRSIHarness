import argparse
import json
from .data import fetch_streusle, prepare_snacs
from .baselines import run_baselines
from .agent import run_agent

def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('fetch-streusle');p.add_argument('--output',default='data/raw/streusle')
    p=sub.add_parser('prepare-snacs');p.add_argument('--raw',default='data/raw/streusle');p.add_argument('--output',default='data/prepared/snacs')
    p=sub.add_parser('baselines');p.add_argument('--data',default='data/prepared/snacs');p.add_argument('--output',default='results/snacs-controls');p.add_argument('--split',choices=['dev','test'],default='dev')
    p.add_argument('--budgets',default='4,16,64,128');p.add_argument('--seeds',default='11,23,47,83,101')
    p=sub.add_parser('agent');p.add_argument('config')
    args=parser.parse_args()
    if args.command=='fetch-streusle': result=fetch_streusle(args.output)
    elif args.command=='prepare-snacs':result=prepare_snacs(args.raw,args.output)
    elif args.command=='baselines':
        result=run_baselines(args.data,args.output,[int(x) for x in args.budgets.split(',')],[int(x) for x in args.seeds.split(',')],args.split)
        result={k:v for k,v in result.items() if k not in ('runs','source_audit')}
    else: result=run_agent(args.config)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
