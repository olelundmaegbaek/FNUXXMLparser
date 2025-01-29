"""FNUX XML Parser for medical data extraction."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Union

# XML Namespace definitions
FNUX_NS = {
    'plo': 'urn:oio:medcom:plo:2009.12.31',
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
}

class XMLParserError(Exception):
    """Raised when there are issues parsing the XML file."""
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
        for cave_struktur in cave_samling.findall('plo:CaveStruktur', FNUX_NS):
            for kommentar_linie_samling in cave_struktur.findall('plo:KommentarLinieSamling', FNUX_NS):
                lines = [
                    elem.text.strip()
                    for elem in kommentar_linie_samling.findall('plo:LinieTekst', FNUX_NS)
                    if elem.text and elem.text.strip()
                ]
                # Process lines in pairs
                for i in range(0, len(lines), 2):
                    if i + 1 < len(lines):
                        cave_entries.append(f"{lines[i]}: {lines[i+1]}")
                    else:
                        cave_entries.append(lines[i])
    return cave_entries

def _extract_vaccinations(root: ET.Element) -> List[Dict[str, str]]:
    """Extract vaccination records from XML root."""
    vaccinations = []
    vacc_samling = root.find('.//plo:VaccinationSamling', FNUX_NS)
    if vacc_samling is not None:
        for vacc in vacc_samling.findall('plo:VaccinationStruktur', FNUX_NS):
            # Get all elements in order
            elements = list(vacc)
            
            # Iterate through elements to find UUID/DatoTid/VaccinationNavn groups
            i = 0
            while i < len(elements):
                if elements[i].tag == f'{{{FNUX_NS["plo"]}}}UUID':
                    # Look ahead for DatoTid and VaccinationNavn
                    date_elem = None
                    vaccine_elem = None
                    
                    # Check next few elements for matching data
                    for j in range(i + 1, min(i + 4, len(elements))):
                        if elements[j].tag == f'{{{FNUX_NS["plo"]}}}DatoTid':
                            date_elem = elements[j]
                        elif elements[j].tag == f'{{{FNUX_NS["plo"]}}}VaccinationNavn':
                            vaccine_elem = elements[j]
                    
                    if date_elem is not None and vaccine_elem is not None:
                        vaccinations.append({
                            'date': extract_date_from_datotid(date_elem.text),
                            'vaccine': vaccine_elem.text
                        })
                i += 1
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
