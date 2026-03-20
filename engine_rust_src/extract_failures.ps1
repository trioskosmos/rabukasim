$text = [System.IO.File]::ReadAllText('all_tests_full_output.txt', [System.Text.Encoding]::Unicode)
$start = $text.IndexOf('failures:')
if ($start -ge 0) {
    $details = $text.Substring($start)
    $details | Out-File -FilePath 'test_failure_details.txt' -Encoding utf8
} else {
    'No failures found or format unexpected' | Out-File -FilePath 'test_failure_details.txt'
}
