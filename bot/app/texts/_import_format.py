"""Canonical import-format example shared by every locale.

JSON keys and example values are part of the public import contract, not
translatable UI copy. Keep this block in English and use it verbatim.
"""

IMPORT_JSON_EXAMPLE = """<b>File structure and example</b>
<pre><code>{
  "version": 1,
  "exercises": [
    {
      "name": "Pull-ups",
      "days": [
        {
          "date": "2026-08-01",
          "entries": [[10], [8, 7]]
        }
      ]
    }
  ]
}</code></pre>"""
