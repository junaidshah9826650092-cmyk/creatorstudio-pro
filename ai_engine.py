import os
import requests
import json
import re

class VitoxAI:
    """
    Vitox AI Engine - Handles LLM, ML, DL, and Generative AI logic.
    Separated from server.py for better scalability.
    """
    
    def __init__(self, budget_mode=True):
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.hf_url = "https://api-inference.huggingface.co/models/"
        self.budget_mode = budget_mode

    def _get_gemini_key(self):
        return (os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY', '')).strip()

    def _get_openrouter_key(self):
        return os.environ.get('OPENROUTER_API_KEY', '').strip()

    def _get_hf_key(self):
        return os.environ.get('HUGGINGFACE_API_KEY', '').strip()

    def ask(self, prompt, model_alias='gemini-flash', premium=False):
        """Unified method for LLM queries with automatic free model fallbacks.
        Set premium=True to unlock GPT-4-class models for premium/admin users."""
        
        # Define all models - free and premium
        models = {
            # --- Free Models ---
            'gemini-flash': 'gemini-2.5-flash',
            'llama-3-free': 'meta-llama/llama-3-8b-instruct:free',
            'mistral-free': 'mistralai/mistral-7b-instruct:free',
            'google-gemma-free': 'google/gemma-7b-it:free',
            'ollama-llama3': 'ollama:llama3:8b',
            # --- Hugging Face Models (Free Inference API) ---
            'hf-falcon': 'hf:tiiuae/falcon-7b-instruct',
            'hf-mistral': 'hf:mistralai/Mistral-7B-Instruct-v0.2',
            'hf-zephyr': 'hf:HuggingFaceH4/zephyr-7b-beta',
            # --- Premium Models (unlocked for subscribers & admin) ---
            'gemini-pro': 'gemini-2.5-pro',
            'llama-3-70b': 'meta-llama/llama-3-70b-instruct',
            'claude-haiku': 'anthropic/claude-haiku',
            'gpt-4o-mini': 'openai/gpt-4o-mini',
        }
        
        # Budget / premium guard
        if not premium:
            # Budget mode: force free models only
            if model_alias in ('gemini-pro', 'llama-3-70b', 'claude-haiku', 'gpt-4o-mini'):
                model_alias = 'gemini-flash'
            elif model_alias not in models:
                model_alias = 'llama-3-free'
        
        # Build attempt chain
        if model_alias == 'gemini-flash':
            attempts = ['gemini-flash', 'hf-zephyr', 'llama-3-free', 'mistral-free', 'google-gemma-free']
        elif model_alias == 'llama-3-free':
            attempts = ['llama-3-free', 'mistral-free', 'gemini-flash', 'hf-mistral']
        elif model_alias.startswith('hf-'):
            attempts = [model_alias, 'gemini-flash', 'llama-3-free']
        elif premium:
            attempts = [model_alias, 'gemini-pro', 'gemini-flash', 'llama-3-free']
        else:
            attempts = [model_alias]
            
        for alias in attempts:
            selected_model = models.get(alias, 'gemini-2.5-flash')
            try:
                if selected_model.startswith('hf:'):
                    # Hugging Face Inference API
                    res = self._call_huggingface(prompt, selected_model[3:])
                    if res and 'Error' not in res:
                        return res
                    raise ValueError(res)
                elif 'gemini' in selected_model:
                    key = self._get_gemini_key()
                    if not key:
                        raise ValueError("Gemini key not configured")
                    res = self._call_gemini(prompt, selected_model)
                    if "Error" in res or "not configured" in res:
                        raise ValueError(res)
                    return res
                elif selected_model.startswith('ollama'):
                    res = self._call_ollama(prompt, selected_model)
                    if "Error" in res or "Connection" in res:
                        raise ValueError(res)
                    return res
                else:
                    key = self._get_openrouter_key()
                    if not key:
                        raise ValueError("OpenRouter key not configured")
                    res = self._call_openrouter(prompt, selected_model)
                    if "Error" in res or "not configured" in res:
                        raise ValueError(res)
                    return res
            except Exception as e:
                print(f"Model {alias} ({selected_model}) failed: {e}. Trying next fallback...")
                
        # Ultimate fallback response if absolutely everything fails
        return "Vitox Girl: Mujhe lagta hai server abhi busy hai ya configurations mein thoda glitch hai. Lekin main aapse jald hi baat karungi! 🙂 Aapka din shubh ho!"

    def _call_gemini(self, prompt, model):
        key = self._get_gemini_key()
        if not key:
            return "Gemini API key not configured."
        
        try:
            url = f"{self.gemini_url}{model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
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
                    "HTTP-Referer": "https://creatorstudio-pro.onrender.com",
                    "X-Title": "Vitox AI"
                },
                data=json.dumps({
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are Vitox AI. An expert in ML, DL, LLMs and Generative AI."},
                        {"role": "user", "content": prompt}
                    ]
                }),
                timeout=30
            )
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"OpenRouter Error: {str(e)}"

    def _call_huggingface(self, prompt, model):
        """Call Hugging Face Inference API"""
        key = self._get_hf_key()
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        try:
            response = requests.post(
                f"{self.hf_url}{model}",
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_new_tokens": 512, "temperature": 0.7}},
                timeout=30
            )
            result = response.json()
            if isinstance(result, list) and result:
                text = result[0].get('generated_text', '')
                # Remove the input prompt from output if model echoes it
                if text.startswith(prompt):
                    text = text[len(prompt):].strip()
                return text or "No response from HuggingFace model."
            elif isinstance(result, dict) and 'error' in result:
                return f"HuggingFace Error: {result['error']}"
            return str(result)
        except Exception as e:
            return f"HuggingFace Error: {str(e)}"

    def _call_ollama(self, prompt, model):
        """Call a locally running Ollama model via its REST API.
        Expected model format: 'ollama:llama3:8b' or similar.
        """
        # Extract the actual model name after the prefix
        parts = model.split(':', 1)
        ollama_model = parts[1] if len(parts) > 1 else model
        url = os.getenv('OLLAMA_URL', 'http://localhost:11434') + '/api/generate'
        try:
            resp = requests.post(url, json={
                'model': ollama_model,
                'prompt': prompt,
                'stream': False
            }, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get('response', '')
        except Exception as e:
            return f"Ollama Error: {str(e)}"

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

    def check_uniqueness(self, title, description):
        """Deep Content Uniqueness Benchmark"""
        # We compare against global fingerprints (Mocking high-fidelity ML check)
        prompt = f"Analyze content uniqueness vs global internet standards: Title: {title}, Desc: {description}. Is this creative/unique? Return ONLY 'unique' or 'common'."
        res = self.ask(prompt, model_alias='gemini-flash').lower()
        return 'common' not in res

    def copyright_scan(self, title):
        """AI Patent/Copyright Scanning"""
        # Detecting trademark violations or copyrighted franchise names
        restricted = ['disney', 'marvel', 'netflix', 'hbo', 'warner bros', 'full movie', 'official trailer 2026']
        for word in restricted:
            if word in title.lower():
                return False
        return True

    # Placeholders for future ML/DL modules
    def predict_trending(self, video_data):
        """ML Placeholder for trending prediction based on velocity and engagement"""
        # Simulated ML model scoring
        score = 85
        if 'title' in video_data and any(w in video_data['title'].lower() for w in ['ai', 'next-gen', 'future']):
            score += 10
        return f"Prediction: High-Velocity Potential (Uniqueness Score: {score}/100)"

    def smart_search_rerank(self, query, videos):
        """Re-rank search results using semantic similarity simulation"""
        # In a real app, this would use vector embeddings
        results = []
        for v in videos:
            rank = 0
            if query.lower() in v.get('title', '').lower(): rank += 10
            if query.lower() in v.get('description', '').lower(): rank += 5
            results.append({'video': v, 'rank': rank})
        
        return [r['video'] for r in sorted(results, key=lambda x: x['rank'], reverse=True)]

    def generate_image_asset(self, prompt):
        """DALL-E / Stable Diffusion simulation for creator studio"""
        return "Generation Request Sent: Synthesizing neural asset for " + prompt
