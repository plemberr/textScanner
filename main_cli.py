import argparse
from src.cli import process_folder

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    process_folder(args.input, args.output)

if __name__ == "__main__":
    main()
