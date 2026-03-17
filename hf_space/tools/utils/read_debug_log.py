def main():
    try:
        with open("strict_debug_log.txt", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "DEBUG:" in line:
                    print(line.strip())
    except Exception as e:
        print(f"Error reading log: {e}")


if __name__ == "__main__":
    main()
