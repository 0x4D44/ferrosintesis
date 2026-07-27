use std::fs;
use std::io;
use std::path::Path;

// `OpenOptions` is reached only through `OpenOptionsExt::share_mode` in the Windows arm of
// `platform_same_file`; keeping it in the unconditional import made it an unused import on
// every unix host, which `-D warnings` promotes to a hard error and so failed the repo's
// own clippy gate everywhere except Windows.
#[cfg(windows)]
use std::fs::{File, OpenOptions};

pub(crate) fn reject_input_alias(input: &Path, output: &Path) -> io::Result<()> {
    if paths_refer_to_same_file(input, output)? {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!(
                "output {} aliases the input {}; refusing to overwrite the source MIDI",
                output.display(),
                input.display()
            ),
        ));
    }
    Ok(())
}

fn paths_refer_to_same_file(input: &Path, output: &Path) -> io::Result<bool> {
    let input_canonical = fs::canonicalize(input)?;
    let output_canonical = match fs::canonicalize(output) {
        Ok(path) => path,
        Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(false),
        Err(error) => return Err(error),
    };

    if input_canonical == output_canonical {
        return Ok(true);
    }

    platform_same_file(input, output)
}

#[cfg(unix)]
fn platform_same_file(input: &Path, output: &Path) -> io::Result<bool> {
    use std::os::unix::fs::MetadataExt;

    let input = fs::metadata(input)?;
    let output = fs::metadata(output)?;
    Ok(input.dev() == output.dev() && input.ino() == output.ino())
}

#[cfg(windows)]
fn platform_same_file(input: &Path, output: &Path) -> io::Result<bool> {
    use std::os::windows::fs::OpenOptionsExt;

    const ERROR_SHARING_VIOLATION: i32 = 32;

    // Stable Rust does not expose Windows' volume/file-index identity. Hold the input
    // with no sharing, then probe the output. A sharing violation is identity evidence
    // only if it disappears after releasing our guard; a third-party exclusive handle
    // can produce the same error for an unrelated output.
    let input_guard = OpenOptions::new().read(true).share_mode(0).open(input)?;
    match File::open(output) {
        Ok(_) => Ok(false),
        Err(error) if error.raw_os_error() == Some(ERROR_SHARING_VIOLATION) => {
            drop(input_guard);
            match File::open(output) {
                Ok(_) => Ok(true),
                Err(retry_error) => Err(retry_error),
            }
        }
        Err(error) => Err(error),
    }
}

#[cfg(not(any(unix, windows)))]
fn platform_same_file(_input: &Path, _output: &Path) -> io::Result<bool> {
    Ok(false)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    struct TestDir(PathBuf);

    impl TestDir {
        fn new(label: &str) -> Self {
            let nonce = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .expect("system clock before Unix epoch")
                .as_nanos();
            let path = std::env::temp_dir().join(format!(
                "ferrosintesis-output-{label}-{}-{nonce}",
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

    #[test]
    fn rejects_normalized_path_alias() {
        let dir = TestDir::new("normalized");
        let input = dir.join("score.mid");
        let nested = dir.join("nested");
        fs::write(&input, b"MIDI").expect("write input");
        fs::create_dir(&nested).expect("create nested directory");
        let normalized_alias = nested.join("..").join("score.mid");

        let error = reject_input_alias(&input, &normalized_alias)
            .expect_err("normalized alias should be rejected");
        assert_eq!(error.kind(), io::ErrorKind::InvalidInput);
    }

    #[test]
    fn rejects_hard_link_alias() {
        let dir = TestDir::new("hard-link");
        let input = dir.join("score.mid");
        let alias = dir.join("alias.wav");
        fs::write(&input, b"MIDI").expect("write input");
        fs::hard_link(&input, &alias).expect("create hard link");

        let error =
            reject_input_alias(&input, &alias).expect_err("hard-link alias should be rejected");
        assert_eq!(error.kind(), io::ErrorKind::InvalidInput);
    }

    #[test]
    fn rejects_supported_symbolic_link_alias() {
        let dir = TestDir::new("symbolic-link");
        let input = dir.join("score.mid");
        let alias = dir.join("alias.wav");
        fs::write(&input, b"MIDI").expect("write input");

        #[cfg(unix)]
        std::os::unix::fs::symlink(&input, &alias).expect("create symbolic link");
        #[cfg(windows)]
        if let Err(error) = std::os::windows::fs::symlink_file(&input, &alias) {
            if error.kind() == io::ErrorKind::PermissionDenied {
                return;
            }
            panic!("create symbolic link: {error}");
        }

        let error =
            reject_input_alias(&input, &alias).expect_err("symbolic-link alias should be rejected");
        assert_eq!(error.kind(), io::ErrorKind::InvalidInput);
    }

    #[test]
    fn accepts_distinct_existing_output_with_identical_contents() {
        let dir = TestDir::new("distinct");
        let input = dir.join("score.mid");
        let output = dir.join("score.wav");
        fs::write(&input, b"same bytes").expect("write input");
        fs::write(&output, b"same bytes").expect("write output");

        reject_input_alias(&input, &output).expect("distinct files should be accepted");
    }
}
