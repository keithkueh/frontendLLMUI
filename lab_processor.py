# lab_processor.py
from agents import function_tool

@function_tool
def extract_lab_values(lab_text):
    """Extract key-value pairs from lab report text"""
    # This is a placeholder - in a real implementation, you would use
    # regex or NLP techniques to extract structured data from lab reports
    import re
    
    extracted_values = {}
    # Example pattern: "Test Name: Value Unit (Reference Range)"
    pattern = r'(\w+[\s\w]*?):\s*([\d\.]+)\s*(\w+)?\s*\(([^)]+)\)'
    
    matches = re.findall(pattern, lab_text)
    for match in matches:
        test_name, value, unit, ref_range = match
        extracted_values[test_name] = {
            'value': value,
            'unit': unit,
            'reference_range': ref_range
        }
    
    return extracted_values
