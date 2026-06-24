# PDF Quality Gate

Use this before exporting Korean business reports to PDF.

## Content

- Markdown source is final and reviewed first.
- Executive summary, recommendation, assumptions, source notes, and next actions are present.
- Tables fit the page width or are split into smaller tables.
- No narrative sentences use plain endings such as `한다`, `이다`, `필요하다`, or `권고한다`.

## Layout

- White background and business-report style.
- A4 portrait by default unless the user requests slides.
- Korean font renders cleanly, preferably Pretendard, Noto Sans KR, or a project-approved font.
- Page breaks do not split headings from their first paragraph.
- Charts, tables, and captions are readable at 100% zoom.

## Verification

- Render page images and inspect first, middle, and last pages.
- Check that no text overlaps or clips.
- Confirm links, dates, source notes, and version labels are visible.
- Store PDF under `business/<slug>/exports/` and keep Markdown as source of truth.
