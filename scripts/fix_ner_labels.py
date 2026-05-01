import json
import re
import os

input_file = r"C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\docs\labeler-eval\api-sonnet-2k-fixed.jsonl"
output_file = r"C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\docs\labeler-eval\api-sonnet-2k-cleaned.jsonl"

def clean_year(span, full_text):
    text = span['text']
    match = re.search(r'\b((?:19|20)\d{2})\b', text)
    if match:
        year_str = match.group(1)
        # Find offset of year_str within the original span text
        offset = text.find(year_str)
        new_start = span['start'] + offset
        new_end = new_start + 4
        span['start'] = new_start
        span['end'] = new_end
        span['text'] = year_str
        return span
    return None # drop if no year found

def strip_titles(span, full_text):
    text = span['text']
    # Regex to catch "Prof. Dr.", "Yrd. Doç.", "Doç :", "Dr.", etc.
    title_regex = re.compile(r'^(?:Prof|Yrd\.\s*Doç|Yard\.\s*Doç|Doç|Dr)[\.\:]?\s*(?:Dr\.?\s*)?', re.IGNORECASE)
    match = title_regex.match(text)
    if match:
        matched_str = match.group(0)
        offset = len(matched_str)
        span['start'] += offset
        span['text'] = text[offset:]
    return span

def merge_authors(spans, full_text):
    # Sort spans by start
    spans = sorted(spans, key=lambda x: x['start'])
    merged = []
    i = 0
    while i < len(spans):
        curr = spans[i]
        if curr['entity'] == 'YAZAR':
            # look ahead to see if the next span is also YAZAR and close by
            while i + 1 < len(spans) and spans[i+1]['entity'] == 'YAZAR':
                nxt = spans[i+1]
                # check distance and text between them
                gap_text = full_text[curr['end']:nxt['start']]
                # if gap is just space, comma, or nothing, merge
                if re.match(r'^[\s,]*$', gap_text):
                    curr['end'] = nxt['end']
                    curr['text'] = full_text[curr['start']:curr['end']]
                    i += 1
                else:
                    break
        merged.append(curr)
        i += 1
    return merged

try:
    with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
        processed_count = 0
        dropped_years = 0
        merged_authors = 0
        title_strips = 0
        
        for line in f_in:
            data = json.loads(line)
            full_text = data.get('text', '')
            spans = data.get('spans', [])
            
            new_spans = []
            # First pass: clean YIL and strip titles
            for span in spans:
                if span['entity'] == 'YIL':
                    cleaned = clean_year(span, full_text)
                    if cleaned:
                        new_spans.append(cleaned)
                    else:
                        dropped_years += 1
                elif span['entity'] == 'YAZAR':
                    original_text = span['text']
                    cleaned = strip_titles(span, full_text)
                    if cleaned['text'] != original_text:
                        title_strips += 1
                    new_spans.append(cleaned)
                else:
                    new_spans.append(span)
                    
            # Second pass: merge YAZAR
            original_yazar_count = sum(1 for s in new_spans if s['entity'] == 'YAZAR')
            new_spans = merge_authors(new_spans, full_text)
            new_yazar_count = sum(1 for s in new_spans if s['entity'] == 'YAZAR')
            merged_authors += (original_yazar_count - new_yazar_count)
            
            data['spans'] = new_spans
            f_out.write(json.dumps(data, ensure_ascii=False) + '\n')
            processed_count += 1

    print(f"Processed {processed_count} paragraphs.")
    print(f"Fixed/Dropped non-numeric YIL entries: {dropped_years}")
    print(f"Stripped academic titles from YAZAR: {title_strips}")
    print(f"Merged fragmented YAZAR entries: {merged_authors}")
    print(f"Cleaned data saved to {output_file}")
    
except Exception as e:
    print(f"Error: {e}")
