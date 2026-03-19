import os
import sys

def is_binary(file_path):
    """Check if a file is binary."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
            return False
    except Exception:
        return True

def check_mojibake(file_path):
    """
    Check for potential mojibake in a file.
    Common mojibake patterns for UTF-8 misdecoded as Latin-1:
    - ã (0xC3) followed by another byte (often seen in Japanese UTF-8)
    - å (0xC2)
    """
    issues = []
    try:
        # Check if it's even valid UTF-8
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for common Latin-1 misdecodings of Japanese UTF-8
                # UTF-8 for common JP characters starts with 0xE3, 0xE4, 0xE5, etc.
                # In Latin-1, these are ã, ä, å, etc.
                # If we see a lot of these characters followed by other Latin-1 chars, it's likely mojibake.
                
                # A simple heuristic: if we see 'ã' character (U+00E3) followed by another
                # character that is NOT a space/common ASCII, it might be mojibake.
                # Actually, in a valid UTF-8 file, U+00E3 IS the character 'ã'.
                # Mojibake happens when the file WAS UTF-8 but someone converted it 
                # incorrectly or is viewing it wrong.
                
                # More specifically: If we see characters like char(195) (ã) in a file
                # that shouldn't have them, it might be a problem.
                
                sus_chars = ['ã', 'å', 'æ', 'ç', 'è', 'é', 'ê', 'ë']
                found_sus = [c for c in sus_chars if c in content]
                
                if found_sus:
                    # Check density or context. 
                    # For example, ã followed by something in the range 0x80-0xBF is a classic UTF-8 sequence.
                    # But if we are reading it as UTF-8, it should have been decoded to the proper JP char.
                    # If we SEE the literal 'ã' in a UTF-8 read, it means the file literally contains C3 A3.
                    # Which might be "ã" in UTF-8, or it might be a double-encoded UTF-8.
                    pass

        except UnicodeDecodeError:
            issues.append("ERROR: Not valid UTF-8")
            
        # Try reading as Shift-JIS to see if it makes more sense?
        try:
            with open(file_path, 'r', encoding='shift-jis') as f:
                f.read()
                # If it's valid SJIS but NOT valid UTF-8, it's a candidate for "oops wrong encoding"
                if "ERROR: Not valid UTF-8" in issues:
                    issues.append("INFO: Valid Shift-JIS")
        except Exception:
            pass

    except Exception as e:
        issues.append(f"EXCEPTION: {str(e)}")
    
    return issues

def main():
    root_dir = "."
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    
    exclude_dirs = {'.git', '.venv', '.uv-cache', '__pycache__', 'node_modules', '.kilocode', '.agent'}
    exclude_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.gz', '.tar', '.exe', '.bin', '.dll', '.so', '.pyc', '.mo', '.po'}

    print(f"Scanning directory: {os.path.abspath(root_dir)}")
    print("-" * 60)
    
    found_any = False
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in exclude_extensions:
                continue
                
            file_path = os.path.join(root, file)
            
            if "scan_mojibake.py" in file_path:
                continue
                
            if is_binary(file_path):
                continue
                
            # Heuristic: Check for non-UTF8 or potential mis-encoding
            # Also check for byte signature of mojibake
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                    
                # Check for UTF-8 misinterpreted as Latin-1 and then re-saved as UTF-8
                # (Double encoding)
                # UTF-8 for 'あ' is E3 81 82
                # Misinterpreted as Latin-1: ã\x81\x82
                # Re-saved as UTF-8: C3 A3 C2 81 C2 82
                
                mojibake_signature = False
                if b'\xc3\xa3' in data or b'\xc3\xa2' in data:
                    mojibake_signature = True
                
                utf8_err = False
                try:
                    data.decode('utf-8')
                except UnicodeDecodeError:
                    utf8_err = True
                
                if utf8_err or mojibake_signature:
                    found_any = True
                    status = []
                    if utf8_err: status.append("Invalid UTF-8")
                    if mojibake_signature: status.append("Double-encoded Mojibake pattern found")
                    
                    # Try SJIS
                    try:
                        data.decode('shift-jis')
                        status.append("Valid Shift-JIS")
                    except:
                        pass
                        
                    print(f"{file_path}: {', '.join(status)}")
                    
            except Exception as e:
                # print(f"Could not scan {file_path}: {e}")
                pass

    if not found_any:
        print("No obvious mojibake or encoding issues found.")

if __name__ == "__main__":
    main()
