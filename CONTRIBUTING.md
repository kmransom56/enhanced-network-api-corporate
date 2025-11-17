# Contributing to Enhanced Network API Builder - Corporate Edition

We welcome contributions to make this the best corporate network API builder available!

## 🤝 How to Contribute

### 1. Fork and Clone
```bash
git fork https://github.com/your-username/enhanced-network-api-corporate.git
git clone https://github.com/your-username/enhanced-network-api-corporate.git
cd enhanced-network-api-corporate
```

### 2. Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### 3. Make Changes
- Create a feature branch: `git checkout -b feature/your-feature`
- Make your changes
- Add tests for new functionality
- Ensure all tests pass: `pytest`
- Run linting: `black src/ && flake8 src/`

### 4. Submit Pull Request
- Push to your fork: `git push origin feature/your-feature`
- Create pull request from your fork to main repository
- Include detailed description of changes
- Reference any related issues

## 🏗️ Areas for Contribution

### Corporate Network Features
- **Additional SSL Interception Support**: New corporate SSL appliances
- **Proxy Authentication Methods**: NTLM, Kerberos, SAML
- **Certificate Discovery**: New certificate sources and formats
- **Environment Detection**: Additional corporate network indicators

### API Platform Support
- **New API Platforms**: Additional network device APIs
- **Enhanced Documentation**: Improved API endpoint documentation
- **Authentication Methods**: New authentication patterns
- **Error Handling**: Better error detection and recovery

### Air-Gapped Deployments
- **Package Optimization**: Smaller, more efficient packages
- **Platform Support**: Additional operating system support
- **Security Enhancements**: Enhanced integrity verification
- **Documentation**: Improved air-gapped deployment guides

### Testing and Quality
- **Corporate Environment Testing**: Tests with real corporate tools
- **SSL/Proxy Testing**: Comprehensive network testing
- **Documentation**: Examples, guides, and troubleshooting
- **Performance**: Optimization and benchmarking

## 🧪 Testing Guidelines

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_corporate_ssl.py
pytest tests/test_network_helpers.py
pytest tests/test_api_documentation.py

# Run with coverage
pytest --cov=enhanced_network_api tests/
```

### Corporate Environment Testing
To test corporate features, you may need:
- Corporate SSL certificates (Zscaler, Blue Coat, etc.)
- Corporate proxy configuration
- VPN access to corporate network
- Test FortiManager/Meraki instances

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing  
- **Corporate Tests**: Real corporate environment testing
- **Security Tests**: SSL, proxy, certificate testing
- **Air-Gapped Tests**: Offline functionality testing

## 📝 Documentation Standards

### Code Documentation
- **Docstrings**: All public functions and classes
- **Type Hints**: Use type hints for all function signatures
- **Comments**: Explain complex logic and corporate-specific handling
- **Examples**: Include usage examples in docstrings

### User Documentation
- **Guides**: Step-by-step instructions
- **Examples**: Working code examples
- **Troubleshooting**: Common issues and solutions
- **Corporate Context**: Explain why features are needed

## 🔒 Security Considerations

### Corporate Security
- **Certificate Handling**: Secure certificate storage and validation
- **Credential Management**: Never hardcode credentials
- **Logging**: Audit trails without exposing sensitive data
- **Compliance**: Consider SOX, HIPAA, PCI-DSS requirements

### Code Security
- **Input Validation**: Validate all user inputs
- **SSL/TLS**: Use secure defaults, avoid SSL bypass in production
- **Dependencies**: Keep dependencies updated and secure
- **Secrets**: Never commit secrets or credentials

## 📋 Code Standards

### Python Style
- **PEP 8**: Follow Python style guide
- **Black**: Use black code formatter
- **Flake8**: Use flake8 for linting
- **Type Hints**: Use type hints (mypy compatible)

### Git Practices
- **Commit Messages**: Clear, descriptive commit messages
- **Branch Naming**: feature/, bugfix/, docs/, security/
- **Small Commits**: Atomic commits with single purpose
- **No Secrets**: Never commit secrets, certificates, or credentials

## 🏷️ Issue Labels

We use these labels to categorize issues:
- **corporate**: Corporate network features
- **ssl**: SSL/TLS certificate handling
- **proxy**: Proxy and network configuration
- **airgapped**: Air-gapped deployment
- **documentation**: Documentation improvements
- **bug**: Bug reports
- **enhancement**: New features
- **security**: Security-related issues
- **testing**: Testing improvements

## 🎯 Contribution Ideas

### Quick Wins (Good First Issues)
- Documentation improvements
- Additional certificate discovery locations
- More corporate environment detection
- Additional SSL appliance support
- Example applications and tutorials

### Medium Projects
- New API platform integration
- Enhanced proxy authentication
- Improved air-gapped packaging
- Corporate compliance features
- Performance optimizations

### Large Projects
- GUI for corporate configuration
- Corporate network topology discovery
- Advanced certificate management
- Multi-platform deployment tools
- Enterprise management dashboard

## 📞 Community

### Getting Help
- **GitHub Discussions**: Ask questions and share ideas
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check existing documentation first

### Communication
- **Be Respectful**: Follow code of conduct
- **Be Helpful**: Help others in discussions
- **Be Clear**: Provide clear problem descriptions
- **Be Patient**: Maintainers are volunteers

## 🏆 Recognition

Contributors will be recognized:
- **README Contributors**: Listed in main README
- **Release Notes**: Mentioned in release notes
- **Corporate Hall of Fame**: Special recognition for corporate features

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Enhanced Network API Builder - Corporate Edition!**