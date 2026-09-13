use std::process::{Command, Output};

fn run(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_ferrosintesis"))
        .args(args)
        .output()
        .expect("run ferrosintesis")
}

#[test]
fn help_is_successful_on_stdout() {
    let output = run(&["--help"]);
    assert!(output.status.success(), "help failed: {output:?}");
    assert!(
        String::from_utf8_lossy(&output.stdout).contains("usage: ferrosintesis"),
        "help was not printed to stdout: {output:?}"
    );
    assert!(output.stderr.is_empty(), "help wrote to stderr: {output:?}");
}

#[test]
fn version_is_successful_and_names_the_package() {
    let output = run(&["--version"]);
    assert!(output.status.success(), "version failed: {output:?}");
    assert!(
        String::from_utf8_lossy(&output.stdout).contains(env!("CARGO_PKG_VERSION")),
        "version did not name the package version: {output:?}"
    );
    assert!(
        output.stderr.is_empty(),
        "version wrote to stderr: {output:?}"
    );
}

#[test]
fn unknown_option_is_named_regardless_of_position() {
    for args in [["--bogus", "song.mid"], ["song.mid", "--bogus"]] {
        let output = run(&args);
        assert_eq!(
            output.status.code(),
            Some(2),
            "unknown option did not produce a usage error: {output:?}"
        );
        assert!(
            String::from_utf8_lossy(&output.stderr).contains("--bogus"),
            "unknown option was not named: {output:?}"
        );
    }
}

#[test]
fn end_of_options_allows_a_dash_prefixed_input_path() {
    let output = run(&["--", "-x.mid"]);
    assert_eq!(
        output.status.code(),
        Some(1),
        "dash-prefixed input did not reach file loading: {output:?}"
    );
    assert!(
        !String::from_utf8_lossy(&output.stderr).contains("unknown option"),
        "end-of-options input was rejected as an option: {output:?}"
    );
}
