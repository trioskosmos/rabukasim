fn main() {
    // Tell Cargo to rerun this script if static_content changes
    println!("cargo:rerun-if-changed=static_content");
    println!("cargo:rerun-if-changed=static_content/js");
    println!("cargo:rerun-if-changed=static_content/css");
    println!("cargo:rerun-if-changed=static_content/index.html");
}
