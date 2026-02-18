import os
import requests
import json
import re

class VitoxAI:
    """
    Vitox AI Engine - Handles LLM, ML, DL, and Generative AI logic.
    Separated from server.py for better scalability.
    """
    
    def __init__(self):
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

    def _get_gemini_key(self):
        return os.environ.get('GOOGLE_API_KEY', '').strip()

    def _get_openrouter_key(self):
        return os.environ.get('OPENROUTER_API_KEY', '').strip()

    def ask(self, prompt, model_alias='gemini-flash'):
        """Unified method for LLM queries (including ML/DL/Generative tasks)"""
        
        models = {
            'gemini-flash': 'gemini-1.5-flash',
            'gemini-pro': 'gemini-1.5-pro',
            'llama-3-free': 'meta-llama/llama-3-8b-instruct:free',
            'mistral-free': 'mistralai/mistral-7b-instruct:free',
            'google-gemma-free': 'google/gemma-7b-it:free'
        }
        
        selected_model = models.get(model_alias, 'gemini-1.5-flash')
        
        if 'gemini' in selected_model:
            return self._call_gemini(prompt, selected_model)
        else:
            return self._call_openrouter(prompt, selected_model)

    def _call_gemini(self, prompt, model):
        key = self._get_gemini_key()
        if not key:
            return "Gemini API key not configured."
        
        try:
            url = f"{self.gemini_url}{model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            result = res.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"Gemini Error: {str(e)}"

    def _call_openrouter(self, prompt, model):
        key = self._get_openrouter_key()
        if not key:
            return "OpenRouter API key not configured."
            
        try:
            response = requests.post(
                url=self.openrouter_url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are Vitox AI. An expert in ML, DL, LLMs and Generative AI."},
                        {"role": "user", "content": prompt}
                    ]
                })
            )
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"OpenRouter Error: {str(e)}"

    def suggest_content(self, topic):
        """Specialized for content creation helpers"""
        prompt = f"Suggest a catchy video title and a 2-sentence description for a video about: {topic}. Return ONLY raw JSON format with 'title' and 'description' keys."
        raw_res = self.ask(prompt, model_alias='gemini-flash')
        
        try:
            # Clean up JSON if LLM added markdown formatting
            clean_text = re.sub(r'```json\n?|\n?```', '', raw_res).strip()
            return json.loads(clean_text)
        except:
            return {
                'title': f'Exploring {topic}',
                'description': f'A deep dive into {topic} on Vitox.'
            }

    def moderate(self, title, description):
        """Content Moderation Module"""
        prompt = f"Moderation Request: Title: {title}, Description: {description}. Does this violate policies against nudity, hate speech, or extreme violence? Return ONLY 'safe' or 'unsafe'."
        res = self.ask(prompt, model_alias='gemini-flash').lower()
        return 'unsafe' if 'unsafe' in res else 'safe'

    # Placeholders for future ML/DL modules
    def predict_trending(self, video_data):
        """ML Placeholder for trending prediction"""
        return "Prediction: Potential Viral Content (Score: 85/100)"

    def generate_image_asset(self, prompt):
        """DALL-E / Stable Diffusion Placeholder"""
        return "Generation Request Sent: Generating AI asset for " + prompt
