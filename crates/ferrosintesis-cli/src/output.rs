use ferrosintesis::offline;
use std::ffi::OsString;
use std::fs::{self, OpenOptions};
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

#[cfg(windows)]
use std::fs::File;

static NEXT_TEMP_FILE: AtomicU64 = AtomicU64::new(0);

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

pub(crate) fn write_wav_atomically(
    output: &Path,
    sample_rate: u32,
    interleaved: &[i16],
) -> io::Result<()> {
    atomic_write(output, |temporary| {
        offline::write_wav(temporary, sample_rate, interleaved)
    })
}

fn atomic_write(
    output: &Path,
    write_temporary: impl FnOnce(&Path) -> io::Result<()>,
) -> io::Result<()> {
    let temporary = reserve_temporary_path(output)?;
    let result = (|| {
        write_temporary(&temporary)?;
        OpenOptions::new()
            .write(true)
            .open(&temporary)?
            .sync_all()?;
        fs::rename(&temporary, output)
    })();

    if result.is_err() {
        let _ = fs::remove_file(&temporary);
    }
    result
}

fn reserve_temporary_path(output: &Path) -> io::Result<PathBuf> {
    let parent = output
        .parent()
        .filter(|path| !path.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    let file_name = output.file_name().ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("output {} has no file name", output.display()),
        )
    })?;

    for _ in 0..100 {
        let sequence = NEXT_TEMP_FILE.fetch_add(1, Ordering::Relaxed);
        let mut temporary_name = OsString::from(".");
        temporary_name.push(file_name);
        temporary_name.push(format!(".{}.{}.tmp", std::process::id(), sequence));
        let temporary = parent.join(temporary_name);

        match OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary)
        {
            Ok(_) => return Ok(temporary),
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {}
            Err(error) => return Err(error),
        }
    }

    Err(io::Error::new(
        io::ErrorKind::AlreadyExists,
        format!(
            "could not reserve a temporary file beside {}",
            output.display()
        ),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
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

    #[test]
    fn failed_temporary_write_preserves_existing_output() {
        let dir = TestDir::new("write-failure");
        let output = dir.join("score.wav");
        fs::write(&output, b"prior output").expect("write prior output");

        let error = atomic_write(&output, |temporary| {
            fs::write(temporary, b"partial replacement")?;
            Err(io::Error::other("injected write failure"))
        })
        .expect_err("injected write failure should escape");

        assert_eq!(error.kind(), io::ErrorKind::Other);
        assert_eq!(
            fs::read(&output).expect("read preserved output"),
            b"prior output"
        );
    }

    #[test]
    fn successful_temporary_write_replaces_existing_output() {
        let dir = TestDir::new("write-success");
        let output = dir.join("score.wav");
        fs::write(&output, b"prior output").expect("write prior output");

        atomic_write(&output, |temporary| fs::write(temporary, b"new output"))
            .expect("replace output");

        assert_eq!(fs::read(&output).expect("read new output"), b"new output");
    }
}
