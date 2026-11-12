import json
print('EVALS v2.1')
cases=json.load(open('evals/cases.json')); print(f'Cases: {len(cases)}')
print('Grounding target >=0.9, Hallucination target 0')
