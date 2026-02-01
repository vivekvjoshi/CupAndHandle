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
        
        # List of models to try in order of preference
        # 1.5 Flash (Fast/Cheap), 1.5 Pro (Best), Pro Vision (Legacy)
        models_to_try = [
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro',
            'gemini-pro',
            'gemini-1.0-pro-vision-latest',
            'gemini-pro-vision'
        ]
        
        last_error = ""
        
        for model_name in models_to_try:
            try:
                # Prepare image
                sample_file = genai.upload_file(path=image_path, display_name="Stock Chart")
                
                model = genai.GenerativeModel(model_name)
                
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
                return response.text
                
            except Exception as e:
                last_error = str(e)
                # If it's a model not found error, continue to next model
                if "404" in str(e) or "not found" in str(e).lower():
                    continue
                else:
                    # If it's another error (like auth), fail immediately
                    return f"AI Error ({model_name}): {str(e)}"
        
        return f"AI Error: Could not find a working model. Last error: {last_error}"
        
    except Exception as e:
        return f"AI Error: {str(e)}"
