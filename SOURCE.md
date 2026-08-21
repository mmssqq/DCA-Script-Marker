# Source code for distributed betas

DCA Script Marker is licensed under GNU AGPL version 3 or later.

Every beta release provides a separate archive named like
`DCA-Script-Marker-v0.9.0-beta.1-source.zip` beside the macOS DMG. That archive
is the authoritative corresponding source for the binary released with it. It
includes:

- the Python marking engine and tests;
- the active SwiftUI macOS project and app assets;
- the build, verification, signing, and packaging scripts;
- the finalized blank DCA State template;
- the documentation, licence, and third-party notices; and
- the exact upstream dependency source archives used for the bundled runtime,
  identified by SHA-256 checksums.

The source archive contains `SOURCE_MANIFEST.sha256`. From its extracted root,
verify it with:

```sh
shasum -a 256 -c SOURCE_MANIFEST.sha256
```

The project home is <https://github.com/mmssqq/DCA-Script-Marker>. When a beta
is published there, download the source ZIP from the same GitHub Release as the
DMG. The release tag and accompanying source archive should be used instead of
a later, mutable branch.

Build instructions are in [packaging/macos/README.md](packaging/macos/README.md).
