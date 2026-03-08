import re

with open("alphazero/training/overnight_vanilla.py", "r") as f:
    code = f.read()

# Remove map_engine_to_vanilla function entirely
code = re.sub(r'LOGIC_ID_MASK = 0x0FFF\s+def map_engine_to_vanilla.*?return -1', '', code, flags=re.DOTALL)

# In play_one_game, replace uses of map_engine_to_vanilla
# mapping_info
code = re.sub(r'mapping_info = \[\]\s+for aid in legal_ids\[:8\]:\s+vid = map_engine_to_vanilla\(state_json\[\'players\'\]\[state.current_player\], aid, initial_decks\[state.current_player\]\)\s+mapping_info\.append\(f"\{aid\}->\{vid\}"\)', 'mapping_info = []\n                for aid in legal_ids[:8]:\n                    mapping_info.append(str(aid))', code)

# policy_target updates
policy_target_update = """
            if total_visits > 0:
                for engine_id, q, visits in suggestions:
                    vid = engine_id
                    if 0 <= vid < ACTION_SPACE:
                        policy_target[vid] += visits / total_visits
                    else:
                        mapping_failures += 1
"""
code = re.sub(r'if total_visits > 0:\s+for engine_id, q, visits in suggestions:\s+vid = map_engine_to_vanilla.*?\s+if 0 <= vid < ACTION_SPACE:\s+policy_target\[vid\] \+= visits / total_visits\s+else:\s+mapping_failures \+= 1', policy_target_update.strip(), code, flags=re.DOTALL)

# mask updates
mask_update = """
            mask = np.zeros(ACTION_SPACE, dtype=np.bool_)
            v_to_e = {}
            for aid in legal_ids:
                vid = aid
                if 0 <= vid < ACTION_SPACE:
                    mask[vid] = True
                    v_to_e[vid] = aid
"""
code = re.sub(r'mask = np\.zeros\(ACTION_SPACE, dtype=np\.bool_\)\s+v_to_e = \{\}\s+for aid in legal_ids:\s+vid = map_engine_to_vanilla.*?\s+if 0 <= vid < ACTION_SPACE:\s+mask\[vid\] = True\s+v_to_e\[vid\] = aid', mask_update.strip(), code, flags=re.DOTALL)

# debug log loop
debug_log_loop = """
                    for aid in legal_ids[:20]:
                        vid = aid
                        label = state.get_verbose_label(aid)
                        f.write(f"  ID {aid} -> VID {vid}: {label}\\n")
                    if policy_target.sum() < 1e-11:
                        f.write(f"CRITICAL: Zero-sum policy! Total suggestions: {len(suggestions)}\\n")
                        for eid, q, v in suggestions:
                            vid = eid
                            f.write(f"  Suggestion: EID {eid} -> VID {vid} (Visits: {v})\\n")
"""
code = re.sub(r'for aid in legal_ids\[:20\]:\s+vid = map_engine_to_vanilla.*?\s+label = state\.get_verbose_label\(aid\)\s+f\.write\(f"  ID \{aid\} -> VID \{vid\}: \{label\}\\n"\)\s+if policy_target\.sum\(\) < 1e-11:\s+f\.write\(f"CRITICAL: Zero-sum policy! Total suggestions: \{len\(suggestions\)\}\\n"\)\s+for eid, q, v in suggestions:\s+vid = map_engine_to_vanilla.*?\s+f\.write\(f"  Suggestion: EID \{eid\} -> VID \{vid\} \(Visits: \{v\}\)\\n"\)', debug_log_loop.strip(), code, flags=re.DOTALL)


# model fallback sampling
fallback_1 = """
                    except Exception as e:
                        print(f"Sampling Error (Model): {e}. Fallback to random.")
                        action_engine = random.choice(legal_ids)
                        action_vid = action_engine
"""
code = re.sub(r'except Exception as e:\s+print\(f"Sampling Error \(Model\): \{e\}\. Fallback to random\."\)\s+action_engine = random\.choice\(legal_ids\)\s+action_vid = map_engine_to_vanilla.*?\)', fallback_1.strip(), code, flags=re.DOTALL)

fallback_2 = """
                    except Exception as e:
                        print(f"Sampling Error (MCTS): {e}. Fallback to random.")
                        action_engine = random.choice(legal_ids)
                        action_vid = action_engine
"""
code = re.sub(r'except Exception as e:\s+print\(f"Sampling Error \(MCTS\): \{e\}\. Fallback to random\."\)\s+action_engine = random\.choice\(legal_ids\)\s+action_vid = map_engine_to_vanilla.*?\)', fallback_2.strip(), code, flags=re.DOTALL)

fallback_3 = """
                else:
                    print(f"DEBUG: MCTS visits yielded zero-sum policy. total_visits={total_visits}, suggestions={len(suggestions)}")
                    action_engine = random.choice(legal_ids)
                    action_vid = action_engine
"""
code = re.sub(r'else:\s+print\(f"DEBUG: MCTS visits yielded zero-sum policy\. total_visits=\{total_visits\}, suggestions=\{len\(suggestions\)\}"\)\s+action_engine = random\.choice\(legal_ids\)\s+action_vid = map_engine_to_vanilla.*?\)', fallback_3.strip(), code, flags=re.DOTALL)

fallback_4 = """
            else:
                action_engine = random.choice(legal_ids)
                action_vid = action_engine
"""
code = re.sub(r'else:\s+action_engine = random\.choice\(legal_ids\)\s+action_vid = map_engine_to_vanilla.*?\)', fallback_4.strip(), code, flags=re.DOTALL)

with open("alphazero/training/overnight_vanilla.py", "w") as f:
    f.write(code)
