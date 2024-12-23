import argparse

from error_parser import LogParser

ap = argparse.ArgumentParser()
ap.add_argument("-p", "--path", required=True,
                help="Path to a log file")

ap.add_argument("-s", "--symbols", required=False, action='store_true',
                help="Returns a list of symbols. No parameters")

ap.add_argument("-o", "--orders", required=False, action='store_true',
                help="Returns a list of orders and order details.")
ap.add_argument("-f", "--failed", required=False, action='store_true',
                help="Flag for order scanning to only show failed orders.")

ap.add_argument("-e", "--errors", required=False, type=int, default=-1,
                help="Returns a list of errors in the logs. "
                     "Add an int parameter to include N preceding/following log entries. "
                     "e.g -e 2 will return error entries and 2 additional entries before and after the error")
ap.add_argument("-n", "--no-stacktrace", required=False, action='store_true',
                help="Flag for error scanning to include following stacktraces. "
                     "Optional since it can make the output quite noisy")

ap.add_argument("-m", "--metrics", required=False, action='store_true',
                help="Display error and performance metrics")
args = ap.parse_args()

if __name__ == '__main__':
    parser = LogParser(args.path)
    if args.symbols:
        parser.list_symbols()
    if args.orders:
        parser.list_orders(args.failed)
    if args.errors > -1:
        parser.list_errors(extra_lines=args.errors, stacktrace = not args.no_stacktrace)
    if args.metrics:
        parser.print_metrics()
