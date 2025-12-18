import csv
import re
import os
import random

def curate_repos(input_path, output_path):
    # Aggressive exclude list for informational repositories
    exclude_keywords = {
        'awesome', 'list', 'learning', 'tutorial', 'interview', 'cheatsheet', 
        'roadmap', 'guide', 'collection', 'resource', 'book', 'poetry',
        'concepts', 'practices', 'algorithms', 'standard', 'style guide',
        'lessons', 'curriculum', 'questions', 'answers', 'cheatsheets',
        'examples', 'notes', 'snippets', 'handbook', 'solutions', 'record',
        'tips', 'tricks', 'knowledge', 'principles', 'summary', 'education',
        'roadmap', 'pathway', 'syllabus', 'chinese', 'translation', 'pronunciation'
    }

    # Descriptors that strongly suggest the repo contains functional software
    software_indicators = {
        'library', 'framework', 'tool', 'client', 'server', 'engine', 
        'parser', 'middleware', 'compiler', 'bundler', 'runtime', 
        'plugin', 'component', 'app'
    }

    def is_curated(row):
        # Criteria 1: Language must be JavaScript
        if row['language'] != 'JavaScript':
            return False
        
        text = (row['name'] + ' ' + row['full_name'] + ' ' + row['description'] + ' ' + row['topics']).lower()
        
        # Criteria 1 (continued): Exclude if it appears to be a TypeScript project
        # (High-star JS repos often have .d.ts files, but we exclude if TS is a major topic/identifier)
        if 'typescript' in text or 'ts' in row['topics'].split(', '):
            return False

        # Criteria 2: Exclude informational/documentation/awesome-list repos
        for word in exclude_keywords:
            if re.search(r'\b' + re.escape(word) + r'\b', text):
                return False
                
        # Exclude common non-production repo types
        if any(re.search(r'\b' + re.escape(x) + r'\b', text) for x in ['sample', 'demo', 'example', 'boilerplate', 'template']):
            return False

        # Criteria 3: Must be actual software (heuristic for functional codebase with tests)
        if not any(re.search(r'\b' + re.escape(indicator) + r'\b', text) for indicator in software_indicators):
            return False

        return True

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    curated_rows = []
    header = []
    
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        for row in reader:
            if is_curated(row):
                curated_rows.append(row)

    random.shuffle(curated_rows)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(curated_rows)

    print(f"Curated {len(curated_rows)} repositories into {output_path}")

if __name__ == "__main__":
    input_file = 'new_repos.csv'
    output_file = 'new_curated_repos.csv'
    curate_repos(input_file, output_file)
