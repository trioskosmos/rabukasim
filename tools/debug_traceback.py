import sys, traceback, json
from compiler.main import parse_member
try:
    data=json.load(open('data/cards.json', encoding='utf-8'))
    card = data['PL!SP-pb1-001-R']
    m = parse_member(4684, 'PL!SP-pb1-001-R', card)
except Exception as e:
    traceback.print_exc(file=sys.stdout)
