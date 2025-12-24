import convertapi
import requests
import os
import json
import traceback

# --- CONFIGURATION ---
# Replace with your actual API keys


# Set ConvertAPI credentials at module level (required for multiprocessing)
convertapi.api_credentials = CONVERT_API_SECRET

def image_to_ocr_string(image_path):
    """
    Takes an image, converts it to PDF, runs OCR, and returns the text string.
    """
    temp_pdf_path = None
    
    try:
        # --- STEP 1: Convert Image to PDF (ConvertAPI) ---
        print(f"1. Converting '{image_path}' to PDF...")
        
        try:
            # We save the PDF to the same folder as the image temporarily
            output_dir = os.path.dirname(image_path) or '.'
            
            result = convertapi.convert(
                'pdf',
                {'Files': [image_path]}, # Fixed syntax: keys must be strings
                from_format='images'
            )
            
            # Save the file and get the path
            saved_files = result.save_files(output_dir)
            
            # Check if we got a valid result
            if not saved_files or len(saved_files) == 0:
                return "Error: PDF conversion succeeded but no file was saved."
            
            temp_pdf_path = str(saved_files[0]) # Ensure it's a string
            print(f"   PDF created at: {temp_pdf_path}")
            
        except Exception as convert_error:
            print(f"   Full traceback:")
            traceback.print_exc()
            return f"Error during PDF conversion: {str(convert_error)}"

        # --- STEP 2: OCR the PDF (OCR.space) ---
        print("2. Sending PDF to OCR service...")
        
        # Settings optimized for PDF
        payload = {
            'apikey': OCR_SPACE_API_KEY,
            'language': 'eng',
            'isOverlayRequired': False,
            'scale': True,             
            'detectOrientation': True, 
            'OCREngine': 1             
        }

        with open(temp_pdf_path, 'rb') as f:
            r = requests.post(
                'https://api.ocr.space/parse/image',
                files={'file': f},
                data=payload
            )
        
        ocr_result = r.json()

        # --- STEP 3: Parse and Return String ---
        full_text = ""
        
        # Check if the API call itself worked
        if ocr_result.get('OCRExitCode') == 1:
            # Check if ParsedResults exists
            if 'ParsedResults' not in ocr_result or not ocr_result['ParsedResults']:
                return "Error: OCR succeeded but no parsed results returned."
            
            # Loop through all pages in the PDF result
            for page in ocr_result['ParsedResults']:
                if page.get('FileParseExitCode') == 1:
                    full_text += page.get('ParsedText', '') + "\n" # Append text
                else:
                    error_msg = page.get('ErrorMessage', 'Unknown error')
                    print(f"   Warning: Failed to parse a page. Error: {error_msg}")
            
            print("3. OCR Complete.")
            return full_text.strip() # Return the clean string
        
        else:
            error_msg = ocr_result.get('ErrorMessage', 'Unknown error')
            error_details = ocr_result.get('ErrorDetails', '')
            return f"Error: OCR failed. API Message: {error_msg}. Details: {error_details}"

    except Exception as e:
        return f"Critical Error: {str(e)}"

    finally:
        # --- STEP 4: Cleanup ---
        # Remove the temporary PDF file to keep the folder clean
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            print("   (Temporary PDF file deleted)")

# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    # Replace this with a real image file on your computer
    my_image = "/Users/asadirfan358/Documents/Learnly.AI-main/question-answer-background-design-can-260nw-2566897691.png" 
    
    # Run the tool
    extracted_text = image_to_ocr_string(my_image)
    
    # Print the final result string
    print("\n--- FINAL OUTPUT ---")
    print(extracted_text)