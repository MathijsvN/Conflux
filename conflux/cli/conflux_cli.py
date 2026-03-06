import argparse


def main():
    parser = argparse.ArgumentParser(prog="conflux")
    sub = parser.add_subparsers(dest="command")
    tr = sub.add_parser("translate", help="translate between formalisms")
    tr.add_argument("--from", dest="frm", required=True)
    tr.add_argument("--to", dest="to", required=True)
    tr.add_argument("--in", dest="infile", required=True)
    tr.add_argument("--out", dest="outfile", required=True)
    args = parser.parse_args()
    if args.command == "translate":
        # TODO: call translator
        print(f"Translating {args.frm} -> {args.to} from {args.infile} to {args.outfile}")
