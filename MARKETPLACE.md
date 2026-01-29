# Marketplace Submission Guide

This document provides information about the marketplace-ready structure of this Claude Code plugin.

## Plugin Structure

The plugin follows the Claude Code marketplace specifications with the following structure:

```
claude-otel-plugin/
├── .claude/
│   ├── plugin.json          # Main plugin manifest with marketplace metadata
│   └── skills/
│       ├── opentelemetry-java/
│       │   ├── SKILL.md     # Java skill knowledge base
│       │   └── references/
│       │       └── examples.md
│       ├── opentelemetry-go/
│       │   ├── SKILL.md     # Go skill knowledge base
│       │   └── references/
│       │       └── examples.md
│       ├── opentelemetry-rust/
│       │   ├── SKILL.md     # Rust skill knowledge base
│       │   └── references/
│       │       └── examples.md
│       └── opentelemetry-js/
│           ├── SKILL.md     # JavaScript/TypeScript skill knowledge base
│           └── references/
│               └── examples.md
├── LICENSE                   # MIT License
├── README.md                 # Plugin documentation
└── validate-marketplace.py   # Validation script
```

## Marketplace Metadata

The `plugin.json` file includes all required marketplace metadata:

### Required Fields
- ✅ `name`: "opentelemetry-instrumentation"
- ✅ `version`: "1.0.0"
- ✅ `description`: Full plugin description
- ✅ `author`: Author name and URL

### Marketplace Section
- ✅ `displayName`: "OpenTelemetry Instrumentation Assistant"
- ✅ `shortDescription`: Brief description for marketplace listing
- ✅ `category`: "observability"
- ✅ `tags`: Comprehensive list of relevant tags
- ✅ `icon`: "📊" (emoji icon)
- ✅ `keywords`: SEO-optimized keywords for discoverability

### Additional Metadata
- ✅ `license`: "MIT"
- ✅ `repository`: GitHub repository information
- ✅ `homepage`: Plugin homepage URL

## Skills

The plugin provides four specialized skills:

1. **opentelemetry-java**: Expert knowledge for Java applications
2. **opentelemetry-go**: Expert knowledge for Go applications
3. **opentelemetry-rust**: Expert knowledge for Rust applications
4. **opentelemetry-js**: Expert knowledge for JavaScript/TypeScript applications

Each skill includes:
- Main knowledge base (SKILL.md)
- Reference examples
- Best practices and patterns

## Commands

The plugin provides a custom `/instrument` command that:
- Analyzes project structure
- Identifies programming language
- Activates appropriate skill
- Guides through instrumentation process
- Provides tailored code examples

## Installation

### For Users (Marketplace)

Users can install this plugin directly from the Claude Code marketplace:

1. Open Claude Code
2. Navigate to Plugin Marketplace
3. Search for "OpenTelemetry Instrumentation Assistant"
4. Click "Install"

### For Developers (Manual)

Developers can install the plugin manually for testing:

1. Clone the repository
2. Copy the `.claude` directory to your project
3. Claude Code will automatically detect and load the plugin

## Validation

Run the validation script to ensure marketplace compliance:

```bash
python3 validate-marketplace.py
```

This checks:
- ✅ LICENSE file exists
- ✅ README.md exists
- ✅ plugin.json exists and is valid JSON
- ✅ All required metadata fields are present
- ✅ Marketplace section is complete
- ✅ All skills have required files

## Publishing

To publish this plugin to the Claude Code marketplace:

1. Ensure all validation checks pass
2. Create a release on GitHub with version tag (e.g., v1.0.0)
3. Submit to Claude Code marketplace following their submission process
4. Reference: https://code.claude.com/docs/

## Versioning

The plugin follows semantic versioning:
- Major version: Breaking changes
- Minor version: New features (backward compatible)
- Patch version: Bug fixes

Current version: **1.0.0**

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/cedricziel/claude-otel-plugin/issues
- GitHub Discussions: https://github.com/cedricziel/claude-otel-plugin/discussions
