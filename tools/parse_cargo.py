import json
import sys

def parse_cargo_json(input_file, output_file):
    lines = []
    try:
        with open(input_file, 'r', encoding='utf-16') as f:
            lines = f.readlines()
            print(f"Read {len(lines)} lines using utf-16")
    except Exception as e:
        print(f"Failed to read utf-16: {e}")
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"Read {len(lines)} lines using utf-8")
        except Exception as e2:
            print(f"Failed to read utf-8: {e2}")
            return
            
    with open(output_file, 'w', encoding='utf-8') as out_f:
        error_count = 0
        for line in lines:
            if not line.strip(): continue
            try:
                msg = json.loads(line)
                reason = msg.get('reason')
                if reason == 'compiler-message':
                    message = msg.get('message', {})
                    if message.get('level') == 'error':
                        error_count += 1
                        out_f.write('-' * 40 + '\n')
                        spans = message.get('spans', [])
                        if spans:
                            span = spans[0]
                            out_f.write(f"{span['file_name']}:{span['line_start']}\n")
                        out_f.write(message.get('message', 'No message') + '\n')
                elif reason == 'test':
                    event = msg.get('event')
                    if event == 'failed':
                        error_count += 1
                        out_f.write('-' * 40 + '\n')
                        out_f.write(f"TEST FAILED: {msg.get('name')}\n")
                        stdout = msg.get('stdout')
                        if stdout:
                            out_f.write(f"STDOUT:\n{stdout}\n")
                elif reason == 'build-finished':
                    if not msg.get('success'):
                        out_f.write('Build failed. Check compiler messages.\n')
            except Exception as e:
                pass
        print(f"Found {error_count} errors/failures.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python parse_cargo.py <input> <output>")
    else:
        parse_cargo_json(sys.argv[1], sys.argv[2])
