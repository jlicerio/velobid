# Bidder Profiles

This directory contains modular bidder configurations for the VeloBid system. Each subdirectory represents a single bidder/contractor entity.

## Directory Structure

```
bidders/
├── air_hero/
│   └── bidder.json          # Air Hero LLC (active)
├── template_example/
│   └── bidder.json          # Copy this to add new bidders
├── README.md                # This file
└── (add your own bidders here)
```

## Adding a New Bidder

### Step 1: Create Directory
```bash
cp -r template_example your_company
cd your_company
```

### Step 2: Edit bidder.json
```json
{
  "company_name": "Your Company Inc.",
  "primary_contact": "John Smith",
  "contact_email": "john@yourcompany.com",
  "phone": "(555) 123-4567",
  "location": "Houston, TX",
  "trade_domain": "Electrical / Division 26",
  "operating_region": "Greater Houston Area"
}
```

### Step 3: Reference in Project Config
In your project JSON, add:
```json
{
  "name": "Your Project",
  ...other fields...,
  "bidder": "your_company"
}
```

### Step 4: Generate Bids
```bash
python generate_pdfs.py --project config/projects/your_project.json --trade electrical
```

## Bidder Alias System

Aliases provide shortcuts to bidder names. Add to `generate_pdfs.py::BIDDER_ALIASES`:

```python
BIDDER_ALIASES: dict[str, str] = {
    "air_hero": "air_hero",
    "hero": "air_hero",              # Alias
    "your_company": "your_company",
    "your_alias": "your_company",    # Alias
}
```

## Multi-Bidder Workflow

The same project can generate bids for multiple bidders. Example:

```bash
# Generate HVAC bid from Air Hero
python generate_pdfs.py --project shalom.json --trade hvac --output bids/air_hero

# Generate Electrical bid from different contractor
# (add "bidder": "your_company" to shalom.json, or use different project config)
```

## Bidder Config Fields

### Required
- `company_name`: Legal company name (appears on PDFs)
- `primary_contact`: Contact person name

### Optional but Recommended
- `contact_email`: Email address
- `phone`: Phone number
- `location`: HQ location (city, state)
- `trade_domain`: Primary trade/division focus
- `operating_region`: Geographic service area

### Phase 2 Extensions (Planned)
Future versions will support:
- `logo_path`: Path to company logo for PDF header
- `primary_color`: Brand color (hex code)
- `secondary_color`: Accent color
- `tax_id`: EIN for invoicing
- `license_numbers`: Trade licenses per division

## Troubleshooting

### "Config file not found: config/bidders/xyz/bidder.json"
- Check bidder directory exists with correct spelling
- Verify `bidder.json` file is in directory
- Check JSON is valid (use `python -m json.tool bidder.json`)

### Bids showing wrong company name
- Verify project config has correct `"bidder": "..."` field
- Check bidder.json `company_name` value
- Default fallback is always `air_hero`

### Adding bidder doesn't work
- Make sure directory name matches `"bidder": "..."` value (case-sensitive on Linux/Mac)
- Update `BIDDER_ALIASES` in `generate_pdfs.py` if using aliases
- Restart Python process / clear any caches

## File Size Expectations

Each bidder directory should have:
- `bidder.json` — ~300-500 bytes

Future versions may include:
- `logo.png` — ~10-50 KB (optional)
- `styles.json` — ~500-1000 bytes (brand colors, fonts)
- `templates/` — custom overrides per bidder

## Security Notes

Bidder configs are configuration-only — no sensitive data should be stored here. Passwords, API keys, and credentials belong in environment variables or secure vaults, never in version-controlled JSON files.
