# OpenTelemetry Instrumentation Plugin for Claude Code

A Claude Code plugin that provides expert guidance for instrumenting applications with OpenTelemetry SDKs. This plugin helps developers add observability to their Java, Go, Rust, and JavaScript/TypeScript applications through traces, metrics, and logs.

## 📊 Features

- **Expert Knowledge**: Comprehensive guidance on OpenTelemetry instrumentation
- **Multi-Language Support**: Dedicated skills for Java, Go, Rust, and JavaScript/TypeScript
- **Best Practices**: Industry-standard patterns and conventions
- **Practical Examples**: Real-world code examples and patterns
- **Complete Coverage**: Manual and automatic instrumentation approaches
- **Framework Support**: Express, React, Next.js, Spring Boot, and more

## 🚀 Skills

### OpenTelemetry Java

Expert knowledge for instrumenting Java applications with OpenTelemetry, including:

- Automatic instrumentation with Java agent
- Manual instrumentation with OpenTelemetry API
- Spring Boot integration
- SDK configuration and setup
- Span creation and context propagation
- Metric collection (counters, histograms, gauges)
- Database, HTTP, and gRPC instrumentation
- Error handling and troubleshooting

### OpenTelemetry Go

Expert knowledge for instrumenting Go applications with OpenTelemetry, including:

- Manual instrumentation with OpenTelemetry Go API
- SDK configuration and initialization
- HTTP server and client instrumentation
- gRPC instrumentation
- Database instrumentation patterns
- Context propagation across goroutines
- Metric collection and recording
- Best practices for production deployments

### OpenTelemetry Rust

Expert knowledge for instrumenting Rust applications with OpenTelemetry, including:

- Manual instrumentation with OpenTelemetry Rust API
- SDK configuration and initialization
- HTTP server and client instrumentation (Axum, Actix-web, etc.)
- Integration with the `tracing` crate ecosystem
- Database instrumentation patterns (SQLx, Diesel)
- Async runtime integration (Tokio)
- Metric collection and recording
- OTLP exporters (HTTP and gRPC)
- Context propagation in async code
- Best practices for production deployments

### OpenTelemetry JavaScript

Expert knowledge for instrumenting JavaScript and TypeScript applications with OpenTelemetry, including:

- Automatic instrumentation for Node.js applications
- Manual instrumentation with OpenTelemetry JavaScript API
- Browser instrumentation for frontend applications
- React and Next.js instrumentation patterns
- Express.js and web framework instrumentation
- SDK configuration for Node.js and browsers
- HTTP, database, and GraphQL instrumentation
- Context propagation in async operations
- Metric collection and custom spans
- TypeScript support and best practices

## 📦 Installation

### From the Claude Marketplace (Recommended)

Install this plugin directly from the Claude Code marketplace:

1. Open Claude Code
2. Navigate to the Plugin Marketplace
3. Search for "OpenTelemetry Instrumentation Assistant"
4. Click "Install"

The plugin will be automatically available in all your projects.

### Manual Installation

Alternatively, you can install the plugin manually:

1. Clone this repository or download the plugin files
2. Place the `.claude` directory in your project root, or
3. Configure Claude Code to load the plugin from this repository

For more information on installing plugins, see the [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugin-marketplaces)

## 🎯 Usage

Once installed, the plugin provides expert guidance when you ask Claude about OpenTelemetry instrumentation:

**Example prompts:**
- "How do I instrument my Java Spring Boot application with OpenTelemetry?"
- "Show me how to add tracing to a Go HTTP service"
- "How do I set up OpenTelemetry in a Rust application using Axum?"
- "How do I set up OpenTelemetry in a Next.js application?"
- "How do I instrument a React application with OpenTelemetry?"
- "Show me how to add automatic instrumentation to my Node.js Express app"
- "How do I configure OpenTelemetry to export to Jaeger?"
- "What's the best way to add custom metrics to my Java application?"
- "How do I propagate trace context across microservices in Go?"
- "How do I instrument GraphQL with OpenTelemetry in Node.js?"

