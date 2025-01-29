"""FNUX XML Parser for medical data summarization."""

import sys
from typing import Dict, List, Any

from openai import OpenAI

from .config import load_llm_config, setup_llm_logging, ConfigurationError
from .xml_parser import parse_fnux_xml, extract_medical_data, XMLParserError

def generate_medical_summary(data: Dict[str, Any], auto_approve: bool = False) -> str:
    """Generate medical summary using configured LLM.
    
    Args:
        data: Dictionary containing medical data
        auto_approve: Whether to skip prompt confirmation
        
    Returns:
        Generated medical summary
        
    Raises:
        ConfigurationError: If LLM configuration is invalid
        LLMError: If there are issues with LLM processing
    """
    # Load and validate configuration
    config = load_llm_config()
    setup_llm_logging(config)
    
    # Format data sections
    sections = {
        'cave_info': _format_list(data['cave_entries'], "Ingen registrerede cave-oplysninger"),
        'vaccines_info': _format_vaccinations(data['vaccinations']),
        'diagnoses_info': _format_list(data['diagnoses'], "Ingen registrerede diagnoser"),
        'kontinuationer_info': _format_kontinuationer(data['kontinuationer'])
    }
    
    # Build user prompt
    user_prompt = _build_prompt(sections, config['llm']['prompt']['format_instructions'])
    
    print("\n=== LLM Prompt Preview ===")
    print(user_prompt)
    print("===========================")
    
    if not auto_approve and sys.stdin.isatty():
        confirm = input("\nSend denne prompt til LLM? (j/n): ")
        if confirm.lower() != 'j':
            raise LLMError("User aborted process")
    else:
        print("\nAutomatisk godkendt (ikke-interaktiv tilstand)")
    
    try:
        client = OpenAI(
            base_url=config['llm']['base_url'],
            api_key=config['llm']['api_key']
        )
        response = client.chat.completions.create(
            model=config['llm']['model'],
            messages=[
                {"role": "system", "content": config['llm']['prompt']['system_message']},
                {"role": "user", "content": user_prompt}
            ],
            **config['llm']['parameters']
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise LLMError(f"LLM processing failed: {str(e)}")

def _format_list(items: List[str], empty_msg: str) -> str:
    """Format a list of items with bullet points."""
    return "\n".join(f"- {item}" for item in items) if items else empty_msg

def _format_vaccinations(vaccinations: List[Dict[str, str]]) -> str:
    """Format vaccination records."""
    if not vaccinations:
        return "Ingen registrerede vaccinationer"
    return "\n".join(f"- {v['date']}: {v['vaccine']}" for v in vaccinations)

def _format_kontinuationer(kontinuationer: List[Dict[str, str]]) -> str:
    """Format continuation records."""
    if not kontinuationer:
        return "Ingen registrerede kontinuationer"
    return "\n".join(f"- {k['date']}: {k['text']}" for k in kontinuationer)

def _build_prompt(sections: Dict[str, str], format_instructions: str) -> str:
    """Build the complete prompt for LLM."""
    return f'''### Cave-informationer:
{sections['cave_info']}
### Vaccinationshistorik:
{sections['vaccines_info']}
### Diagnosekoder:
{sections['diagnoses_info']}
### Kontinuationer:
{sections['kontinuationer_info']}

{format_instructions}'''

def main() -> None:
    """Main CLI interface."""
    try:
        # Get input file path
        if len(sys.argv) > 1:
            xml_path = sys.argv[1]
        elif sys.stdin.isatty():
            xml_path = input("Indtast sti til FNUX XML fil: ")
        else:
            xml_path = sys.stdin.readline().strip()
        
        # Process XML and generate summary
        tree = parse_fnux_xml(xml_path)
        medical_data = extract_medical_data(tree)
        summary = generate_medical_summary(medical_data)
        
        # Display results
        print("\n=== Medicinsk Resume ===")
        print(summary)
        
    except (FileNotFoundError, XMLParserError, ConfigurationError, LLMError) as e:
        print(f"\nFejl: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUventet fejl: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
