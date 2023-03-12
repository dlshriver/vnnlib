#!/bin/sh

set -e

command=""

print_usage() {
    echo "Usage: style.sh [-h] [--check] [--format]"
    echo ""
    echo "optional arguments:"
    echo "  -h, --help            show this help message and exit"
    echo "  --check               run the style checkers"
    echo "  --format              run the style formatters"
}

while [ -n "$1" ]; do # while loop starts
    case "$1" in
    -h | --help)
        print_usage
        exit 0
        ;;
    --check)
        command="check"
        ;;
    --format)
        command="format"
        ;;
    *)
        echo "Option $1 not recognized"
        print_usage
        exit 1
        ;;
    esac
    shift
done

if [ -x $command ]; then
    echo "At least 1 command must be provided."
    print_usage
    exit 1
fi

if [ "$command" = "check" ]; then
    black --check vnnlib tests
    isort --check --profile=black vnnlib tests
elif [ "$command" = "format" ]; then
    black vnnlib tests
    isort --profile=black vnnlib tests
fi
