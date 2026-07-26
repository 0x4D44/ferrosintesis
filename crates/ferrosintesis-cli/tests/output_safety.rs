use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

const SHORT_MIDI: &[u8] = &[
    b'M', b'T', b'h', b'd', 0, 0, 0, 6, 0, 0, 0, 1, 0, 96, b'M', b'T', b'r', b'k', 0, 0, 0, 22, 0,
    0xff, 0x51, 3, 0x07, 0xa1, 0x20, 0, 0xc0, 0, 0, 0x90, 60, 100, 96, 0x80, 60, 0, 0, 0xff, 0x2f,
    0,
];

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock before Unix epoch")
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "ferrosintesis-cli-{label}-{}-{nonce}",
            std::process::id()
        ));
        fs::create_dir(&path).expect("create test directory");
        Self(path)
    }

    fn join(&self, path: impl AsRef<Path>) -> PathBuf {
        self.0.join(path)
    }
}

impl Drop for TestDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn assert_alias_rejected(input: &Path, extra_args: &[&Path]) {
    fs::write(input, SHORT_MIDI).expect("write MIDI fixture");
    let original = fs::read(input).expect("read MIDI fixture");

    let mut command = Command::new(env!("CARGO_BIN_EXE_ferrosintesis"));
    command.arg(input);
    for arg in extra_args {
        command.arg(arg);
    }
    command.args(["--tail", "0", "--no-samples", "-q"]);
    let output = command.output().expect("run ferrosintesis");

    assert!(
        !output.status.success(),
        "input/output alias unexpectedly succeeded"
    );
    assert_eq!(
        fs::read(input).expect("read input after rejection"),
        original,
        "rejected command changed its input"
    );
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("aliases the input"),
        "stderr did not explain the rejection: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn explicit_output_cannot_replace_input() {
    let dir = TestDir::new("explicit-alias");
    let input = dir.join("score.mid");
    let out_flag = Path::new("-o");
    assert_alias_rejected(&input, &[out_flag, &input]);
}

#[test]
fn default_output_cannot_replace_midi_named_wav() {
    let dir = TestDir::new("default-alias");
    let input = dir.join("score.wav");
    assert_alias_rejected(&input, &[]);
}

#[test]
fn distinct_output_still_replaces_an_existing_wav() {
    let dir = TestDir::new("distinct-output");
    let input = dir.join("score.mid");
    let output = dir.join("score.wav");
    fs::write(&input, SHORT_MIDI).expect("write MIDI fixture");
    fs::write(&output, b"prior output").expect("write prior output");

    let result = Command::new(env!("CARGO_BIN_EXE_ferrosintesis"))
        .arg(&input)
        .args(["-o"])
        .arg(&output)
        .args(["--tail", "0", "--no-samples", "-q"])
        .output()
        .expect("run ferrosintesis");

    assert!(
        result.status.success(),
        "distinct output failed: {}",
        String::from_utf8_lossy(&result.stderr)
    );
    assert!(
        fs::read(&output)
            .expect("read rendered output")
            .starts_with(b"RIFF"),
        "output is not a WAV"
    );
    assert_eq!(
        fs::read(&input).expect("read source after render"),
        SHORT_MIDI,
        "successful render changed its input"
    );
}

#[cfg(windows)]
#[test]
fn exclusively_held_distinct_output_is_not_reported_as_an_input_alias() {
    use std::fs::OpenOptions;
    use std::os::windows::fs::OpenOptionsExt;

    let dir = TestDir::new("held-distinct-output");
    let input = dir.join("score.mid");
    let output = dir.join("score.wav");
    fs::write(&input, SHORT_MIDI).expect("write MIDI fixture");
    fs::write(&output, b"held prior output").expect("write prior output");
    let output_guard = OpenOptions::new()
        .read(true)
        .write(true)
        .share_mode(0)
        .open(&output)
        .expect("hold output without sharing");

    let result = Command::new(env!("CARGO_BIN_EXE_ferrosintesis"))
        .arg(&input)
        .args(["-o"])
        .arg(&output)
        .args(["--tail", "0", "--no-samples", "-q"])
        .output()
        .expect("run ferrosintesis");

    assert!(
        !result.status.success(),
        "renderer unexpectedly replaced an exclusively held output"
    );
    let stderr = String::from_utf8_lossy(&result.stderr);
    assert!(
        !stderr.contains("aliases the input"),
        "a third-party sharing violation was misreported as aliasing: {stderr}"
    );
    assert_eq!(
        fs::read(&input).expect("read input after rejection"),
        SHORT_MIDI,
        "rejected command changed its input"
    );

    drop(output_guard);
    assert_eq!(
        fs::read(&output).expect("read output after releasing guard"),
        b"held prior output",
        "rejected command changed the held output"
    );
}
