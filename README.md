# dtv-schedule-rss

## Release

Version tags use CalVer: `YYYY.MM.DD.N` (increment `N` for multiple releases on the same day).

After merging what you want to ship to `main`:

```bash
gh release create YYYY.MM.DD.N --generate-notes --target main
```

This creates a GitHub Release and tag. The tag triggers CD to push `ghcr.io/dmingn/dtv-schedule-rss:YYYY.MM.DD.N`.
