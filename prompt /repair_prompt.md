# Self-Healing Prompt Instructions

The structure of the target website has changed, causing missing or null values in extraction.

## Objective
Re-analyze the target web page's HTML structure and update the extraction selectors.

## Healing Strategy
1. Identify missing target fields: {{MISSING_FIELDS}}
2. Locate updated CSS/XPath selectors or data attributes matching plain-language descriptions.
3. Update extraction schema without altering existing field names or output JSON structure.
4. Ensure downstream data compatibility.
5. 
