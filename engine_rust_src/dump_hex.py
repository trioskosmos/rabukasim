import sys
with open('../data/cards.json', 'rb') as f:
    for line in f:
        if b'LL-bp2-001-R' in line:
            print(line.hex())
            break
