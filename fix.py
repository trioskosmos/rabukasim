import os
filepath = "engine_rust_src/src/qa_verification_tests.rs"
with open(filepath, "r") as f:
    text = f.read()

# Let's just run them directly by matching exactly how other tests in this file are done!
# Find the start of `mod tests {`
start = text.find("mod tests {")
# I'll strip my added tests at the end and re-insert them right after `mod tests {`.
end_idx = text.find("    #[test]\n    pub fn test_q73_reveal_until_refresh()")
if end_idx != -1:
    my_tests = text[end_idx:].rstrip()
    if my_tests.endswith("}"):
        my_tests = my_tests[:-1]
    if my_tests.endswith("}"):
        my_tests = my_tests[:-1]

    text = text[:end_idx]

    # insert my_tests right after mod tests {
    insert_pos = start + len("mod tests {")
    text = text[:insert_pos] + "\n" + my_tests + "\n" + text[insert_pos:]

    # clean up any pub fn
    text = text.replace("pub fn test_q73", "fn test_q73")
    text = text.replace("pub fn test_q102", "fn test_q102")

    with open(filepath, "w") as f:
        f.write(text)
