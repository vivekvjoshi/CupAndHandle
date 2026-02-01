import google.generativeai as genai
import os
import time

def analyze_chart(image_path, api_key):
    """
    Uses Google Gemini Flash to analyze the chart image.
    Returns: (score, reasoning)
    """
    if not api_key:
        return 0, "No API Key provided."
        
    try:
        genai.configure(api_key=api_key)
        
        # logical model choice: gemini-1.5-flash is fast and free-tier eligible
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare image
        # Uploading file or passing bytes? 
        # For simple usage with genai, we can pass the PIL image or path if supported, 
        # or upload if using the File API. 
        # Let's use the simpler standardized approach with PIL if possible, or read bytes.
        
        # Actually, genai.upload_file is robust.
        sample_file = genai.upload_file(path=image_path, display_name="Stock Chart")
        
        # Prompt
        prompt = """
        You are a professional technical analyst. Look at this stock chart.
        I am looking for a 'Cup and Handle' pattern where the handle is currently forming (bull flag).
        
        1. Is this a valid Cup and Handle formation?
        2. Is the handle forming constructively (drifting down/stabilizing) or is it broken?
        3. Rate your confidence from 0 to 10 that this is a high-quality setup ready for a breakout.
        
        Return your answer in this format:
        Score: [0-10]
        Reasoning: [One sentence explanation]
        """
        
        response = model.generate_content([sample_file, prompt])
        
        # Cleanup
        # genai.delete_file(sample_file.name) # Optional execution cleanup
        
        return response.text
        
    except Exception as e:
        return f"AI Error: {str(e)}"
