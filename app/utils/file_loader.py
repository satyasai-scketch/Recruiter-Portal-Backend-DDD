import json
from typing import Dict, Any, List, Union
from pathlib import Path

class JDFileLoader:
    """Utility for loading JD templates from files"""
    
    @staticmethod
    def load_from_json_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Load JD templates from a JSON file.
        Handles both single JD objects and arrays of JDs.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of JD dictionaries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single JD and array of JDs
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError(f"Invalid JSON structure in {file_path}")
    
    @staticmethod
    def load_from_directory(directory_path: str) -> List[Dict[str, Any]]:
        """
        Load all JD templates from JSON files in a directory.
        
        Args:
            directory_path: Path to directory containing JSON files
            
        Returns:
            List of all JD dictionaries from all files
        """
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        all_jds = []
        json_files = list(dir_path.glob("*.json"))
        
        for json_file in json_files:
            try:
                jds = JDFileLoader.load_from_json_file(str(json_file))
                all_jds.extend(jds)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        return all_jds
    
    @staticmethod
    def parse_json_text(json_text: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Parse JD data from JSON string.
        
        Args:
            json_text: JSON string
            
        Returns:
            JD dictionary or list of JD dictionaries
        """
        return json.loads(json_text)