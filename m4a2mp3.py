from pydub import AudioSegment
import os

def convert_m4a_to_mp3(input_path, output_path):
    """
    Convert an M4A file to MP3 format.
    
    Args:
        input_path (str): Path to the input M4A file
        output_path (str): Path where the output MP3 file will be saved
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file {input_path} does not exist")
        
        # Check if input file is M4A
        if not input_path.lower().endswith('.m4a'):
            raise ValueError("Input file must be in M4A format")
        
        # Load M4A file
        audio = AudioSegment.from_file(input_path, format="m4a")
        
        # Ensure output path ends with .mp3
        if not output_path.lower().endswith('.mp3'):
            output_path += '.mp3'
        
        # Export as MP3
        audio.export(output_path, format="mp3")
        print(f"Successfully converted {input_path} to {output_path}")
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

def batch_convert_m4a_to_mp3(input_folder, output_folder):
    """
    Convert all M4A files in a folder to MP3 format.
    
    Args:
        input_folder (str): Folder containing M4A files
        output_folder (str): Folder where MP3 files will be saved
    """
    try:
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Process each file in the input folder
        for filename in os.listdir(input_folder):
            if filename.lower().endswith('.m4a'):
                input_path = os.path.join(input_folder, filename)
                output_filename = os.path.splitext(filename)[0] + '.mp3'
                output_path = os.path.join(output_folder, output_filename)
                convert_m4a_to_mp3(input_path, output_path)
                
    except Exception as e:
        print(f"Error during batch conversion: {str(e)}")

if __name__ == "__main__":
    # Example usage
    # Single file conversion
    convert_m4a_to_mp3("/Users/mhuo/Downloads/input.m4a", "/Users/mhuo/Downloads/output.mp3")
    
    # Batch conversion
#    batch_convert_m4a_to_mp3("input_folder", "output_folder")
