import zipfile
import os
from datetime import datetime

def backup_engine_source():
    source_dir = 'engine_rust_src'
    # Use timestamp for the backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'engine_source_backup_{timestamp}.zip'
    
    # Directories to exclude to keep the backup small and focused on source
    exclude_dirs = {'.venv', 'target', '__pycache__', '.git'}

    print(f"Starting backup of {source_dir}...")
    count = 0
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Prune directories in-place to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # Also exclude any potential giant log files if they still exist
                if file.endswith('.log') or file.endswith('.txt') and os.path.getsize(os.path.join(root, file)) > 1024*1024:
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
                zipf.write(file_path, arcname)
                count += 1
    
    size_mb = os.path.getsize(output_filename) / (1024 * 1024)
    print(f"Successfully backed up {count} files.")
    print(f"Backup saved to: {output_filename}")
    print(f"Total backup size: {size_mb:.2f} MB")
    return output_filename

if __name__ == '__main__':
    backup_engine_source()
