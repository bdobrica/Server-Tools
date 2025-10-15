# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-15

### Added
- Initial release of nginx-njs24 container
- Node.js 24 with TypeScript support
- Nginx reverse proxy with SSL termination
- Automatic TypeScript compilation on startup
- Persistent node_modules support
- Environment variable configuration for Node.js port and SSL certificates
- Health check endpoint at /health
- Static file serving optimization
- Gzip compression for web assets

### Features
- TypeScript compilation from index.ts to JavaScript
- Automatic dependency installation via npm
- SSL/TLS support with configurable certificates
- Nginx reverse proxy to Node.js backend
- Production-ready security headers
- Cache optimization for static assets
- Error handling and validation
