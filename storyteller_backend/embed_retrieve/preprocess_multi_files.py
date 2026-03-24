"""
Multi-File Preprocessing Tool

This tool detects folders in raw_texts/ that contain multiple files and concatenates
them into single files that can be processed by the existing ingestion pipeline.
"""

import os
import glob
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple


def detect_multi_file_folders(raw_texts_dir: str = "raw_texts") -> List[str]:
    """
    Detect folders in raw_texts/ that contain multiple files.
    
    Args:
        raw_texts_dir: Path to the raw_texts directory
        
    Returns:
        List of folder names that contain multiple files
    """
    multi_file_folders = []
    
    if not os.path.exists(raw_texts_dir):
        return multi_file_folders
    
    # Check each subdirectory in raw_texts
    for item in os.listdir(raw_texts_dir):
        item_path = os.path.join(raw_texts_dir, item)
        
        if os.path.isdir(item_path):
            # Count files in this directory
            txt_files = glob.glob(os.path.join(item_path, "*.txt"))
            pdf_files = glob.glob(os.path.join(item_path, "*.pdf"))
            total_files = len(txt_files) + len(pdf_files)
            
            if total_files > 1:
                multi_file_folders.append(item)
                print(f"Found multi-file folder: {item} ({total_files} files)")
    
    return multi_file_folders


def concatenate_files(folder_path: str, output_file: str, file_type: str) -> bool:
    """
    Concatenate all files in a folder into a single output file.
    
    Args:
        folder_path: Path to the folder containing files
        output_file: Path to the output concatenated file
        file_type: "text" or "pdf"
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get all files of the specified type
        if file_type.lower() == "pdf":
            file_pattern = os.path.join(folder_path, "*.pdf")
        else:
            file_pattern = os.path.join(folder_path, "*.txt")
        
        files = sorted(glob.glob(file_pattern))
        
        if not files:
            print(f"No {file_type} files found in {folder_path}")
            return False
        
        print(f"Concatenating {len(files)} files from {folder_path}...")
        
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for file_path in files:
                print(f"  Processing: {os.path.basename(file_path)}")
                
                if file_type.lower() == "pdf":
                    # Extract text from PDF
                    with fitz.open(file_path) as doc:
                        for page in doc:
                            text = page.get_text()
                            outfile.write(text)
                        outfile.write("\n\n")  # Add separator between files
                        
                else:
                    # Read text file
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(content)
                        outfile.write("\n\n")  # Add separator between files
        
        print(f"Successfully created: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error concatenating files in {folder_path}: {e}")
        return False


def determine_file_type(folder_path: str) -> str:
    """
    Determine the file type based on files in the folder.
    
    Args:
        folder_path: Path to the folder
        
    Returns:
        "text" or "pdf"
    """
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    
    if len(txt_files) > len(pdf_files):
        return "text"
    elif len(pdf_files) > len(txt_files):
        return "pdf"
    else:
        # If equal, prefer text files
        return "text" if txt_files else "pdf"


def preprocess_all_multi_files(raw_texts_dir: str = "raw_texts") -> List[Tuple[str, str, str]]:
    """
    Preprocess all multi-file folders in raw_texts/.
    
    Args:
        raw_texts_dir: Path to the raw_texts directory
        
    Returns:
        List of tuples: (folder_name, output_file_path, file_type)
    """
    multi_file_folders = detect_multi_file_folders(raw_texts_dir)
    processed_folders = []
    
    for folder_name in multi_file_folders:
        folder_path = os.path.join(raw_texts_dir, folder_name)
        file_type = determine_file_type(folder_path)
        
        # Create output filename
        if file_type == "pdf":
            output_file = os.path.join(raw_texts_dir, f"{folder_name}_concatenated.pdf")
        else:
            output_file = os.path.join(raw_texts_dir, f"{folder_name}_concatenated.txt")
        
        # Concatenate files
        if concatenate_files(folder_path, output_file, file_type):
            processed_folders.append((folder_name, output_file, file_type))
    
    return processed_folders


def main():
    """Main function for the preprocessing tool."""
    print("🔍 Multi-File Preprocessing Tool")
    print("=" * 50)
    
    # Detect multi-file folders
    multi_file_folders = detect_multi_file_folders()
    
    if not multi_file_folders:
        print("No multi-file folders found in raw_texts/")
        return
    
    print(f"\nFound {len(multi_file_folders)} multi-file folder(s)")
    
    # Process each folder
    processed = preprocess_all_multi_files()
    
    print(f"\n✅ Successfully processed {len(processed)} folder(s):")
    for folder_name, output_file, file_type in processed:
        print(f"  - {folder_name} → {os.path.basename(output_file)} ({file_type})")
    
    print(f"\n📝 Next steps:")
    print(f"  1. Add the concatenated files to your jobs.yaml")
    print(f"  2. Run the ingestion process")
    print(f"  3. Optionally delete the original multi-file folders")


if __name__ == '__main__':
    main() 