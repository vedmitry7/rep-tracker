# JSON import format

Rep Tracker accepts UTF-8 `.json` files in this version 1 format:

```json
{
  "version": 1,
  "exercises": [
    {
      "name": "Pull-ups",
      "days": [
        {
          "date": "2026-08-01",
          "entries": [
            [10],
            [8],
            [10, 10, 10, 8]
          ]
        },
        {
          "date": "2026-08-02",
          "entries": [[12, 11, 9]]
        }
      ]
    }
  ]
}
```

The nesting is `exercises → days → entries`. Every array inside `entries` is
one workout entry: `[10]` creates one entry with one set, while
`[10, 10, 10, 8]` creates one entry with four sets. All entries under a day use
that day's `date`. The system assigns `created_at` when the import is applied.

Exercise names are matched after trimming and case normalization. Merge keeps
all existing history and adds the imported entries. Importing the same file
with Merge more than once may therefore create duplicate entries. Replace
keeps each matching exercise but permanently deletes its existing history
before adding the imported entries. New exercises are created with either
strategy.
