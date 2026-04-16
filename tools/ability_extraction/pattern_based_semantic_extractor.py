#!/usr/bin/env python3
"""
Pattern-based semantic extractor - automatically builds semantic AST from template syntax
Uses pattern rules to identify structure and extract variables automatically
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class SemanticAbility:
    """Semantic AST structure for an ability"""
    timing: Dict[str, Any]
    cost: Optional[Dict[str, Any]]
    conditions: List[Dict[str, Any]]
    selector: Optional[Dict[str, Any]]
    action: Dict[str, Any]
    postcondition: Optional[Dict[str, Any]]
    duration: Optional[Dict[str, Any]]
    choice: Optional[Dict[str, Any]]
    sequential_operations: Optional[List[Dict[str, Any]]]
    conditional_branching: Optional[Dict[str, Any]]
    choice_branching: Optional[Dict[str, Any]]
    original_text: str
    original_template: str
    matched_patterns: List[str]


class OperationTaxonomy:
    """Specific operation types for semantic classification"""
    
    # Condition types
    CONDITIONS = {
        'score_comparison_condition': r'\[value_type:score\].*?(より高い|以上|以下|未満)',
        'presence_condition': r'(いる|ある)場合',
        'count_condition': r'\[number\]枚以上|\[number\]枚以下',
        'zone_condition': r'\[zone_condition\]に|\[zone\]に',
        'group_condition': r'『\[group_name\]』の'
    }
    
    # Source types
    SOURCES = {
        'zone_source': r'\[zone\]から|\[zone_condition\]から',
        'hand_source': r'手札から',
        'deck_source': r'山札から|デッキから',
        'stage_source': r'ステージから',
        'energy_source': r'エネルギーから',
        'discard_source': r'控え室から'
    }
    
    # Action types
    ACTIONS = {
        'draw_from_zone': r'(引く|加える).*?\[zone\]に',
        'move_to_zone': r'(移動|置く).*?\[zone\]に',
        'place_in_zone_state': r'(置く|配置).*?(状態|で)',
        'grant_score_modifier': r'\[value_type:score\].*?[+-]',
        'grant_resource': r'(ハート|ブレード|\[heart\]|\[blade\]).*?得る',
        'activate_card': r'アクティブにする',
        'deactivate_card': r'ウェイトにする',
        'reveal_card': r'公開する',
        'destroy_card': r'(破壊|捨てる)',
        'gain_life': r'ライフ.*?[+-]'
    }
    
    # Trigger types
    TRIGGERS = {
        'movement_trigger': r'移動するたび',
        'score_threshold_trigger': r'\[value_type:score\].*?(より高い|以上|以下)',
        'card_play_trigger': r'(登場|プレイ)するたび',
        'live_start_trigger': r'ライブ開始時',
        'live_end_trigger': r'ライブ終了時',
        'live_success_trigger': r'ライブ成功時',
        'turn_start_trigger': r'ターン開始時',
        'turn_end_trigger': r'ターン終了時'
    }
    
    @classmethod
    def classify_operation(cls, template: str, operation_type: str) -> str:
        """Classify an operation into specific type based on template patterns"""
        # Check triggers first (they're most specific)
        for trigger_name, pattern in cls.TRIGGERS.items():
            if re.search(pattern, template):
                return trigger_name
        
        # Check conditions
        for condition_name, pattern in cls.CONDITIONS.items():
            if re.search(pattern, template):
                return condition_name
        
        # Check sources
        for source_name, pattern in cls.SOURCES.items():
            if re.search(pattern, template):
                return source_name
        
        # Check actions
        for action_name, pattern in cls.ACTIONS.items():
            if re.search(pattern, template):
                return action_name
        
        # Return original operation type if no specific classification found
        return operation_type


class JapaneseGrammarParser:
    """Parse Japanese grammar structure for context-aware semantic extraction"""
    
    # Zone relationship particles
    ZONE_PARTICLES = {
        'から': 'from',  # source zone
        'に': 'to',      # destination zone
        'で': 'in',      # location/state
        'の': 'of',      # possession/relationship
        'を': 'object'   # direct object marker
    }
    
    # Comparison operators
    COMPARISON_OPERATORS = {
        'より高い': 'greater_than',
        'より低い': 'less_than',
        '以上': 'greater_than_or_equal',
        '以下': 'less_than_or_equal',
        '未満': 'less_than',
        '超える': 'greater_than',
        '等しい': 'equal'
    }
    
    # Verb patterns for identifying actions
    VERB_PATTERNS = {
        'movement': r'(移動|置く|動く|移る)',
        'add': r'(加える|足す|増やす)',
        'remove': r'(減らす|除く|捨てる)',
        'draw': r'(引く|ドロー)',
        'activate': r'(アクティブ|発動|起動)',
        'deactivate': r'(ウェイト|休止)',
        'reveal': r'(公開|見る|確認)',
        'gain': r'(得る|獲得)',
        'change': r'(変更|変える|変換)',
        'destroy': r'(破壊|除去)'
    }
    
    @classmethod
    def parse_zone_relationships(cls, template: str) -> Dict[str, Any]:
        """Parse zone relationships using Japanese particles (から, に, で, の, を)"""
        relationships = {
            'source_zones': [],
            'destination_zones': [],
            'location_zones': [],
            'possession_zones': [],
            'objects': []
        }
        
        # Find all zone placeholders
        zone_pattern = re.compile(r'\[zone\]|\[zone_condition\]')
        zones = list(zone_pattern.finditer(template))
        
        # Analyze context around each zone to determine relationship
        for i, zone_match in enumerate(zones):
            zone_text = zone_match.group()
            start_pos = zone_match.start()
            end_pos = zone_match.end()
            
            # Look ahead for particles
            context_after = template[end_pos:end_pos + 10]
            
            # Look behind for particles
            context_before = template[max(0, start_pos - 10):start_pos]
            
            # Determine relationship based on particles
            if 'から' in context_after[:5]:
                relationships['source_zones'].append(zone_text)
            elif 'に' in context_after[:5]:
                relationships['destination_zones'].append(zone_text)
            elif 'で' in context_after[:5]:
                relationships['location_zones'].append(zone_text)
            elif 'の' in context_after[:5]:
                relationships['possession_zones'].append(zone_text)
            elif 'を' in context_after[:5]:
                relationships['objects'].append(zone_text)
        
        return relationships
    
    @classmethod
    def extract_comparison_operators(cls, template: str) -> Dict[str, Any]:
        """Extract comparison operators and their targets"""
        comparisons = []
        
        for operator_jp, operator_en in cls.COMPARISON_OPERATORS.items():
            if operator_jp in template:
                # Find what's being compared
                operator_pos = template.find(operator_jp)
                
                # Look for the target before the operator
                target_pattern = re.compile(r'\[([^\]]+)\](.*?)' + re.escape(operator_jp))
                target_match = target_pattern.search(template)
                
                if target_match:
                    comparisons.append({
                        'operator': operator_en,
                        'operator_jp': operator_jp,
                        'target': target_match.group(1),
                        'full_match': target_match.group(0)
                    })
                else:
                    comparisons.append({
                        'operator': operator_en,
                        'operator_jp': operator_jp,
                        'target': 'unknown',
                        'full_match': operator_jp
                    })
        
        return {'comparisons': comparisons}
    
    @classmethod
    def identify_verb_type(cls, template: str) -> str:
        """Identify the type of verb/action in the template"""
        for verb_type, pattern in cls.VERB_PATTERNS.items():
            if re.search(pattern, template):
                return verb_type
        return 'unknown'
    
    @classmethod
    def parse_subject_object_verb(cls, template: str) -> Dict[str, Any]:
        """Parse subject-object-verb relationships in Japanese"""
        structure = {
            'subject': None,
            'objects': [],
            'verb': None,
            'verb_type': None,
            'modifiers': []
        }
        
        # Identify verb
        structure['verb_type'] = cls.identify_verb_type(template)
        
        # Find objects (marked by を)
        object_pattern = re.compile(r'\[([^\]]+)\](.*?)を')
        for obj_match in object_pattern.finditer(template):
            structure['objects'].append(obj_match.group(1))
        
        # Find subject (typically at start, marked by は or implicit)
        subject_pattern = re.compile(r'^\[([^\]]+)\](.*?)は')
        subject_match = subject_pattern.search(template)
        if subject_match:
            structure['subject'] = subject_match.group(1)
        else:
            # If no explicit subject, look for first noun phrase
            first_noun = re.search(r'\[([^\]]+)\]', template)
            if first_noun:
                structure['subject'] = first_noun.group(1)
        
        return structure
    
    @classmethod
    def parse_grammar_structure(cls, template: str) -> Dict[str, Any]:
        """Complete grammar structure analysis"""
        return {
            'zone_relationships': cls.parse_zone_relationships(template),
            'comparisons': cls.extract_comparison_operators(template),
            'subject_object_verb': cls.parse_subject_object_verb(template),
            'verb_type': cls.identify_verb_type(template)
        }


class PatternBasedSemanticExtractor:
    """Extract semantic structure from templates using pattern rules"""
    
    def __init__(self):
        # Load pattern rules
        rules_path = Path("data/semantic_pattern_rules.json")
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.rules = json.load(f)
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, Dict[str, re.Pattern]]:
        """Compile all regex patterns for efficiency"""
        compiled = {}
        
        # Compile core operation patterns
        compiled['core_operations'] = {}
        for op_name, op_data in self.rules['core_operation_patterns'].items():
            compiled['core_operations'][op_name] = [
                re.compile(pattern) for pattern in op_data['patterns']
            ]
        
        # Compile wrapper patterns
        compiled['wrappers'] = {}
        for wrapper_name, wrapper_data in self.rules['wrapper_patterns'].items():
            compiled['wrappers'][wrapper_name] = {}
            for pattern_name, pattern in wrapper_data['patterns'].items():
                compiled['wrappers'][wrapper_name][pattern_name] = re.compile(pattern)
        
        # Compile select-do patterns
        compiled['select_do'] = {}
        for pattern_name, pattern_data in self.rules['select_do_patterns'].items():
            compiled['select_do'][pattern_name] = [
                re.compile(pattern) for pattern in pattern_data['patterns']
            ]
        
        # Compile choice patterns
        compiled['choice'] = {}
        for pattern_name, pattern_data in self.rules['choice_patterns'].items():
            compiled['choice'][pattern_name] = [
                re.compile(pattern) for pattern in pattern_data['patterns']
            ]
        
        # Compile postcondition patterns
        compiled['postcondition'] = {}
        for pattern_name, pattern_data in self.rules['postcondition_patterns'].items():
            compiled['postcondition'][pattern_name] = [
                re.compile(pattern) for pattern in pattern_data['patterns']
            ]
        
        return compiled
    
    def extract_variables_from_template(self, template: str, pattern: re.Pattern) -> Dict[str, str]:
        """Extract variables from template using pattern matching"""
        match = pattern.search(template)
        if not match:
            return {}
        
        # Extract all placeholder variables from the template
        variables = {}
        placeholder_pattern = re.compile(r'\[([^\]]+)\]')
        
        for placeholder in placeholder_pattern.finditer(template):
            var_name = placeholder.group(1)
            if var_name not in variables:
                variables[var_name] = placeholder.group(0)
        
        return variables
    
    def match_core_operation(self, template: str) -> Tuple[str, Dict[str, str]]:
        """Match template against core operation patterns and classify specifically"""
        for op_name, patterns in self.compiled_patterns['core_operations'].items():
            for pattern in patterns:
                if pattern.search(template):
                    variables = self.extract_variables_from_template(template, pattern)
                    # Use specific operation taxonomy for classification
                    specific_operation = OperationTaxonomy.classify_operation(template, op_name)
                    return specific_operation, variables
        
        return "unknown", {}
    
    def extract_timing(self, full_text: str) -> Dict[str, Any]:
        """Extract timing from full text"""
        timing_patterns = self.compiled_patterns['wrappers']['timing']
        
        for timing_name, pattern in timing_patterns.items():
            if pattern.search(full_text):
                return {
                    "trigger_type": timing_name,
                    "source": "pattern_match"
                }
        
        return {"trigger_type": "manual", "source": "default"}
    
    def extract_cost(self, cost_template: str) -> Optional[Dict[str, Any]]:
        """Extract cost from cost template"""
        if not cost_template:
            return None
        
        cost_patterns = self.compiled_patterns['wrappers']['cost']
        cost_data = {"resources": {}, "actions": [], "optional": False}
        
        # Check for optional cost
        if cost_patterns['optional'].search(cost_template):
            cost_data["optional"] = True
        
        # Extract energy cost
        energy_match = cost_patterns['energy_cost'].search(cost_template)
        if energy_match:
            icon_count_match = re.search(r'\[icon_count:(\d+)\]', cost_template)
            if icon_count_match:
                cost_data["resources"]["energy"] = int(icon_count_match.group(1))
        
        # Extract action costs
        if cost_patterns['action_cost'].search(cost_template):
            cost_data["actions"].append("action_cost")
        
        if cost_data["resources"] or cost_data["actions"]:
            return cost_data
        
        return None
    
    def extract_duration(self, effect_template: str) -> Optional[Dict[str, Any]]:
        """Extract duration from effect template"""
        duration_patterns = self.compiled_patterns['wrappers']['duration']
        
        for duration_name, pattern in duration_patterns.items():
            if pattern.search(effect_template):
                return {"type": duration_name, "source": "pattern_match"}
        
        return None
    
    def extract_conditions(self, effect_template: str) -> List[Dict[str, Any]]:
        """Extract conditions from effect template"""
        condition_patterns = self.compiled_patterns['wrappers']['condition']
        conditions = []
        
        # Check for count conditions
        if condition_patterns['count_condition'].search(effect_template):
            count_match = re.search(r'\[(?:number|card|zone)\]を\[(?:number|zone)\]枚', effect_template)
            if count_match:
                conditions.append({
                    "operator": "count_in_zone",
                    "comparison": ">=",
                    "value": "[number]",
                    "source": "pattern_match"
                })
        
        # Check for presence conditions
        if condition_patterns['presence_condition'].search(effect_template):
            conditions.append({
                "operator": "presence",
                "comparison": ">=",
                "value": 1,
                "source": "pattern_match"
            })
        
        return conditions
    
    def extract_select_do(self, effect_template: str) -> Optional[Dict[str, Any]]:
        """Extract select-then-do structure from effect template"""
        select_do_patterns = self.compiled_patterns['select_do']
        
        for pattern_name, patterns in select_do_patterns.items():
            for pattern in patterns:
                if pattern.search(effect_template):
                    return {
                        "type": "select_then_do",
                        "select_action": "look/reveal",
                        "do_action": "move/add",
                        "source": "pattern_match"
                    }
        
        return None
    
    def extract_choice(self, effect_template: str) -> Optional[Dict[str, Any]]:
        """Extract choice structure from effect template"""
        choice_patterns = self.compiled_patterns['choice']
        
        for pattern_name, patterns in choice_patterns.items():
            for pattern in patterns:
                if pattern.search(effect_template):
                    count_match = re.search(r'\[number\]', effect_template)
                    return {
                        "type": "choice",
                        "choice_count": "[number]" if count_match else 1,
                        "source": "pattern_match"
                    }
        
        return None
    
    def extract_sequential_operations(self, effect_template: str) -> List[Dict[str, Any]]:
        """Extract sequential operations from effect template with specific classification and grammar analysis"""
        sequential_patterns = self.compiled_patterns['wrappers']['sequential_operations']
        operations = []
        
        # Split by multiple delimiters for sequential operations
        # Skip Japanese parentheses （ and ） to avoid fragment issues
        delimiters = ['、', '。', '：']
        parts = [effect_template]
        for delimiter in delimiters:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(delimiter))
            parts = new_parts
        
        # Filter out empty parts and parse each
        step = 0
        for part in parts:
            part = part.strip()
            if part:  # Skip empty parts
                # Skip invalid fragments
                if part in ['(', ')', 'その後', '。', '、']:
                    continue
                
                operation, variables = self.match_core_operation(part)
                
                # Add grammar structure analysis using JapaneseGrammarParser
                grammar_structure = JapaneseGrammarParser.parse_grammar_structure(part)
                
                # Use grammar analysis to improve classification (PRIORITIZE OVER PATTERN MATCHING)
                verb_type = grammar_structure.get('verb_type', 'unknown')
                zone_rel = grammar_structure.get('zone_relationships', {})
                
                # Override operation based on grammar analysis if it provides better classification
                if verb_type != 'unknown':
                    if verb_type == 'add' and zone_rel.get('source_zones') and zone_rel.get('destination_zones'):
                        operation = 'add_card_to_zone'
                    elif verb_type == 'add':
                        operation = 'gain_resource'
                    elif verb_type == 'movement' and zone_rel.get('source_zones') and zone_rel.get('destination_zones'):
                        operation = 'move_card'
                    elif verb_type == 'movement':
                        operation = 'reposition'
                    elif verb_type == 'draw':
                        operation = 'draw_card'
                    elif verb_type == 'activate':
                        operation = 'activate_card'
                    elif verb_type == 'deactivate':
                        operation = 'deactivate_card'
                    elif verb_type == 'destroy':
                        operation = 'destroy_card'
                    elif verb_type == 'gain':
                        operation = 'gain_effect'
                    elif verb_type == 'change':
                        operation = 'change_state'
                    else:
                        operation = verb_type + '_action'
                elif zone_rel.get('source_zones') and zone_rel.get('destination_zones'):
                    operation = 'move_between_zones'
                elif zone_rel.get('destination_zones'):
                    operation = 'move_to_zone'
                elif zone_rel.get('source_zones'):
                    operation = 'from_zone_source'
                
                # If still unknown, try to classify using OperationTaxonomy
                if operation == "unknown":
                    operation = OperationTaxonomy.classify_operation(part, operation)
                
                # If still unknown, try pattern-based classification
                if operation == "unknown":
                    # Check for resource selection patterns
                    if re.search(r'\[heart\]+\か', part):
                        operation = "resource_selection"
                        variables = self.extract_variables_from_template(part, re.compile(r'\[heart\]+\か'))
                    # Check for optional action patterns
                    elif 'してもよい' in part:
                        operation = "optional_action"
                        variables = self.extract_variables_from_template(part, re.compile(r'\[number\]'))
                    # Check for selection patterns
                    elif '選ぶ' in part:
                        operation = "select"
                        variables = self.extract_variables_from_template(part, re.compile(r'\[number\]'))
                    # Check for resource patterns
                    elif '[heart]' in part:
                        operation = "resource_cost"
                        variables = self.extract_variables_from_template(part, re.compile(r'\[heart\]'))
                    # Check for condition patterns
                    elif '場合' in part or 'とき' in part:
                        operation = OperationTaxonomy.classify_operation(part, "condition")
                        variables = self.extract_variables_from_template(part, re.compile(r'\[card\]|\[zone\]|\[player\]'))
                    # Check for transition patterns
                    elif 'その後' in part:
                        operation = "transition_clause"
                        variables = {}
                
                operations.append({
                    "step": step + 1,
                    "operation": operation,
                    "variables": variables,
                    "type": "sequential",
                    "text": part,
                    "grammar_analysis": grammar_structure
                })
                step += 1
        
        # Look for "その中から" (then from among) pattern - indicates select-then-do
        if sequential_patterns['then_clause'].search(effect_template):
            # Split by this pattern to get select and do parts
            parts = effect_template.split('その中から')
            if len(parts) == 2:
                select_part = parts[0]
                do_part = parts[1]
                select_op, select_vars = self.match_core_operation(select_part)
                do_op, do_vars = self.match_core_operation(do_part)
                operations.append({
                    "type": "select_then_do",
                    "select_operation": select_op,
                    "select_variables": select_vars,
                    "do_operation": do_op,
                    "do_variables": do_vars,
                    "pattern": "then_clause"
                })
        
        # Look for "残りを" (remainder) pattern
        if sequential_patterns['remainder_clause'].search(effect_template):
            parts = effect_template.split('残りを')
            if len(parts) == 2:
                main_part = parts[0]
                remainder_part = parts[1]
                remainder_op, remainder_vars = self.match_core_operation(remainder_part)
                operations.append({
                    "type": "handle_remainder",
                    "remainder_operation": remainder_op,
                    "remainder_variables": remainder_vars,
                    "pattern": "remainder_clause"
                })
        
        # Look for "そうした場合" (if so) pattern - indicates conditional success
        if sequential_patterns['success_clause'].search(effect_template):
            parts = effect_template.split('そうした場合')
            if len(parts) == 2:
                main_part = parts[0]
                followup_part = parts[1]
                followup_op, followup_vars = self.match_core_operation(followup_part)
                operations.append({
                    "type": "conditional_success",
                    "followup_operation": followup_op,
                    "followup_variables": followup_vars,
                    "pattern": "success_clause"
                })
        
        return operations if operations else None
    
    def extract_conditional_branching(self, effect_template: str) -> Optional[Dict[str, Any]]:
        """Extract conditional branching logic from effect template"""
        branching_patterns = self.compiled_patterns['wrappers']['conditional_branching']
        
        # Check for OR conditions
        if branching_patterns['or_conditions'].search(effect_template):
            # Count OR conditions
            or_count = effect_template.count('か')
            return {
                "type": "or_branching",
                "branches": or_count + 1,
                "source": "pattern_match"
            }
        
        return None
    
    def extract_choice_branching(self, effect_template: str) -> Optional[Dict[str, Any]]:
        """Extract choice branching logic from effect template"""
        branching_patterns = self.compiled_patterns['wrappers']['choice_branching']
        
        # Check for choice patterns
        if branching_patterns['select_from'].search(effect_template):
            return {
                "type": "select_from_options",
                "source": "pattern_match"
            }
        
        return None
    
    def extract_postcondition(self, effect_template: str) -> Optional[Dict[str, Any]]:
        """Extract postcondition from effect template"""
        postcondition_patterns = self.compiled_patterns['postcondition']
        
        for pattern_name, patterns in postcondition_patterns.items():
            for pattern in patterns:
                if pattern.search(effect_template):
                    return {
                        "type": pattern_name,
                        "source": "pattern_match"
                    }
        
        return None
    
    def extract_ability(self, ability: Dict[str, Any]) -> SemanticAbility:
        """Extract semantic structure from ability using pattern rules"""
        full_text = ability['full_text']
        combined_template = ability['combined_template']
        cost_template = ability.get('cost_template', '')
        effect_template = ability.get('effect_template', '')
        
        matched_patterns = []
        
        # Extract timing
        timing = self.extract_timing(full_text)
        matched_patterns.append(f"timing_{timing['trigger_type']}")
        
        # Extract cost
        cost = self.extract_cost(cost_template)
        if cost:
            matched_patterns.append("cost_extracted")
        
        # Extract core operation
        operation, variables = self.match_core_operation(effect_template)
        action = {
            "operation": operation,
            "variables": variables,
            "source": "pattern_match"
        }
        matched_patterns.append(f"operation_{operation}")
        
        # Extract duration
        duration = self.extract_duration(effect_template)
        if duration:
            matched_patterns.append(f"duration_{duration['type']}")
        
        # Extract conditions
        conditions = self.extract_conditions(effect_template)
        if conditions:
            matched_patterns.append("conditions_extracted")
        
        # Extract sequential operations
        sequential_operations = self.extract_sequential_operations(effect_template)
        if sequential_operations:
            matched_patterns.append("sequential_operations_extracted")
        
        # Extract conditional branching
        conditional_branching = self.extract_conditional_branching(effect_template)
        if conditional_branching:
            matched_patterns.append("conditional_branching_extracted")
        
        # Extract choice branching
        choice_branching = self.extract_choice_branching(effect_template)
        if choice_branching:
            matched_patterns.append("choice_branching_extracted")
        
        # Extract select-do
        select_do = self.extract_select_do(effect_template)
        if select_do:
            matched_patterns.append("select_do_extracted")
        
        # Extract choice
        choice = self.extract_choice(effect_template)
        if choice:
            matched_patterns.append("choice_extracted")
        
        # Extract postcondition
        postcondition = self.extract_postcondition(effect_template)
        if postcondition:
            matched_patterns.append("postcondition_extracted")
        
        # Build selector from variables
        selector = None
        if variables:
            selector = {
                "variables": variables,
                "source": "extracted_from_action"
            }
        
        return SemanticAbility(
            timing=timing,
            cost=cost,
            conditions=conditions,
            selector=selector,
            action=action,
            postcondition=postcondition,
            duration=duration,
            choice=choice,
            sequential_operations=sequential_operations,
            conditional_branching=conditional_branching,
            choice_branching=choice_branching,
            original_text=full_text,
            original_template=combined_template,
            matched_patterns=matched_patterns
        )
    
    def extract_all_abilities(self, abilities_file: Path) -> List[Dict[str, Any]]:
        """Extract all abilities from file using pattern rules"""
        with open(abilities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        unique_abilities = data['unique_abilities']
        extracted_abilities = []
        
        for ability in unique_abilities:
            semantic_ability = self.extract_ability(ability)
            extracted_abilities.append(asdict(semantic_ability))
        
        return extracted_abilities


def main():
    """Main function to extract abilities using pattern rules"""
    abilities_file = Path("data/abilities_extracted_from_cards.json")
    output_file = Path("data/pattern_based_semantic_abilities.json")
    
    extractor = PatternBasedSemanticExtractor()
    extracted_abilities = extractor.extract_all_abilities(abilities_file)
    
    output_data = {
        "schema": "pattern_based_semantic_ast.v1",
        "generated_at": "2026-04-16T02:58:00.000000",
        "source_file": str(abilities_file),
        "pattern_rules_file": "data/semantic_pattern_rules.json",
        "statistics": {
            "total_abilities": len(extracted_abilities),
        },
        "semantic_abilities": extracted_abilities
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"Extracted {len(extracted_abilities)} abilities using pattern-based semantic extraction")
    print(f"Output written to {output_file}")
    
    # Analyze pattern coverage
    pattern_coverage = {}
    for ability in extracted_abilities:
        for pattern in ability['matched_patterns']:
            pattern_coverage[pattern] = pattern_coverage.get(pattern, 0) + 1
    
    print(f"\nPattern Coverage:")
    for pattern, count in sorted(pattern_coverage.items(), key=lambda x: -x[1])[:10]:
        print(f"  {pattern}: {count} ({count/len(extracted_abilities)*100:.1f}%)")


if __name__ == "__main__":
    main()
