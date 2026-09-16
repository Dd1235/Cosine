"""Narrow, fail-closed statement adapters for verified CodeChef/Kattis PYQs.

Only fetches a statement; the existing solve/label/skeptic pipeline still owns
publication. Unsupported or gated pages must remain collection resources.
"""
import ast
import re
from urllib.parse import urlparse


def kattis_body(page):
    start = re.search(r'<div[^>]*class="[^"]*\bproblembody\b[^"]*"[^>]*>', page)
    if not start:
        raise ValueError('Kattis statement unavailable; retain resource link')
    depth = 1
    for tag in re.finditer(r'</?div\b[^>]*>', page[start.end():], re.I):
        depth += -1 if tag.group().startswith('</') else 1
        if depth == 0:
            return page[start.end():start.end() + tag.start()]
    raise ValueError('truncated Kattis statement')


def codechef_extras(data, slugify):
    """The metadata a CodeChef problem page carries beyond its statement.

    `computed_tags` is CodeChef's own classification and `user_tags` is the
    crowd's; the computed list is preferred and the crowd list is the fallback,
    and both are slugified so they read like every other judge tag in the
    corpus. They are JUDGE tags, kept apart from the reviewed labels.

    `difficulty_rating` is -1 on every ICPC replay problem — CodeChef's "not
    rated" sentinel, which it returns as the string '-1'. A sentinel is not a
    rating, so it is dropped rather than stored as one."""
    tags = data.get('computed_tags') or data.get('user_tags') or []
    extras = {'judge_tags': [slugify(str(t)) for t in tags if str(t).strip()],
              'date_added': data.get('date_added') or None,
              'problem_author': data.get('problem_author') or None}
    try:
        rating = int(str(data.get('difficulty_rating')))
    except (TypeError, ValueError):
        rating = -1
    if rating != -1:
        extras['difficulty_rating'] = rating
    return extras


def metadata(url, topic):
    from annotate_problem_urls import request_json, request_text, html_to_text, slugify
    parsed = urlparse(url)
    extras = {}
    match = re.search(r'/problems/([A-Za-z0-9_-]+)/?$', parsed.path)
    if not match:
        raise ValueError('expected a direct problem URL')
    code = match.group(1)
    if parsed.hostname in {'codechef.com', 'www.codechef.com'}:
        platform = 'codechef'
        data = request_json(f'https://www.codechef.com/api/contests/PRACTICE/problems/{code}')
        title = data.get('problem_name') or data.get('name')
        components = data.get('problemComponents')
        if isinstance(components, str):
            components = ast.literal_eval(components)
        if isinstance(components, dict) and components.get('statement'):
            sections = [components['statement']]
            for label, key in [('Input', 'inputFormat'), ('Output', 'outputFormat'), ('Constraints', 'constraints')]:
                if components.get(key):
                    sections.extend([label, components[key]])
            for sample in components.get('sampleTestCases', []):
                if not sample.get('isDeleted'):
                    sections.extend(['Sample Input', sample.get('input', ''), 'Sample Output', sample.get('output', ''), sample.get('explanation', '')])
            raw = '\n\n'.join(sections).replace('\\n', '\n')
        else:
            raw = data.get('body')
            if isinstance(raw, dict):
                raw = raw.get('en')
            if raw and re.search(r'problem statement.*template|remove.*before.*publish', raw, re.I):
                raise ValueError('placeholder statement; retain resource link')
        text = html_to_text(raw or '')
        extras = codechef_extras(data, slugify)
    elif parsed.hostname in {'open.kattis.com', 'icpc.kattis.com'}:
        platform = 'kattis'
        page = request_text(url)
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', page, re.S)
        title = html_to_text(title_match.group(1)) if title_match else ''
        text = html_to_text(kattis_body(page))
    else:
        raise ValueError('unsupported judge host')
    if not title or len(text) < 150 or not re.search(r'\binput\b', text, re.I) or not re.search(r'\boutput\b', text, re.I):
        raise ValueError('incomplete/gated statement; retain resource link')
    return {'id': f'{platform}-{slugify(code)}', 'platform': platform,
            'title': title, 'slug': slugify(code), 'source_url': url,
            'source_topic': topic, 'source_text': text, 'source_tags': [],
            'difficulty': None, 'rating': None, **extras}
