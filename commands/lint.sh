#!/bin/bash
# Run complete Python linting and formatting

TOOLS="${1:-all}"
TARGET="${2:-.}"

# Function to run black
run_black() {
    echo "Running Black formatter..."
    if command -v black &> /dev/null; then
        black "$TARGET" --line-length 100 --skip-string-normalization $ARGUMENTS
    else
        echo "Black not installed. Installing..."
        pip install black
        black "$TARGET" --line-length 100 --skip-string-normalization $ARGUMENTS
    fi
}

# Function to run flake8
run_flake8() {
    echo "Running flake8 linter..."
    if command -v flake8 &> /dev/null; then
        flake8 "$TARGET" --max-line-length=100 --extend-ignore=E203,W503 --statistics $ARGUMENTS
    else
        echo "flake8 not installed. Installing..."
        pip install flake8
        flake8 "$TARGET" --max-line-length=100 --extend-ignore=E203,W503 --statistics $ARGUMENTS
    fi
}

# Function to run isort
run_isort() {
    echo "Running isort import sorter..."
    if command -v isort &> /dev/null; then
        isort "$TARGET" --profile black --line-length 100 $ARGUMENTS
    else
        echo "isort not installed. Installing..."
        pip install isort
        isort "$TARGET" --profile black --line-length 100 $ARGUMENTS
    fi
}

# Function to run pylint
run_pylint() {
    echo "Running pylint..."
    if command -v pylint &> /dev/null; then
        pylint "$TARGET" --max-line-length=100 --fail-under=8.0 $ARGUMENTS || true
    else
        echo "pylint not installed. Installing..."
        pip install pylint
        pylint "$TARGET" --max-line-length=100 --fail-under=8.0 $ARGUMENTS || true
    fi
}

# Function to run mypy
run_mypy() {
    echo "Running mypy type checker..."
    if command -v mypy &> /dev/null; then
        mypy "$TARGET" --ignore-missing-imports --strict-optional $ARGUMENTS || true
    else
        echo "mypy not installed. Installing..."
        pip install mypy
        mypy "$TARGET" --ignore-missing-imports --strict-optional $ARGUMENTS || true
    fi
}

# Main execution
case "$TOOLS" in
    black)
        run_black
        ;;
    flake8)
        run_flake8
        ;;
    isort)
        run_isort
        ;;
    pylint)
        run_pylint
        ;;
    mypy)
        run_mypy
        ;;
    all)
        echo "Running all linting tools on $TARGET..."
        echo "=================================="
        run_isort
        echo ""
        run_black
        echo ""
        run_flake8
        echo ""
        run_pylint
        echo ""
        run_mypy
        echo "=================================="
        echo "Linting complete!"
        ;;
    *)
        echo "Unknown tool: $TOOLS"
        echo "Available: all, black, flake8, isort, pylint, mypy"
        exit 1
        ;;
esac

# Generate summary report if requested
if [[ "$ARGUMENTS" == *"--report"* ]]; then
    echo ""
    echo "Generating linting report..."
    {
        echo "# Linting Report"
        echo "Date: $(date)"
        echo "Target: $TARGET"
        echo ""
        echo "## Results"
        flake8 "$TARGET" --statistics --count 2>&1 || true
    } > linting_report.md
    echo "Report saved to linting_report.md"
fi
