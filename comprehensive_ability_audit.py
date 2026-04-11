#!/usr/bin/env python3
"""
Comprehensive Ability Frame Audit Tool
Analyzes every ability in ability_frame_source.json and identifies mismatches
between ability text and frame implementation.
"""

import json
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class AuditIssue:
    ability_index: int
    card_no: str
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    issue_type: str
    text: str
    current_frames: List[str]
    expected_behavior: str
    recommendation: str

class AbilityAuditor:
    def __init__(self, json_path: str):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.abilities = self.data.get('abilities', [])
        self.issues: List[AuditIssue] = []
        self.frame_stats: Dict[str, int] = {}
        
    def audit_all(self) -> List[AuditIssue]:
        """Run comprehensive audit on all abilities"""
        for idx, ability in enumerate(self.abilities):
            self._audit_ability(idx, ability)
        return self.issues
    
    def _audit_ability(self, idx: int, ability: Dict):
        """Audit a single ability"""
        text = ability.get('primary_text_jp', '')
        frames = ability.get('frames', [])
        card_refs = ability.get('card_refs', [])
        
        if not text or not frames:
            return
        
        card_no = card_refs[0].get('card_no', 'UNKNOWN') if card_refs else 'UNKNOWN'
        frame_ops = [f.get('op', 'UNKNOWN') for f in frames]
        
        # Update frame statistics
        for op in frame_ops:
            self.frame_stats[op] = self.frame_stats.get(op, 0) + 1
        
        # Pattern 1: RECOVER_LIVE from wrong zone
        if 'RECOVER_LIVE' in frame_ops:
            self._check_recover_live_zone(idx, card_no, text, frames)
        
        # Pattern 2: SELECT_MODE missing option_names for flavor choices
        if 'SELECT_MODE' in frame_ops:
            self._check_select_mode_options(idx, card_no, text, ability)
        
        # Pattern 3: TRANSFORM_HEART missing color specification
        if 'TRANSFORM_HEART' in frame_ops:
            self._check_transform_heart(idx, card_no, text, frames)
        
        # Pattern 4: Wrong frames for success pile count abilities
        if any(kw in text for kw in ['成功ライブ', 'ブレード']):
            self._check_success_pile_blades(idx, card_no, text, frames)
        
        # Pattern 5: Flavor choice abilities (like the LL-PR-004-PR card)
        if any(kw in text for kw in ['チョコミント', 'ストロベリー', 'フレイバー', '好き？']):
            self._check_flavor_choice(idx, card_no, text, frames, ability)
        
        # Pattern 6: Missing conditional frames
        if any(kw in text for kw in ['場合', 'いる場合', 'ある場合']) and 'JUMP_IF_FALSE' not in frame_ops:
            self.issues.append(AuditIssue(
                ability_index=idx,
                card_no=card_no,
                severity='WARNING',
                issue_type='MISSING_CONDITIONAL_JUMP',
                text=text[:100],
                current_frames=frame_ops,
                expected_behavior='Ability has conditional text but no JUMP_IF_FALSE frame',
                recommendation='Add JUMP_IF_FALSE frame after condition check'
            ))
        
        # Pattern 7: "エールにより公開された" should use LOOK_AND_CHOOSE not RECOVER_LIVE
        if 'エールにより公開された' in text and 'RECOVER_LIVE' in frame_ops:
            self.issues.append(AuditIssue(
                ability_index=idx,
                card_no=card_no,
                severity='CRITICAL',
                issue_type='WRONG_ZONE_FOR_YELL',
                text=text[:100],
                current_frames=frame_ops,
                expected_behavior='Should recover from Yell zone, but RECOVER_LIVE hardcodes Discard',
                recommendation='Replace RECOVER_LIVE with LOOK_AND_CHOOSE, source_zone=YELL'
            ))
    
    def _check_recover_live_zone(self, idx: int, card_no: str, text: str, frames: List[Dict]):
        """Check if RECOVER_LIVE is using wrong source zone"""
        for i, frame in enumerate(frames):
            if frame.get('op') == 'RECOVER_LIVE':
                slot = frame.get('slot', {})
                source_zone = slot.get('source_zone', 'DISCARD')
                
                # If text mentions yell/エール but frame doesn't specify YELL zone
                if 'エール' in text and source_zone != 'YELL':
                    self.issues.append(AuditIssue(
                        ability_index=idx,
                        card_no=card_no,
                        severity='CRITICAL',
                        issue_type='RECOVER_LIVE_WRONG_ZONE',
                        text=text[:100],
                        current_frames=[f.get('op', '') for f in frames],
                        expected_behavior=f'Recover from Yell zone, but RECOVER_LIVE uses {source_zone}',
                        recommendation='Change to LOOK_AND_CHOOSE with source_zone=YELL'
                    ))
    
    def _check_select_mode_options(self, idx: int, card_no: str, text: str, ability: Dict):
        """Check if SELECT_MODE abilities have proper option_names"""
        option_names = ability.get('option_names', [])
        
        if not option_names:
            # Check if this is a flavor choice ability
            if any(kw in text for kw in ['チョコミント', 'ストロベリー', 'クッキー', 'フレイバー']):
                self.issues.append(AuditIssue(
                    ability_index=idx,
                    card_no=card_no,
                    severity='WARNING',
                    issue_type='MISSING_FLAVOR_OPTIONS',
                    text=text[:150],
                    current_frames=[f.get('op', '') for f in ability.get('frames', [])],
                    expected_behavior='Flavor choice ability should have option_names with flavor names',
                    recommendation='Add option_names: ["チョコミント", "ストロベリーフレイバー", "クッキー＆クリーム", "あなた"]'
                ))
            else:
                self.issues.append(AuditIssue(
                    ability_index=idx,
                    card_no=card_no,
                    severity='INFO',
                    issue_type='MISSING_OPTION_NAMES',
                    text=text[:100],
                    current_frames=[f.get('op', '') for f in ability.get('frames', [])],
                    expected_behavior='SELECT_MODE should have descriptive option_names',
                    recommendation='Add option_names array describing each choice'
                ))
    
    def _check_transform_heart(self, idx: int, card_no: str, text: str, frames: List[Dict]):
        """Check TRANSFORM_HEART has proper color specification"""
        for frame in frames:
            if frame.get('op') == 'TRANSFORM_HEART':
                value = frame.get('value', 0)
                attr = frame.get('attr', {})
                color_mask = attr.get('color_mask', 0)
                
                # If color_mask is 0 or missing, transformation won't work properly
                if color_mask == 0:
                    self.issues.append(AuditIssue(
                        ability_index=idx,
                        card_no=card_no,
                        severity='CRITICAL',
                        issue_type='TRANSFORM_HEART_MISSING_COLOR',
                        text=text[:100],
                        current_frames=[f.get('op', '') for f in frames],
                        expected_behavior='TRANSFORM_HEART needs color_mask to specify destination color',
                        recommendation=f'Add attr.color_mask (1=pink, 8=green, etc.)'
                    ))
    
    def _check_success_pile_blades(self, idx: int, card_no: str, text: str, frames: List[Dict]):
        """Check success pile count -> blade abilities"""
        frame_ops = [f.get('op', '') for f in frames]
        
        # Check if text mentions success pile and blades but frames are wrong
        if '成功ライブ' in text and 'ブレード' in text:
            if 'COUNT_SUCCESS' not in frame_ops and 'BATON' in frame_ops:
                self.issues.append(AuditIssue(
                    ability_index=idx,
                    card_no=card_no,
                    severity='CRITICAL',
                    issue_type='WRONG_FRAMES_FOR_SUCCESS_BLADES',
                    text=text[:150],
                    current_frames=frame_ops,
                    expected_behavior='Should check success pile count then add blades',
                    recommendation='Replace BATON/COUNT_ENERGY/ENERGY_CHARGE with COUNT_SUCCESS/ADD_BLADES'
                ))
    
    def _check_flavor_choice(self, idx: int, card_no: str, text: str, frames: List[Dict], ability: Dict):
        """Check flavor choice abilities have proper structure"""
        frame_ops = [f.get('op', '') for f in frames]
        
        # Check for proper option names
        option_names = ability.get('option_names', [])
        expected_options = ['チョコミント', 'ストロベリーフレイバー', 'クッキー＆クリーム', 'あなた']
        
        if not option_names or len(option_names) < 3:
            self.issues.append(AuditIssue(
                ability_index=idx,
                card_no=card_no,
                severity='WARNING',
                issue_type='INCOMPLETE_FLAVOR_OPTIONS',
                text=text[:200],
                current_frames=frame_ops,
                expected_behavior=f'Should have 4 flavor options: {expected_options}',
                recommendation=f'Add option_names: {expected_options}'
            ))
        
        # Check frame flow - should have proper branching for each option
        if 'SELECT_MODE' in frame_ops:
            # Check if there are enough JUMP frames for the branches
            jump_count = frame_ops.count('JUMP')
            if jump_count < 3:  # Need jumps for 4-option branching
                self.issues.append(AuditIssue(
                    ability_index=idx,
                    card_no=card_no,
                    severity='CRITICAL',
                    issue_type='INSUFFICIENT_BRANCHING',
                    text=text[:150],
                    current_frames=frame_ops,
                    expected_behavior='4-option choice needs proper branching structure',
                    recommendation='Add proper JUMP frames for each flavor option branch'
                ))
    
    def generate_report(self, output_path: str):
        """Generate detailed audit report"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Ability Frame Audit Report\n\n")
            f.write(f"Total abilities analyzed: {len(self.abilities)}\n")
            f.write(f"Total issues found: {len(self.issues)}\n\n")
            
            # Summary by severity
            critical = [i for i in self.issues if i.severity == 'CRITICAL']
            warnings = [i for i in self.issues if i.severity == 'WARNING']
            info = [i for i in self.issues if i.severity == 'INFO']
            
            f.write(f"## Summary by Severity\n\n")
            f.write(f"- **CRITICAL**: {len(critical)} issues\n")
            f.write(f"- **WARNING**: {len(warnings)} issues\n")
            f.write(f"- **INFO**: {len(info)} issues\n\n")
            
            # Summary by issue type
            f.write("## Issues by Type\n\n")
            issue_types = {}
            for issue in self.issues:
                issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
            
            for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
                f.write(f"- {issue_type}: {count}\n")
            
            f.write("\n## Detailed Issues\n\n")
            
            # Critical issues first
            if critical:
                f.write("### CRITICAL Issues (Must Fix)\n\n")
                for issue in critical:
                    self._write_issue_detail(f, issue)
            
            if warnings:
                f.write("### WARNING Issues (Should Fix)\n\n")
                for issue in warnings:
                    self._write_issue_detail(f, issue)
            
            if info:
                f.write("### INFO (Suggestions)\n\n")
                for issue in info:
                    self._write_issue_detail(f, issue)
            
            # Frame usage statistics
            f.write("\n## Frame Usage Statistics\n\n")
            f.write("| Frame | Count |\n")
            f.write("|-------|-------|\n")
            for frame, count in sorted(self.frame_stats.items(), key=lambda x: -x[1]):
                f.write(f"| {frame} | {count} |\n")
        
        print(f"Audit report written to: {output_path}")
    
    def _write_issue_detail(self, f, issue: AuditIssue):
        """Write detailed issue information"""
        f.write(f"#### Ability #{issue.ability_index} - {issue.card_no}\n\n")
        f.write(f"**Issue Type:** {issue.issue_type}\n\n")
        f.write(f"**Text:** {issue.text}\n\n")
        f.write(f"**Current Frames:** {', '.join(issue.current_frames)}\n\n")
        f.write(f"**Expected:** {issue.expected_behavior}\n\n")
        f.write(f"**Recommendation:** {issue.recommendation}\n\n")
        f.write("---\n\n")
    
    def apply_fixes(self):
        """Apply automatic fixes for identified issues"""
        fixes_applied = 0
        
        for issue in self.issues:
            if issue.severity == 'CRITICAL':
                ability = self.abilities[issue.ability_index]
                
                if issue.issue_type == 'RECOVER_LIVE_WRONG_ZONE':
                    self._fix_recover_live_to_look_and_choose(ability)
                    fixes_applied += 1
                
                elif issue.issue_type == 'TRANSFORM_HEART_MISSING_COLOR':
                    self._fix_transform_heart_color(ability)
                    fixes_applied += 1
                
                elif issue.issue_type == 'WRONG_FRAMES_FOR_SUCCESS_BLADES':
                    self._fix_success_blades_frames(ability)
                    fixes_applied += 1
        
        return fixes_applied
    
    def _fix_recover_live_to_look_and_choose(self, ability: Dict):
        """Fix RECOVER_LIVE from wrong zone to LOOK_AND_CHOOSE"""
        frames = ability.get('frames', [])
        for i, frame in enumerate(frames):
            if frame.get('op') == 'RECOVER_LIVE':
                # Replace with LOOK_AND_CHOOSE
                frames[i] = {
                    "op": "LOOK_AND_CHOOSE",
                    "frame_index": frame.get('frame_index', i),
                    "value": 1,
                    "attr": {
                        "is_optional": 1,
                        "card_type": "LIVE"
                    },
                    "slot": {
                        "target_slot": "HAND",
                        "source_zone": "YELL"
                    }
                }
    
    def _fix_transform_heart_color(self, ability: Dict):
        """Fix TRANSFORM_HEART missing color specification"""
        text = ability.get('primary_text_jp', '')
        frames = ability.get('frames', [])
        
        for frame in frames:
            if frame.get('op') == 'TRANSFORM_HEART':
                # Determine color from text
                if '緑' in text or 'グリーン' in text or 'heart04' in text:
                    color_mask = 8  # Green
                elif 'ピンク' in text or 'heart01' in text:
                    color_mask = 1  # Pink
                else:
                    color_mask = 8  # Default to green if unclear
                
                if 'attr' not in frame:
                    frame['attr'] = {}
                frame['attr']['color_mask'] = color_mask
                
                # Also ensure value is set for source (7 = ALL)
                if frame.get('value', 0) == 0:
                    frame['value'] = 7
    
    def _fix_success_blades_frames(self, ability: Dict):
        """Fix wrong frames for success pile -> blades abilities"""
        text = ability.get('primary_text_jp', '')
        
        # Extract the threshold value from text (usually 3)
        threshold = 3
        match = re.search(r'(\d+)枚以上', text)
        if match:
            threshold = int(match.group(1))
        
        # Replace frames
        ability['frames'] = [
            {
                "op": "COUNT_SUCCESS",
                "frame_index": 0,
                "value": threshold,
                "attr": {
                    "target_player": "BOTH",
                    "is_ge": 1
                },
                "slot": {
                    "target_slot": "CONTEXT"
                }
            },
            {
                "op": "JUMP_IF_FALSE",
                "frame_index": 1,
                "value": 2
            },
            {
                "op": "ADD_BLADES",
                "frame_index": 2,
                "value": 3,
                "slot": {
                    "target_slot": "CONTEXT"
                }
            },
            {
                "op": "RETURN",
                "frame_index": 3
            }
        ]
    
    def save_fixed_json(self, output_path: str):
        """Save the fixed JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Fixed JSON saved to: {output_path}")


def main():
    json_path = 'C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json'
    report_path = 'C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/ability_audit_report.md'
    
    print("Starting comprehensive ability audit...")
    auditor = AbilityAuditor(json_path)
    
    # Run audit
    issues = auditor.audit_all()
    print(f"Found {len(issues)} issues")
    
    # Generate report
    auditor.generate_report(report_path)
    
    # Apply critical fixes
    print("\nApplying automatic fixes for CRITICAL issues...")
    fixes = auditor.apply_fixes()
    print(f"Applied {fixes} fixes")
    
    # Save fixed JSON
    auditor.save_fixed_json(json_path)
    
    print("\nAudit complete!")
    print(f"Report: {report_path}")
    print(f"Fixed JSON: {json_path}")


if __name__ == '__main__':
    main()
