# Rust Test Explorer Skill

This skill provides a standardized workflow for discovering, filtering, and running Rust tests within the `engine_rust_src` project.

## Workflow

### 1. Discovering Tests
To get a full list of all registered tests from the cargo test runner:
```powershell
# Run from engine_rust_src directory
cargo test -- --list
```

To find the actual source code location of tests:
```powershell
Get-ChildItem -Path src -Filter *.rs -Recurse | Select-String -Pattern "fn test_"
```

### 2. Filtering and Exporting
To generate a clean, unique list of test names to a file:
```powershell
Get-ChildItem -Path src -Filter *.rs -Recurse | Select-String -Pattern "fn test_" | ForEach-Object { $_.Line.Trim() -replace '\{', '' -replace 'pub ', '' } | Sort-Object -Unique | Out-File -FilePath all_rust_tests.txt -Encoding utf8
```

### 3. Running Specific Tests
To run a specific test by name:
```powershell
cargo test -- <test_name>
```

To run all tests in a specific module:
```powershell
cargo test -- <module_name>::
```

### 4. Capturing Output
Always redirect output for analysis when debugging. Use `Out-File` with `-Encoding utf8` to handle Japanese characters correctly on Windows PowerShell:
```powershell
cargo test -- <test_name> --nocapture 2>&1 | Out-File -FilePath ../reports/test_output.txt -Encoding utf8
```

## Tips
- Use `--nocapture` to see `println!` output during test runs.
- If a test requires specific environment variables or data files, ensure they are accessible from the `engine_rust_src` directory.
