# Support

## Where to Get Help

**Do not open issues for general support questions.**

### Documentation

- [README](https://github.com/Delqhi/upgraded-opencode-stack/blob/main/README.md) - Quick start and features
- [OCI VM Architecture](https://github.com/Delqhi/upgraded-opencode-stack/blob/main/docs/oci-vm-architecture.md) - Detailed system design
- [Fixes Log](https://github.com/Delqhi/upgraded-opencode-stack/blob/main/FIXES_2026-04-11.md) - Bug fixes and RCA
- [Contributing](https://github.com/Delqhi/upgraded-opencode-stack/blob/main/CONTRIBUTING.md) - How to contribute

### Bug Reports

If you found a bug, please open an issue with:

1. Clear description of the problem
2. Steps to reproduce
3. Expected vs actual behavior
4. Environment details (OS, OpenCode version, etc.)

### Feature Requests

For feature requests, please:

1. Check if it already exists in [Issues](https://github.com/Delqhi/upgraded-opencode-stack/issues)
2. Open a new issue with the "enhancement" label
3. Describe the problem you're trying to solve

### Common Issues

**Q: sin-sync fails with "No space left on device"**
A: The OCI VM disk is full. Run cleanup on the VM: `sudo find /tmp -name '*.so' -mtime +0 -delete`

**Q: Qwen model returns "invalid access token"**
A: Run `opencode providers login --provider qwen --method "Qwen OAuth"` to re-authenticate.

**Q: Skills not found after install**
A: Run `./install.sh` again to ensure all skills are synced.

### Contact

For private inquiries: support@example.com
