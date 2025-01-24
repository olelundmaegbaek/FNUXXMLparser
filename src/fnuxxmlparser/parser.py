"""FNUX XML Parser for medical data extraction and summarization."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from openai import OpenAI

from .config import load_llm_config, setup_llm_logging, ConfigurationError

# XML Namespace definitions
FNUX_NS = {
    'plo': 'urn:oio:medcom:plo:2009.12.31',
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
}

class XMLParserError(Exception):
    """Raised when there are issues parsing the XML file."""
    pass

class LLMError(Exception):
    """Raised when there are issues with LLM processing."""
    pass

def extract_date_from_datotid(datotid: str) -> str:
    """Extract date part from DatoTid format.
    
    Args:
        datotid: Date-time string in format YYYY-MM-DDThh:mm:ssZ
        
    Returns:
        Date part of the string (YYYY-MM-DD)
    """
    return datotid.split('T')[0] if datotid else ''

def parse_fnux_xml(xml_path: Union[str, Path]) -> ET.ElementTree:
    """Parse FNUX XML file and return ElementTree object.
    
    Args:
        xml_path: Path to the XML file to parse
        
    Returns:
        Parsed ElementTree object
        
    Raises:
        FileNotFoundError: If XML file doesn't exist
        XMLParserError: If there are issues parsing the XML
    """
    path = Path(xml_path)
    if not path.exists():
        raise FileNotFoundError(f"XML file not found: {path}")
    
    try:
        # Register namespace
        ET.register_namespace('', FNUX_NS['plo'])
        return ET.parse(path)
    except ET.ParseError as e:
        raise XMLParserError(f"Failed to parse XML file: {e}")

def extract_medical_data(tree: ET.ElementTree) -> Dict[str, Any]:
    """Extract relevant medical data from XML structure.
    
    Args:
        tree: Parsed ElementTree object containing FNUX XML data
        
    Returns:
        Dictionary containing extracted medical data with keys:
        - cave_entries: List of cave information strings
        - vaccinations: List of vaccination records
        - diagnoses: List of diagnosis strings
        - kontinuationer: List of continuation records
    """
    root = tree.getroot()
    
    # Extract cave entries
    cave_entries = _extract_cave_entries(root)
    
    # Extract vaccinations
    vaccinations = _extract_vaccinations(root)
    
    # Extract diagnoses
    diagnoses = _extract_diagnoses(root)
    
    # Extract kontinuationer
    kontinuationer = _extract_kontinuationer(root)
    
    return {
        'cave_entries': cave_entries,
        'vaccinations': vaccinations,
        'diagnoses': diagnoses,
        'kontinuationer': kontinuationer
    }

def _extract_cave_entries(root: ET.Element) -> List[str]:
    """Extract cave entries from XML root."""
    cave_entries = []
    cave_samling = root.find('.//plo:CaveSamling', FNUX_NS)
    if cave_samling is not None:
        kommentar_linie_samling = cave_samling.find('plo:CaveStruktur/plo:KommentarLinieSamling', FNUX_NS)
        if kommentar_linie_samling is not None:
            cave_entries = [
                elem.text.strip()
                for elem in kommentar_linie_samling.findall('plo:LinieTekst', FNUX_NS)
                if elem.text and elem.text.strip()
            ]
    return cave_entries

def _extract_vaccinations(root: ET.Element) -> List[Dict[str, str]]:
    """Extract vaccination records from XML root."""
    vaccinations = []
    vacc_samling = root.find('.//plo:VaccinationSamling', FNUX_NS)
    if vacc_samling is not None:
        for vacc in vacc_samling.findall('plo:VaccinationStruktur', FNUX_NS):
            date_elem = vacc.find('.//plo:DatoTid', FNUX_NS)
            vaccine_elem = vacc.find('.//plo:VaccinationNavn', FNUX_NS)
            
            if date_elem is not None and vaccine_elem is not None:
                vaccinations.append({
                    'date': extract_date_from_datotid(date_elem.text),
                    'vaccine': vaccine_elem.text
                })
    return vaccinations

def _extract_diagnoses(root: ET.Element) -> List[str]:
    """Extract diagnosis records from XML root."""
    diagnoses = []
    diagnose_samling = root.find('.//plo:DiagnoseSamling', FNUX_NS)
    if diagnose_samling is not None:
        for diagnose in diagnose_samling.findall('plo:DiagnoseStruktur', FNUX_NS):
            kode_struktur = diagnose.find('plo:KodeStruktur', FNUX_NS)
            if kode_struktur is not None:
                kl_ids = kode_struktur.findall('plo:KlassifikationsIdentifikator', FNUX_NS)
                koder = kode_struktur.findall('plo:Kode', FNUX_NS)
                tekster = kode_struktur.findall('plo:KodeTekst', FNUX_NS)
                
                for kl_id, kode, tekst in zip(kl_ids, koder, tekster):
                    if all([kl_id is not None, kode is not None, tekst is not None]):
                        diagnoses.append(
                            f"{kl_id.text.strip()} {kode.text.strip()}: {tekst.text.strip()}"
                        )
    return diagnoses

def _extract_kontinuationer(root: ET.Element) -> List[Dict[str, str]]:
    """Extract continuation records from XML root."""
    kontinuationer = []
    kontinuation_samling = root.find('.//plo:NoteSamling', FNUX_NS)
    if kontinuation_samling is not None:
        for note_struktur in kontinuation_samling.findall('plo:NoteStruktur', FNUX_NS):
            dates = note_struktur.findall('plo:DatoTid', FNUX_NS)
            texts = note_struktur.findall('plo:Tekst', FNUX_NS)
            note_types = note_struktur.findall('plo:EgneNoterKode', FNUX_NS)
            
            for date_elem, text_elem, note_type in zip(dates, texts, note_types):
                if note_type is None or note_type.text.strip() != 'Kontinuation':
                    continue
                
                if None in [date_elem, text_elem]:
                    continue
                
                text_parts = []
                for t in text_elem.findall('.//w:t', FNUX_NS):
                    if t.text and t.text.strip():
                        text_parts.append(t.text.strip())
                
                if text_parts:
                    kontinuationer.append({
                        'date': extract_date_from_datotid(date_elem.text.strip()),
                        'text': ' '.join(text_parts)
                    })
    return kontinuationer

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
