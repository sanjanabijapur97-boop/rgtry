# A Life I Dreamed Of

A dreamy, responsive scrapbook website for Sanjana: childhood hopes, teenage chapters, present ambitions, and a future vision board.

## Preview locally

This is a static website with no install step. From this folder, start a small local server:

```powershell
py -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000) in your browser. If `py` is unavailable, try `python -m http.server 8000`. Stop the server with `Ctrl+C`.

You can also open `index.html` directly, though a local server is recommended. Google Fonts load over the internet; system serif and sans-serif fonts are used if they are unavailable.

## Files

- `index.html` — page content and sections
- `styles.css` — layout, scrapbook styling, responsive rules, and animations
- `script.js` — scroll progress, mobile navigation, and reveal effects
