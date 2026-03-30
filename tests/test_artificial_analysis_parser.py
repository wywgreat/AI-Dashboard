from collectors.artificial_analysis.parser import TABLES, extract_candidates_from_html, parse_from_html, parse_from_json_payload


def test_parse_from_embedded_json_payload():
    html = '''
    <html><body>
      <script type="application/json">{"data":[{"model":"M1","provider":"P1","country":"US","score":88.8,"cost":0.2}]}</script>
    </body></html>
    '''
    payloads = extract_candidates_from_html(html)
    rows = parse_from_json_payload(TABLES["intelligence-index"], payloads)
    assert len(rows) == 1
    assert rows[0].model == "M1"
    assert rows[0].intelligence_score == 88.8


def test_parse_html_fallback_table():
    html = '''
    <table>
      <tr><th>Model</th><th>Provider</th><th>Country</th><th>Score</th><th>Cost</th></tr>
      <tr><td>M2</td><td>P2</td><td>CN</td><td>90.1</td><td>0.5</td></tr>
    </table>
    '''
    rows = parse_from_html(TABLES["intelligence-vs-cost"], html)
    assert len(rows) == 1
    assert rows[0].provider == "P2"
    assert rows[0].cost_metric == 0.5
