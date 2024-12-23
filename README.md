Built with python3 in mind, no third party dependencies.

For basic instructions run:
`python3 main.py --help`

Baseline review of errors in logs:
```
python3 main.py -p ./qa_ExpTester_PreInterview_Assigment.log -e 0
```
Increment parameter to 1-2 lines for more context on specific errors. 
Or add -n for cleaner results in case there are a lot of exceptions

Show all failed orders, since those are not logged as "ERROR":
```
python3 main.py -p ./qa_ExpTester_PreInterview_Assigment.log -of
```

Performance and error metrics:
```
python3 main.py -p ./qa_ExpTester_PreInterview_Assigment.log -m
```
