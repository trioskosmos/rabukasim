#!/usr/bin/env python
# Bit position analysis

bit_29 = 1 << 29
bit_61 = 1 << 61

bytecode_attr = 536870912
expected_attr = 2305843009213693952

print('Bytecode Analysis:')
print(f'Card 41 bytecode attr = {bytecode_attr}')
print(f'Expected (bit 61)     = {expected_attr}')
print(f'1 << 29               = {bit_29}')
print(f'1 << 61               = {bit_61}')
print(f'Match bit 29? {bytecode_attr == bit_29}')
print(f'Match bit 61? {bytecode_attr == bit_61}')

# Check what FILTER_IS_OPTIONAL should be
from engine.models.generated_metadata import EXTRA_CONSTANTS
filter_optional = EXTRA_CONSTANTS.get('FILTER_IS_OPTIONAL', 'NOT FOUND')
print(f'\nEXTRA_CONSTANTS FILTER_IS_OPTIONAL = {filter_optional}')

print('\n' + '='*60)
print('CONCLUSION: Bug Found!')
print('='*60)
print(f'Bytecode uses bit 29  (value: {bit_29})')
print(f'Code expects bit 61   (value: {bit_61})')
print(f'Difference: {bit_61// bit_29} orders of magnitude!')
print('\nThe optional flag is NOT being detected by Rust handlers!')
