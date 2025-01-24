# FNUX XML Parser API Documentation

## Core Functions

### XML Parsing

#### `parse_fnux_xml(xml_path: Union[str, Path]) -> ET.ElementTree`
Parse a FNUX XML file and return an ElementTree object.

**Parameters:**
- `xml_path`: Path to the XML file to parse (string or Path object)

**Returns:**
- Parsed ElementTree object

**Raises:**
- `FileNotFoundError`: If XML file doesn't exist
- `XMLParserError`: If there are issues parsing the XML

#### `extract_medical_data(tree: ET.ElementTree) -> Dict[str, Any]`
Extract relevant medical data from XML structure.

**Parameters:**
- `tree`: Parsed ElementTree object containing FNUX XML data

**Returns:**
Dictionary containing:
- `cave_entries`: List of cave information strings
- `vaccinations`: List of vaccination records
- `diagnoses`: List of diagnosis strings
- `kontinuationer`: List of continuation records

### LLM Integration

#### `generate_medical_summary(data: Dict[str, Any], auto_approve: bool = False) -> str`
Generate medical summary using configured LLM.

**Parameters:**
- `data`: Dictionary containing medical data
- `auto_approve`: Whether to skip prompt confirmation (default: False)

**Returns:**
- Generated medical summary text

**Raises:**
- `ConfigurationError`: If LLM configuration is invalid
- `LLMError`: If there are issues with LLM processing

### Configuration

#### `load_llm_config(config_path: Optional[Path] = None) -> Dict[Any, Any]`
Load and validate LLM configuration from YAML.

**Parameters:**
- `config_path`: Optional path to config file. If not provided, looks in default locations.

**Returns:**
- Dictionary containing the validated configuration

**Raises:**
- `ConfigurationError`: If config file is missing or invalid
- `FileNotFoundError`: If the specified config file doesn't exist

## Configuration File Structure

The `llm_config.yaml` file should contain:

```yaml
llm:
  # OpenAI settings
  base_url: "https://api.example.com/v1"
  api_key: "your-api-key"
  model: "gpt-3.5-turbo"
  
  # Generation parameters
  parameters:
    temperature: 0.2
    max_tokens: 1000
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0
    stop: ["</report>"]
    
  # Prompt configuration
  prompt:
    system_message: "..."
    format_instructions: "..."

  # Logging configuration
  logging:
    enabled: true
    level: "INFO"
    file: "llm_calls.log"
```

## Error Types

### `XMLParserError`
Raised when there are issues parsing the XML file.

### `ConfigurationError`
Raised when there are issues with the configuration file or its contents.

### `LLMError`
Raised when there are issues with LLM processing.

## Usage Examples

### Basic Usage
```python
from fnuxxmlparser.parser import parse_fnux_xml, extract_medical_data, generate_medical_summary

# Parse XML file
tree = parse_fnux_xml("patient_data.xml")

# Extract data
medical_data = extract_medical_data(tree)

# Generate summary
summary = generate_medical_summary(medical_data)
print(summary)
```

### Custom Configuration
```python
from pathlib import Path
from fnuxxmlparser.config import load_llm_config

# Load custom configuration
config = load_llm_config(Path("custom_config.yaml"))

# Use in summary generation
summary = generate_medical_summary(medical_data, auto_approve=True)
