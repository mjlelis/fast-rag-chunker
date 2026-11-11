fn main() {
    println!("cargo:rerun-if-changed=c_legacy/chunker.c");
    println!("cargo:rerun-if-changed=c_legacy/chunker.h");
    println!("cargo:rerun-if-changed=c_legacy/fastcdc.c");
    println!("cargo:rerun-if-changed=c_legacy/fastcdc.h");
    println!("cargo:rerun-if-changed=c_legacy/test_v2_caller.c");

    cc::Build::new()
        .file("c_legacy/fastcdc.c")
        .file("c_legacy/chunker.c")
        .file("c_legacy/test_v2_caller.c")
        .include("c_legacy")
        .compile("fastcdc_c_legacy");
}
