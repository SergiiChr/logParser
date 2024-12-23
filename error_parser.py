import json
import re
from collections import deque
from statistics import quantiles

ERROR = "ERROR"
SYMBOL_ID_REGEX = '\\ssymbol:(\\d+)\\s'
ORDER_API = "/api/v3/order"


def parse_pattern(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def update_preceding_lines(extra_lines: int, log_queue: deque, line: str):
    if extra_lines:
        if log_queue:
            log_queue.popleft()
        log_queue.append(line)


def print_preceding_lines(log_queue: deque):
    if log_queue:
        # Printing preceding {extra_lines} of logs
        while log_queue:
            print(log_queue.popleft())


def get_order_details(order_log: str) -> (str, int):
    expected_parameters = ['type', 'side', 'quantity', 'price']
    parameters = order_log.split(" ")
    print_line = ""
    # not particularly effective but lets you easily customize print order and display.
    # Would use fewer loops if performance is more important
    timestamp_value = 0
    for parameter in parameters:
        if 'timestamp' in parameter:
            timestamp_value = parameter.replace('timestamp:', '')
            print_line += f"[{timestamp_value}] "
            break
    for expected in expected_parameters:
        for parameter in parameters:
            if expected in parameter:
                print_line += parameter + " "
                break
    return print_line, int(timestamp_value)


def parse_resp_code(response_log: str):
    match = re.search("httpStatus:(\\d+)\\s", response_log)
    if match:
        return match.group(1)
    return None


def print_response_details(order_details: str, response_log: str, error: bool, failed_only: bool, dry_run: bool):
    json_start = response_log.index("{")
    json_str = response_log[json_start:]
    resp = json.loads(json_str)
    if error:
        order_details += f" - [ERROR] {json_str}"
    else:
        order_details += f" - [{resp.get('status', 'POSTED')}] orderId:{resp['orderId']} clientOrderId:{resp['clientOrderId']}"
    if failed_only and not error:
        return
    if not dry_run:
        print(order_details)
        trades = resp.get('fills')
        if trades:
            for trade in trades:
                print(f"\t tradeId:{trade['tradeId']} {trade.get('qty')}X{trade.get('price')}")


class LogParser:
    """
    All parsing is done line by line to make sure it doesn't crash with big log files
    """

    def __init__(self, log_path: str):
        self.log_path: str = log_path
        self.start_time = None
        self.end_time = None
        self.resp_times = []
        self.errors = 0

    def print_metrics(self):
        # reusing order parsing to calculate metrics
        self.list_orders(dry_run=True)
        log_time_ms = self.end_time - self.start_time
        log_time_sec = log_time_ms / 1000
        total_orders = len(self.resp_times)
        print(f"Analyzed: {round(log_time_sec, 2)} seconds of log time")
        print(f"Orders per second: {round(total_orders / log_time_sec, 2)}")
        print(f"Total order count: {total_orders}")
        print(f"Total error count: {self.errors}")
        print(f"Error rate: {round(self.errors / total_orders * 100, 2)}%")
        percentiles = quantiles(self.resp_times, n=100)
        print(f"Median proc time: {round(percentiles[49], 2)}ms")
        print(f"99th percentile: {round(percentiles[98], 2)}ms")
        print(f"Slowest order: {round(max(self.resp_times), 2)}ms")

    def list_errors(self, extra_lines: int, stacktrace=True):
        print(f"Filtered errors:")
        next_print: int = 0
        error = False
        # using queue to continuously store preceding lines
        log_queue = deque(maxlen=extra_lines)
        with open(self.log_path) as file:
            for line in file:
                if ERROR in line:
                    print_preceding_lines(log_queue)
                    print(line)
                    next_print = extra_lines
                    error = True
                    continue
                if next_print:
                    print(line)
                    next_print -= 1
                    # avoids double print
                    continue
                if stacktrace and error:
                    # check for stacktrace
                    if "|" not in line:
                        print(line)
                        continue
                    error = False
                update_preceding_lines(extra_lines, log_queue, line)

    def list_symbols(self):
        symbol_ids = set()
        with open(self.log_path) as file:
            for line in file:
                match = re.search(SYMBOL_ID_REGEX, line)
                if match:
                    symbol_ids.add(match.group(1))
        print("Symbol IDs:")
        for symbol_id in symbol_ids:
            print(symbol_id)

    def list_orders(self, failed_only=False, dry_run=False):
        if not dry_run:
            print(f"Orders:")
        first = True
        with open(self.log_path) as file:
            for line in file:
                if ORDER_API in line:
                    timestamp = self.parse_order(line, failed_only, dry_run)
                    if first:
                        self.start_time = timestamp
                        first = False
                    self.end_time = timestamp

    def parse_order(self, line: str, failed_only: bool, dry_run: bool) -> int:
        split_log_line = line.split('|')
        if len(split_log_line) < 4:
            print(f"Unexpected log format:")
            print(line)
            return 0
        response_log = split_log_line[-1]
        order_log = response_log if ORDER_API in response_log else split_log_line[-2]
        order_details, timestamp = get_order_details(order_log)
        resp_code = parse_pattern("httpStatus:(\\d+)\\s", response_log)
        error = resp_code != "200"
        if error:
            self.errors += 1
        proc = parse_pattern("proc:([0-9\\.]+)ms\\s", response_log)
        self.resp_times.append(float(proc))
        order_details += f": {resp_code}"
        print_response_details(order_details, response_log, error, failed_only, dry_run)
        return timestamp
