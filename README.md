# OpenTelemetry Instrumentation Plugin for Claude Code

A Claude Code plugin that provides expert guidance for instrumenting applications with OpenTelemetry SDKs. This plugin helps developers add observability to their Java and Go applications through traces, metrics, and logs.

## 📊 Features

- **Expert Knowledge**: Comprehensive guidance on OpenTelemetry instrumentation
- **Multi-Language Support**: Dedicated skills for Java and Go
- **Best Practices**: Industry-standard patterns and conventions
- **Practical Examples**: Real-world code examples and patterns
- **Complete Coverage**: Manual and automatic instrumentation approaches

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

## 📦 Installation

To use this plugin in Claude Code:

1. Clone this repository or download the plugin files
2. Place the `.claude` directory in your project root, or
3. Configure Claude Code to load the plugin from this repository

## 🎯 Usage

Once installed, the plugin provides expert guidance when you ask Claude about OpenTelemetry instrumentation:

**Example prompts:**
- "How do I instrument my Java Spring Boot application with OpenTelemetry?"
- "Show me how to add tracing to a Go HTTP service"
- "How do I configure OpenTelemetry to export to Jaeger?"
- "What's the best way to add custom metrics to my Java application?"
- "How do I propagate trace context across microservices in Go?"

## 📚 Plugin Structure

```
.claude/
├── plugin.json                      # Plugin manifest
└── skills/
    ├── opentelemetry-java/          # Java skill
    │   ├── skill.json               # Java skill configuration
    │   ├── knowledge.md             # Java instrumentation guide
    │   └── examples.md              # Java code examples
    └── opentelemetry-go/            # Go skill
        ├── skill.json               # Go skill configuration
        ├── knowledge.md             # Go instrumentation guide
        └── examples.md              # Go code examples
```

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

## 📖 Resources

- [OpenTelemetry Official Documentation](https://opentelemetry.io/docs/)
- [OpenTelemetry Java](https://github.com/open-telemetry/opentelemetry-java)
- [OpenTelemetry Go](https://github.com/open-telemetry/opentelemetry-go)
- [OpenTelemetry Specification](https://github.com/open-telemetry/opentelemetry-specification)

## 📄 License

This plugin is provided as-is for use with Claude Code. Please refer to the LICENSE file for details.

## 🙏 Acknowledgments

Built on the excellent work of the OpenTelemetry community and based on official OpenTelemetry documentation and best practices.