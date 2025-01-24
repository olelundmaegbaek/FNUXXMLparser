# FNUX XML Parser

En Python-pakke til at parse og analysere FNUX XML-filer med medicinsk data og generere resuméer ved hjælp af LLM.

## Installation

```bash
pip install fnuxxmlparser
```

For udvikling, installer med ekstra udviklerværktøjer:
```bash
pip install fnuxxmlparser[dev]
```

## Konfiguration

Opret en `llm_config.yaml` fil i en af følgende placeringer:
- `./config/llm_config.yaml`
- `./llm_config.yaml`

Eksempel på konfiguration:
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
    system_message: "Du er en erfaren dansk læge der skal lave et resume af patientdata."
    format_instructions: |
      Opret en professionel medicinsk resume med følgende struktur:
      <report>
      ## Medicinsk Resume
      [Her skal du skriver resume af diagnoser og kontinuationer]
      ### Vigtigste Oplysninger
      [Her skal du fremhæve vigtige cave-oplysninger og vaccinationer]
      
      ### Klinisk Vurdering
      [Her skal du give en faglig vurdering af informationerne]
      </report>

  # Logging configuration
  logging:
    enabled: true
    level: "INFO"
    file: "llm_calls.log"
```

## Brug

### Fra kommandolinjen

```bash
# Parse XML-fil og generer resumé
fnuxxmlparser path/to/file.xml

# Eller pipe input
cat path/to/file.xml | fnuxxmlparser
```

### Som Python-modul

```python
from fnuxxmlparser.parser import parse_fnux_xml, extract_medical_data, generate_medical_summary

# Parse XML
tree = parse_fnux_xml("path/to/file.xml")

# Udtræk data
medical_data = extract_medical_data(tree)

# Generer resumé
summary = generate_medical_summary(medical_data)
print(summary)
```

## Udvikling

1. Klon repository:
```bash
git clone https://github.com/username/fnuxxmlparser.git
cd fnuxxmlparser
```

2. Opret og aktiver virtuelt miljø:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installer udviklingsafhængigheder:
```bash
pip install -e ".[dev]"
```

4. Kør tests:
```bash
pytest
```

5. Formatér kode:
```bash
black .
isort .
```

6. Kør type check:
```bash
mypy src/fnuxxmlparser
```

## Licens

Dette projekt er licenseret under MIT-licensen - se [LICENSE](LICENSE) filen for detaljer.
