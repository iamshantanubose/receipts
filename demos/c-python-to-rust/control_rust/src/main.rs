use std::io::{self, BufRead, Write};

const MAX_TOKENS_LIMIT: i64 = 4096;
const MAX_PROMPT_CHARS: usize = 20;

/// Python's str.isspace() set (Unicode White_Space + \x1c-\x1f), as used by str.strip().
fn py_space(c: char) -> bool {
    c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c)
}

/// Whitespace that int()/float() tolerate: str.isspace() minus \x1c-\x1f.
fn num_space(c: char) -> bool {
    py_space(c) && !('\u{1c}'..='\u{1f}').contains(&c)
}

/// Code points of every Unicode "Nd" zero digit known to the reference (CPython 3.12, Unicode 15).
/// Each is followed by the digits 1-9 at consecutive code points.
const ND_ZEROS: &[u32] = &[0x30, 0x660, 0x6f0, 0x7c0, 0x966, 0x9e6, 0xa66, 0xae6, 0xb66, 0xbe6, 0xc66, 0xce6, 0xd66, 0xde6, 0xe50, 0xed0, 0xf20, 0x1040, 0x1090, 0x17e0, 0x1810, 0x1946, 0x19d0, 0x1a80, 0x1a90, 0x1b50, 0x1bb0, 0x1c40, 0x1c50, 0xa620, 0xa8d0, 0xa900, 0xa9d0, 0xa9f0, 0xaa50, 0xabf0, 0xff10, 0x104a0, 0x10d30, 0x11066, 0x110f0, 0x11136, 0x111d0, 0x112f0, 0x11450, 0x114d0, 0x11650, 0x116c0, 0x11730, 0x118e0, 0x11950, 0x11c50, 0x11d50, 0x11da0, 0x11f50, 0x16a60, 0x16ac0, 0x16b50, 0x1d7ce, 0x1d7d8, 0x1d7e2, 0x1d7ec, 0x1d7f6, 0x1e140, 0x1e2f0, 0x1e4f0, 0x1e950, 0x1fbf0];

/// Like CPython's _PyUnicode_TransformDecimalAndSpaceToASCII: Nd digits -> ASCII, numeric spaces -> ' '.
fn to_ascii_number(raw: &str) -> String {
    raw.chars()
        .map(|c| {
            let cp = c as u32;
            if let Some(z) = ND_ZEROS.iter().find(|&&z| cp >= z && cp < z + 10) {
                char::from(b'0' + (cp - z) as u8)
            } else if num_space(c) {
                ' '
            } else {
                c
            }
        })
        .collect()
}

/// Underscores are allowed only between two ASCII digits (PEP 515).
fn underscores_ok(s: &str) -> bool {
    let b = s.as_bytes();
    (0..b.len()).all(|i| {
        b[i] != b'_' || (i > 0 && i + 1 < b.len() && b[i - 1].is_ascii_digit() && b[i + 1].is_ascii_digit())
    })
}

/// Mirrors Python int(str). Values too large for i64 saturate (they are out of range anyway).
fn py_int(raw: &str) -> Option<i64> {
    let t = to_ascii_number(raw);
    let s = t.trim_matches(' ');
    let (neg, body) = match s.strip_prefix('-') {
        Some(b) => (true, b),
        None => (false, s.strip_prefix('+').unwrap_or(s)),
    };
    if body.is_empty() || !underscores_ok(body) {
        return None;
    }
    let digits: String = body.chars().filter(|c| *c != '_').collect();
    if digits.is_empty() || !digits.bytes().all(|c| c.is_ascii_digit()) {
        return None;
    }
    if digits.len() > 4300 {
        return None; // CPython's default int max-str-digits limit: int() raises ValueError
    }
    let v: i64 = digits.parse().unwrap_or(i64::MAX);
    Some(if neg { -v } else { v })
}

/// Mirrors Python float(str).
fn py_float(raw: &str) -> Option<f64> {
    let t = to_ascii_number(raw);
    let s = t.trim_matches(' ');
    if s.is_empty() || !underscores_ok(s) {
        return None;
    }
    let cleaned: String = s.chars().filter(|c| *c != '_').collect();
    let body = cleaned.trim_start_matches(['+', '-']);
    if cleaned.len() - body.len() > 1 {
        return None;
    }
    let lower = body.to_ascii_lowercase();
    if matches!(lower.as_str(), "inf" | "infinity" | "nan") {
        return cleaned.parse::<f64>().ok();
    }
    // Python grammar: digits [. [digits]] | . digits, then optional exponent. ASCII only.
    if !body.bytes().all(|c| c.is_ascii_digit() || matches!(c, b'.' | b'e' | b'E' | b'+' | b'-')) {
        return None;
    }
    cleaned.parse::<f64>().ok()
}

fn normalize(line: &str) -> String {
    let parts: Vec<&str> = line.split('\t').collect();
    if parts.len() != 3 {
        return "ERR\tbad_shape".to_string();
    }
    let prompt = parts[0].trim_matches(py_space);
    if prompt.is_empty() {
        return "ERR\tempty_prompt".to_string();
    }
    let chars = prompt.chars().count();
    if chars > MAX_PROMPT_CHARS {
        return "ERR\tprompt_too_long".to_string();
    }
    let max_tokens = match py_int(parts[1]) {
        Some(v) => v,
        None => return "ERR\tbad_max_tokens".to_string(),
    };
    if max_tokens < 1 || max_tokens > MAX_TOKENS_LIMIT {
        return "ERR\tmax_tokens_range".to_string();
    }
    let temperature = if parts[2].is_empty() {
        1.0
    } else {
        match py_float(parts[2]) {
            Some(v) => v,
            None => return "ERR\tbad_temperature".to_string(),
        }
    };
    if !(0.0..=1.0).contains(&temperature) {
        return "ERR\ttemperature_range".to_string();
    }
    // Rust {:.1} rounds the exact binary value half-to-even, like Python round()+format.
    format!("OK\tchars={}\tmax_tokens={}\ttemperature={:.1}", chars, max_tokens, temperature)
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    let mut buf = Vec::new();
    let mut reader = stdin.lock();
    // Split on '\n' only (like Python iterating sys.stdin); keep '\r'.
    loop {
        buf.clear();
        let n = reader.read_until(b'\n', &mut buf).expect("read stdin");
        if n == 0 {
            break;
        }
        if buf.last() == Some(&b'\n') {
            buf.pop();
        }
        let line = String::from_utf8_lossy(&buf);
        writeln!(out, "{}", normalize(&line)).expect("write stdout");
    }
}
