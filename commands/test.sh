#!/bin/bash
# Run comprehensive Python tests

FRAMEWORK="${1:-pytest}"
TARGET="${2:-tests/}"
COVERAGE="${3:-false}"

# Function to run pytest
run_pytest() {
    echo "Running pytest..."
    if ! command -v pytest &> /dev/null; then
        echo "Installing pytest..."
        pip install pytest pytest-cov pytest-asyncio pytest-mock
    fi
    
    if [ "$COVERAGE" == "true" ] || [[ "$ARGUMENTS" == *"--cov"* ]]; then
        pytest "$TARGET" \
            --cov=app \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-report=xml \
            -v \
            $ARGUMENTS
        echo ""
        echo "Coverage report generated:"
        echo "  - HTML: htmlcov/index.html"
        echo "  - XML: coverage.xml"
    else
        pytest "$TARGET" -v $ARGUMENTS
    fi
}

# Function to run unittest
run_unittest() {
    echo "Running unittest..."
    python -m unittest discover "$TARGET" -v $ARGUMENTS
}

# Function to run Django tests
run_django() {
    echo "Running Django tests..."
    if [ -f "manage.py" ]; then
        python manage.py test "$TARGET" --verbosity=2 $ARGUMENTS
    else
        echo "Error: manage.py not found"
        exit 1
    fi
}

# Function to run nose2
run_nose2() {
    echo "Running nose2..."
    if ! command -v nose2 &> /dev/null; then
        echo "Installing nose2..."
        pip install nose2
    fi
    nose2 -v -s "$TARGET" $ARGUMENTS
}

# Main execution
case "$FRAMEWORK" in
    pytest)
        run_pytest
        ;;
    unittest)
        run_unittest
        ;;
    django)
        run_django
        ;;
    nose2)
        run_nose2
        ;;
    *)
        echo "Unknown framework: $FRAMEWORK"
        echo "Available: pytest, unittest, django, nose2"
        # Try to detect and run appropriate framework
        if [ -f "pytest.ini" ] || [ -f "setup.cfg" ] || [ -f "pyproject.toml" ]; then
            echo "Detected pytest configuration, using pytest..."
            run_pytest
        elif [ -f "manage.py" ]; then
            echo "Detected Django project, using Django test runner..."
            run_django
        else
            echo "Using unittest as default..."
            run_unittest
        fi
        ;;
esac

# Generate test report if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Tests passed successfully!"
else
    echo ""
    echo "✗ Some tests failed. Check output above."
    exit 1
fi

# Run performance benchmarks if requested
if [[ "$ARGUMENTS" == *"--benchmark"* ]]; then
    echo ""
    echo "Running performance benchmarks..."
    pytest "$TARGET" --benchmark-only --benchmark-autosave $ARGUMENTS
fi
