# Slide-to-Image-Converter Test Suite

This directory contains comprehensive tests for the slide-to-image-converter module, covering all aspects of functionality, performance, and edge cases.

## Test Structure

```
tests/
├── conftest.py                           # Pytest configuration and fixtures
├── README.md                            # This file
├── run_comprehensive_tests.py           # Test runner script
├── integration/                         # Integration tests
│   └── test_slide_to_image_converter.py # End-to-end pipeline tests
└── unit/                               # Unit tests
    ├── test_comprehensive_edge_cases.py # Edge cases and error handling
    ├── test_html_renderer.py           # HTML renderer tests
    ├── test_markdown_converter.py      # Markdown converter tests
    ├── test_performance_and_memory.py  # Performance and memory tests
    └── test_slide_processor.py         # Slide processor tests
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Core Component Tests:**
- `test_markdown_converter.py`: Tests for Markdown to HTML conversion
- `test_html_renderer.py`: Tests for HTML to PNG rendering
- `test_slide_processor.py`: Tests for the main orchestrator

**Specialized Tests:**
- `test_comprehensive_edge_cases.py`: Edge cases, error handling, boundary conditions
- `test_performance_and_memory.py`: Performance benchmarks and memory usage analysis

### 2. Integration Tests (`tests/integration/`)

**End-to-End Tests:**
- `test_slide_to_image_converter.py`: Complete pipeline testing from Markdown to PNG

## Test Features

### Comprehensive Coverage

✅ **Markdown Formatting Scenarios**
- Headers (H1-H6)
- Text formatting (bold, italic, strikethrough)
- Lists (ordered, unordered, nested)
- Code blocks (with and without syntax highlighting)
- Tables (basic and complex)
- Blockquotes (simple and nested)
- Links and references
- Unicode and special characters
- Task lists and mixed content

✅ **Image Dimensions and Browser Types**
- Multiple resolution testing (HD, Full HD, 4K, custom)
- Browser compatibility (Chromium, Firefox, WebKit)
- Custom browser arguments
- Dimension edge cases (very small, very large)

✅ **Error Handling and Edge Cases**
- Invalid input handling
- File system errors
- Browser failures and fallbacks
- JSON structure validation
- Memory management
- Concurrent processing

✅ **Performance and Memory Testing**
- Conversion speed scaling
- Template caching performance
- Browser reuse benefits
- Memory usage patterns
- Concurrent vs sequential processing
- Batch processing scalability

## Running Tests

### Quick Start

```bash
# Run all tests
python tests/run_comprehensive_tests.py --all

# Run specific test categories
python tests/run_comprehensive_tests.py --unit
python tests/run_comprehensive_tests.py --integration
python tests/run_comprehensive_tests.py --performance
python tests/run_comprehensive_tests.py --edge-cases
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/slide_to_image_converter --cov-report=html

# Run specific test files
pytest tests/unit/test_markdown_converter.py -v

# Run tests by marker
pytest -m "not integration"  # Skip integration tests
pytest -m "performance"      # Only performance tests
pytest -m "slow"            # Only slow tests

# Run with parallel execution
pytest -n auto
```

### Test Runner Options

```bash
python tests/run_comprehensive_tests.py --help
```

**Available options:**
- `--unit`: Run unit tests only
- `--integration`: Run integration tests only  
- `--performance`: Run performance tests only
- `--edge-cases`: Run edge case tests only
- `--all`: Run all tests (default)
- `--verbose`: Verbose output
- `--coverage`: Run with coverage reporting
- `--html-report`: Generate HTML coverage report
- `--parallel`: Run tests in parallel

## Test Requirements

### Basic Requirements
- Python 3.8+
- pytest
- All slide-to-image-converter dependencies

### Integration Test Requirements
- Playwright browsers installed: `playwright install`
- Sufficient system resources for browser automation

### Performance Test Requirements
- psutil (for memory monitoring): `pip install psutil`
- memory_profiler (optional): `pip install memory_profiler`

### Installing Test Dependencies

```bash
# Install basic test dependencies
pip install pytest pytest-cov pytest-asyncio

# Install integration test dependencies
pip install playwright
playwright install

# Install performance test dependencies
pip install psutil memory_profiler

# Install parallel execution support
pip install pytest-xdist
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.integration`: Tests requiring browser setup
- `@pytest.mark.performance`: Performance and benchmarking tests
- `@pytest.mark.memory`: Memory usage tests
- `@pytest.mark.slow`: Tests that may take longer to run

## Fixtures

Common test fixtures are provided in `conftest.py`:

- `temp_dir`: Temporary directory for test files
- `sample_markdown`: Sample Markdown content
- `sample_html`: Sample HTML content
- `sample_presentation_json`: Sample presentation data
- `create_test_json_file`: Helper to create test JSON files
- `complex_markdown`: Complex Markdown for stress testing

## Performance Benchmarks

Performance tests provide benchmarks for:

### Conversion Speed
- Markdown to HTML conversion scaling
- Template caching benefits
- Concurrent processing speedup

### Memory Usage
- Memory consumption during conversion
- Memory cleanup effectiveness
- Cache memory management

### Browser Performance
- Rendering speed vs image dimensions
- Browser reuse benefits
- Async vs sync performance

## Continuous Integration

The test suite is designed to work in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-cov playwright
    playwright install --with-deps chromium
    python tests/run_comprehensive_tests.py --all --coverage
```

## Troubleshooting

### Common Issues

**Browser Installation:**
```bash
# If integration tests fail with browser errors
playwright install
# or for specific browser
playwright install chromium
```

**Memory Tests:**
```bash
# If memory tests are skipped
pip install psutil
```

**Parallel Execution:**
```bash
# If parallel tests fail
pip install pytest-xdist
```

### Test Debugging

```bash
# Run with verbose output and no capture
pytest -v -s tests/unit/test_markdown_converter.py

# Run single test method
pytest tests/unit/test_markdown_converter.py::TestMarkdownConverter::test_convert_to_html_basic -v

# Debug integration tests
pytest tests/integration/ -v -s --tb=long
```

### Performance Analysis

```bash
# Run performance tests with detailed output
pytest tests/unit/test_performance_and_memory.py -v -s

# Profile memory usage
python -m memory_profiler tests/unit/test_performance_and_memory.py
```

## Contributing

When adding new tests:

1. **Use appropriate markers** for test categorization
2. **Use fixtures** from `conftest.py` for common test data
3. **Add docstrings** explaining what the test validates
4. **Handle browser dependencies** gracefully with `pytest.skip()`
5. **Include performance assertions** where appropriate
6. **Test both success and failure scenarios**

### Test Naming Convention

- `test_<functionality>_<scenario>`: Basic test naming
- `test_<component>_<edge_case>`: Edge case tests
- `test_<feature>_performance`: Performance tests
- `test_<error_type>_handling`: Error handling tests

## Coverage Goals

Target coverage areas:

- ✅ Core conversion pipeline (Markdown → HTML → PNG)
- ✅ Error handling and recovery
- ✅ Performance characteristics
- ✅ Memory management
- ✅ Concurrent processing
- ✅ Configuration handling
- ✅ File I/O operations
- ✅ Browser automation
- ✅ Template processing
- ✅ JSON validation

## Test Results

Tests generate detailed output including:
- Conversion performance metrics
- Memory usage statistics
- Browser compatibility results
- Error handling verification
- Coverage reports (when enabled)

For questions or issues with the test suite, please refer to the main project documentation or create an issue in the project repository.