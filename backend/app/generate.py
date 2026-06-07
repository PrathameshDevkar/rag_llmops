import os
import tokenize
import io
# Define the folders you want to process
target_folders = ['backend/app/api', 'backend/app/core', 'backend/app/models', "backend/app/rag","backend/app/schemas","backend/app/services"]

def strip_comments(file_path):
    """Reads a python file and returns its content with comments removed."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            
        result = []
        g = tokenize.generate_tokens(io.StringIO(source).readline)
        
        for toknum, tokval, _, _, _ in g:
            # Skip comment tokens entirely
            if toknum == tokenize.COMMENT:
                continue
            result.append((toknum, tokval))
            
        # FIXED: Removed .decode('utf-8') since untokenize already returns a string here
        return tokenize.untokenize(result)
    except Exception as e:
        return f"[Error stripping comments from {os.path.basename(file_path)}: {e}]\n"

# Main processing loop
for folder in target_folders:
    if os.path.exists(folder) and os.path.isdir(folder):
        output_file = f"{folder}.txt"
        py_files = [f for f in os.listdir(folder) if f.endswith('.py')]
        
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for file_name in py_files:
                file_path = os.path.join(folder, file_name)
                
                # Write a clear header for each file
                outfile.write(f"{'='*40}\n")
                outfile.write(f" FILE: {file_name} (Comments Removed)\n")
                outfile.write(f"{'='*40}\n\n")
                
                # Get the cleaned code and write it
                cleaned_code = strip_comments(file_path)
                outfile.write(cleaned_code)
                
                # Add extra spacing between files
                outfile.write("\n\n")
                
        print(f"Created {output_file} (no comments) with {len(py_files)} files.")
    else:
        print(f"Directory '{folder}' not found, skipping.")