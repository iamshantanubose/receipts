use std::io::{self, BufRead, Write};

const MAX_TOKENS_LIMIT: i64 = 4096;
const MAX_PROMPT_CHARS: usize = 20;

fn normalize(line: &str) -> String {
    let parts: Vec<&str> = line.trim_end_matches('\n').split('\t').collect();
    if parts.len() != 3 {
        return "ERR\tbad_shape".to_string();
    }
    let prompt = parts[0].trim();
    if prompt.is_empty() {
        return "ERR\tempty_prompt".to_string();
    }
    if prompt.len() > MAX_PROMPT_CHARS {
        return "ERR\tprompt_too_long".to_string();
    }
    let max_tokens: i64 = match parts[1].trim().parse::<f64>() {
        Ok(v) => v as i64,
        Err(_) => return "ERR\tbad_max_tokens".to_string(),
    };
    if max_tokens < 1 || max_tokens > MAX_TOKENS_LIMIT {
        return "ERR\tmax_tokens_range".to_string();
    }
    let temperature: f64 = if parts[2].is_empty() {
        1.0
    } else {
        match parts[2].parse::<f64>() {
            Ok(v) => v,
            Err(_) => return "ERR\tbad_temperature".to_string(),
        }
    };
    if !(0.0..=1.0).contains(&temperature) {
        return "ERR\ttemperature_range".to_string();
    }
    let rounded = (temperature * 10.0).round() / 10.0;
    format!(
        "OK\tchars={}\tmax_tokens={}\ttemperature={:.1}",
        prompt.len(),
        max_tokens,
        rounded
    )
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.expect("read stdin");
        writeln!(out, "{}", normalize(&line)).expect("write stdout");
    }
}