### Using the Instrument Command

The plugin includes an `instrument` command that guides you through the complete instrumentation process:

```
/instrument
```

When you run this command, Claude will:
1. Analyze your codebase to identify the programming language
2. Automatically activate the appropriate OpenTelemetry skill (Java, Go, Rust, or JavaScript/TypeScript)
3. Review your application architecture
4. Identify key instrumentation points (HTTP endpoints, database queries, external services, etc.)
5. Provide specific recommendations for automatic and manual instrumentation
6. Generate tailored code examples for your application
7. Guide you through testing and validation

Learn more about Claude Code skills at [https://code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)

## 📚 Plugin Structure

```
.claude/
├── plugin.json                      # Plugin manifest
└── skills/
    ├── opentelemetry-java/          # Java skill
    │   ├── skill.json               # Java skill configuration
    │   ├── knowledge.md             # Java instrumentation guide
    │   └── examples.md              # Java code examples
    ├── opentelemetry-go/            # Go skill
    │   ├── skill.json               # Go skill configuration
    │   ├── knowledge.md             # Go instrumentation guide
    │   └── examples.md              # Go code examples
    ├── opentelemetry-rust/          # Rust skill
    │   ├── skill.json               # Rust skill configuration
    │   ├── knowledge.md             # Rust instrumentation guide
    │   └── examples.md              # Rust code examples
    └── opentelemetry-js/            # JavaScript/TypeScript skill
        ├── skill.json               # JavaScript skill configuration
        ├── knowledge.md             # JavaScript instrumentation guide
        └── examples.md              # JavaScript code examples
```

## 🤖 GitHub Actions Integration

You can use this plugin in GitHub Actions workflows to automate observability reviews and ensure consistent instrumentation practices across your codebase.

### Automated Observability Reviews

The plugin can help review pull requests for observability best practices, ensuring that:
- New endpoints and services are properly instrumented
- Trace context is propagated correctly
- Metrics and logs are added where appropriate
- Instrumentation follows OpenTelemetry best practices

### Example GitHub Actions Workflow

Here's an example of how you could integrate the plugin into a GitHub Actions workflow. Note: This assumes a hypothetical Claude Code GitHub Action integration. Adapt this example to your specific CI/CD setup:

Create a `.github/workflows/otel-review.yml` file in your repository:

```yaml
name: OpenTelemetry Review

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  otel-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Review Observability Changes
        uses: anthropics/claude-code-action@v1
        with:
          api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          plugin: cedricziel/claude-otel-plugin
          prompt: |
            Review this pull request for observability best practices:
            
            1. Check if new HTTP endpoints, database queries, or external service calls are properly instrumented
            2. Verify trace context propagation in async operations and across service boundaries
            3. Ensure appropriate metrics are collected for business and technical operations
            4. Validate error handling and logging practices
            5. Suggest improvements for observability coverage
            
            Use the opentelemetry-java or opentelemetry-go skills as appropriate for the codebase.
            Provide specific, actionable feedback with code examples.
```

### Environment Setup

To use Claude in GitHub Actions:

1. **Get an Anthropic API key**: Sign up at [https://console.anthropic.com](https://console.anthropic.com)
2. **Add the API key to your repository secrets**:
   - Go to your repository Settings → Secrets and variables → Actions
   - Create a new secret named `ANTHROPIC_API_KEY`
   - Paste your Anthropic API key

3. **Reference this plugin** in your workflow using `plugin: cedricziel/claude-otel-plugin`

### Activating Skills

The plugin's skills are automatically activated when Claude detects relevant context:

- **opentelemetry-java**: Activated when working with Java files (`.java`, `pom.xml`, `build.gradle`)
- **opentelemetry-go**: Activated when working with Go files (`.go`, `go.mod`)
- **opentelemetry-rust**: Activated when working with Rust files (`.rs`, `Cargo.toml`)
- **opentelemetry-js**: Activated when working with JavaScript/TypeScript files (`.js`, `.ts`, `package.json`)

You can also explicitly invoke skills in your prompts:
```
Using the opentelemetry-java skill, review this Spring Boot application for instrumentation gaps.
```

For more information on skills and commands, see the [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills).

## 🔧 What's Included

### Java Instrumentation Knowledge

- Java agent setup and configuration
- Manual instrumentation with OpenTelemetry API
- Maven and Gradle dependencies
- Span creation and management
- Metric recording (counters, histograms)
- Spring Boot integration
- Database instrumentation
- HTTP client/server instrumentation
- Context propagation patterns
- Error handling and debugging

### Go Instrumentation Knowledge

- OpenTelemetry SDK initialization
- Tracer and meter setup
- HTTP middleware instrumentation
- gRPC interceptors
- Database query instrumentation
- Context propagation in goroutines
- Metric collection patterns
- Best practices for production
- Troubleshooting and debugging

### Rust Instrumentation Knowledge

- OpenTelemetry SDK initialization
- Tracer and meter setup
- HTTP server instrumentation (Axum, Actix-web)
- HTTP client instrumentation (reqwest)
- Database instrumentation (SQLx, Diesel)
- Integration with `tracing` crate
- Context propagation in async code
- Metric collection patterns
- OTLP exporters (HTTP and gRPC)
- Best practices for Rust applications
- Troubleshooting and debugging

### JavaScript Instrumentation Knowledge

- Node.js automatic and manual instrumentation
- Browser-based instrumentation
- React component tracing
- Next.js instrumentation hooks
- Express.js middleware
- TypeScript configuration
- NPM package dependencies
- Database instrumentation (PostgreSQL, MongoDB, MySQL)
- GraphQL server instrumentation
- Context propagation in async/await
- Custom metrics and spans
- Sampling strategies
- Production best practices

## 🎓 Supported Use Cases

- Adding observability to new applications
- Migrating from other tracing solutions
- Implementing distributed tracing
- Setting up metrics collection
- Configuring exporters (OTLP, Jaeger, Prometheus)
- Debugging performance issues
- Understanding trace context propagation
- Implementing best practices for observability

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests with:

- Additional examples
- Updated best practices
- New framework integrations
- Bug fixes or corrections
- Documentation improvements

### Plugin Validation

Before submitting changes, you can validate the plugin structure using the included validation script:

```bash
python3 validate-marketplace.py
```

This will check that all required files and metadata are present for marketplace publishing.

## 📦 Marketplace Publishing

This plugin is available on the Claude Code marketplace. The plugin structure follows the [Claude Code Plugin Marketplace](https://code.claude.com/docs/en/plugin-marketplaces) specifications with:

- ✓ Complete marketplace metadata in `plugin.json`
- ✓ MIT License for open-source distribution
- ✓ Comprehensive documentation
- ✓ Four specialized skills for different programming languages
- ✓ Custom `/instrument` command for guided instrumentation

## 📖 Resources

- [OpenTelemetry Official Documentation](https://opentelemetry.io/docs/)
- [OpenTelemetry Java](https://github.com/open-telemetry/opentelemetry-java)
- [OpenTelemetry Go](https://github.com/open-telemetry/opentelemetry-go)
- [OpenTelemetry Rust](https://github.com/open-telemetry/opentelemetry-rust)
- [OpenTelemetry JavaScript](https://github.com/open-telemetry/opentelemetry-js)
- [OpenTelemetry Specification](https://github.com/open-telemetry/opentelemetry-specification)

## 📄 License

This plugin is available under the MIT License. See the [LICENSE](LICENSE) file for full details.

## 🙏 Acknowledgments

Built on the excellent work of the OpenTelemetry community and based on official OpenTelemetry documentation and best practices.