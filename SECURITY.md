# Evidence handling

No network access, device credentials or automatic command execution are part of this tool. Only explicitly selected local UTF-8 exports are packaged. Input and bundle manifests are treated as untrusted structured data; paths, bounds, references and filesystem entry types are checked.

**This is not a redactor.** Export contents are preserved byte for byte. Labels, findings and relative source paths are retained in assessment metadata. A valid hash or a complete collection result does not make a package suitable for public sharing. Review actual contents before publishing a real assessment.

The examples contain synthetic data and previously published, attributed laboratory reports. Do not paste private client exports, credentials or tokens into public issues. Use a minimal synthetic reproducer and report the tool version.

Reports escape supplied text, and coverage CSV fields receive a formula-prefix guard. Treat the attached raw text files as untrusted source material, not executable instructions. Work in a directory not writable by untrusted concurrent users.

Verification establishes internal consistency against an unsigned manifest. It is not authentication, a signature, a health test, a security audit or a compliance certification. A file and manifest modified together can pass, by design; document trusted provenance separately.
