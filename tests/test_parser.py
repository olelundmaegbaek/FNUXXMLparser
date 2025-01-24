"""Tests for the FNUX XML parser."""

import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from fnuxxmlparser.parser import (
    extract_date_from_datotid,
    parse_fnux_xml,
    extract_medical_data,
    XMLParserError,
)

def test_extract_date_from_datotid():
    """Test date extraction from DatoTid format."""
    assert extract_date_from_datotid("2024-01-24T10:00:00Z") == "2024-01-24"
    assert extract_date_from_datotid("") == ""
    assert extract_date_from_datotid(None) == ""

def test_parse_fnux_xml_file_not_found():
    """Test handling of non-existent XML file."""
    with pytest.raises(FileNotFoundError):
        parse_fnux_xml("nonexistent.xml")

def test_parse_fnux_xml_invalid_xml():
    """Test handling of invalid XML file."""
    with patch('xml.etree.ElementTree.parse') as mock_parse:
        mock_parse.side_effect = ET.ParseError("Invalid XML")
        with pytest.raises(XMLParserError):
            parse_fnux_xml(Path(__file__).parent / "test_data" / "invalid.xml")

def test_extract_medical_data_empty():
    """Test extraction from empty XML."""
    # Create a minimal XML structure
    root = ET.Element("{urn:oio:medcom:plo:2009.12.31}FnuxEnvelope")
    tree = ET.ElementTree(root)
    
    data = extract_medical_data(tree)
    
    assert data == {
        'cave_entries': [],
        'vaccinations': [],
        'diagnoses': [],
        'kontinuationer': []
    }

# TODO: Add more comprehensive tests:
# - Test with actual XML files
# - Test each extraction function separately
# - Test error cases and edge cases
# - Test LLM integration (with mocked responses)
