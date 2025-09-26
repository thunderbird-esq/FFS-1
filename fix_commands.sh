#!/bin/bash
# fix_commands.sh - Add $ARGUMENTS to all command files

cd .claude/commands/

# Create proper command scripts from markdown files
for md_file in *.md; do
  if [ -f "$md_file" ]; then
    # Extract base name without extension
    base_name="${md_file%.md}"
    script_name="${base_name}.sh"
    
    # Create executable script with $ARGUMENTS
    cat > "$script_name" << 'EOF'
#!/bin/bash
# Auto-generated command script

# Capture all arguments
ARGS="$@"

# Default behavior - pass all arguments through
if [ -z "$ARGS" ]; then
  echo "No arguments provided. Usage: $0 [arguments]"
  exit 1
fi

# Execute the command logic with $ARGUMENTS
exec_command() {
  # Add your command logic here
  echo "Executing with arguments: $ARGUMENTS"
}

# Main execution
exec_command $ARGUMENTS
EOF
    
    # Make executable
    chmod +x "$script_name"
    echo "Created: $script_name"
  fi
done

echo "Command scripts fixed with \$ARGUMENTS placeholder"
