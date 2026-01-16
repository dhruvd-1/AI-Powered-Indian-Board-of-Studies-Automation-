"""
Base agent class with Ollama integration.
"""

import json
import re
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Base class for all AI agents in the system.
    
    Provides common functionality for Ollama API calls and response parsing.
    """
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        """
        Initialize agent with Ollama model.
        
        Args:
            model_name: Name of Ollama model to use
        """
        self.model_name = model_name
        self._verify_ollama()
    
    def _verify_ollama(self):
        """Verify Ollama is available and model is installed."""
        try:
            import ollama
            
            # Check if model exists
            models = ollama.list()
            model_list = models.get('models', [])
            
            # Robust name extraction
            model_names = []
            for m in model_list:
                if isinstance(m, dict):
                    # Try different possible keys
                    name = m.get('name') or m.get('model') or m.get('id', '')
                    if name:
                        model_names.append(name)
            
            if model_names and not any(self.model_name in name for name in model_names):
                print(f"⚠️ Model '{self.model_name}' not found")
                print(f"   Available models: {model_names}")
                print(f"   Run: ollama pull {self.model_name}")
            
        except ImportError:
            raise ImportError(
                "Ollama Python package not installed.\n"
                "Install with: pip install ollama"
            )
        except Exception as e:
            print(f"⚠️ Could not verify Ollama: {e}")
    
    def call_llm(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Call Ollama LLM with prompt.
        
        Args:
            prompt: Full prompt string
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response tokens
            
        Returns:
            LLM response as string
        """
        import ollama
        
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                    'num_gpu': 0,  # Force CPU mode to avoid CUDA allocation errors
                }
            )
            
            return response['response']
            
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            raise
    
    def extract_json(self, text: str) -> Optional[Dict]:
        """
        Extract JSON from LLM response.
        
        LLMs sometimes wrap JSON in markdown code blocks or add extra text.
        This method robustly extracts the JSON.
        
        Args:
            text: LLM response text
            
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        # Try to find JSON in code blocks first
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON (look for outermost braces)
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = text
        
        # Try to parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse JSON from response")
            print(f"   Response preview: {text[:200]}...")
            return None
    
    @abstractmethod
    def process(self, **kwargs) -> Dict:
        """
        Process input and return output.
        
        Must be implemented by subclasses.
        """
        pass