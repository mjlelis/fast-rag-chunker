fn main() {
    println!("cargo:rerun-if-changed=c_legacy/chunker.c");
    println!("cargo:rerun-if-changed=c_legacy/chunker.h");
    println!("cargo:rerun-if-changed=c_legacy/fastcdc.c");
    println!("cargo:rerun-if-changed=c_legacy/fastcdc.h");

    cc::Build::new()
        .file("c_legacy/fastcdc.c")
        .file("c_legacy/chunker.c")
        .include("c_legacy")
        .compile("fastcdc_c_legacy");
}
