//! amp-lab — twiddle the driven-guitar amp knobs live, over a looping backing
//! track, to choose what GM29/GM30 should default to (MM-REQ-KILN-00028 Part B).
//!
//! The UI never touches the synth. It pushes commands into a lock-free ring that
//! the audio thread drains; see `audio.rs` for why.

mod amp;
mod audio;
mod ring;
#[cfg(test)]
mod rtalloc;

/// Test builds route every allocation through a counter so the audio callback's
/// "no allocation after setup" contract can be MEASURED rather than reasoned about
/// (MM-BUG-KILN-00082). Inert unless armed, and absent from release builds.
#[cfg(test)]
#[global_allocator]
static COUNTING_ALLOCATOR: rtalloc::Counting = rtalloc::Counting;
mod seq;

use std::sync::atomic::Ordering;

use eframe::egui;

use amp::{Rig, KNOBS, NEUTRAL};
use ring::{Cmd, Producer};

/// The backing loop, embedded so the tool is self-contained.
const BACKING: &[u8] = include_bytes!("../assets/backing.mid");

/// The channel the audition guitar plays on (must be in `audio::GUITAR_CHANNELS`).
const GUITAR_CH: u8 = 1;

fn main() -> eframe::Result<()> {
    let (tx, rx) = ring::Ring::channel();
    let engine = match audio::start(rx, BACKING) {
        Ok(e) => Some(e),
        Err(e) => {
            eprintln!("audio unavailable: {e}");
            None
        }
    };
    let app = Lab::new(tx, engine);
    eframe::run_native(
        "amp lab — driven guitar",
        eframe::NativeOptions {
            viewport: egui::ViewportBuilder::default().with_inner_size([560.0, 700.0]),
            ..Default::default()
        },
        Box::new(|_cc| Ok(Box::new(app))),
    )
}

struct Lab {
    tx: Producer,
    engine: Option<audio::Engine>,
    rig: Rig,
    slot_a: Rig,
    slot_b: Rig,
    showing: Option<char>,
    playing: bool,
    solo: bool,
    status: String,
}

impl Lab {
    fn new(tx: Producer, engine: Option<audio::Engine>) -> Self {
        let rig = Rig::default();
        let me = Lab {
            tx,
            engine,
            rig,
            slot_a: rig,
            slot_b: rig,
            showing: None,
            playing: true,
            solo: false,
            status: String::new(),
        };
        me.send_rig();
        me
    }

    /// Push the whole rig (bank, program, six knobs) to the audio thread.
    fn send_rig(&self) {
        self.tx.push_midi(&self.rig.bytes(GUITAR_CH));
    }

    fn send_knob(&self, idx: u8) {
        self.tx.push_midi(&Rig::knob_bytes(
            GUITAR_CH,
            idx,
            self.rig.vals[idx as usize],
        ));
    }

    fn apply(&mut self, r: Rig, label: Option<char>) {
        let voice_changed = r.program != self.rig.program || r.lead_bank != self.rig.lead_bank;
        self.rig = r;
        self.showing = label;
        // A voice change rebuilds the Drive insert, so re-send everything; a knob
        // change alone only needs its own triple.
        if voice_changed {
            self.send_rig();
        } else {
            for k in KNOBS {
                self.send_knob(k.idx);
            }
        }
    }
}

impl eframe::App for Lab {
    fn update(&mut self, ctx: &egui::Context, _f: &mut eframe::Frame) {
        ctx.request_repaint_after(std::time::Duration::from_millis(100));
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("amp lab — driven guitar");

            match &self.engine {
                Some(e) => {
                    ui.label(
                        egui::RichText::new(format!("{} @ {} Hz", e.device_name, e.sample_rate))
                            .small()
                            .weak(),
                    );
                }
                None => {
                    ui.colored_label(
                        egui::Color32::RED,
                        "No audio device — knobs will not be audible. See console.",
                    );
                }
            }
            ui.separator();

            // ---- voice ----
            ui.horizontal(|ui| {
                ui.label("Program:");
                let mut r = self.rig;
                let mut changed = false;
                for p in [29u8, 30] {
                    let name = if p == 29 {
                        "29 overdrive"
                    } else {
                        "30 distortion"
                    };
                    if ui.selectable_label(r.program == p, name).clicked() {
                        r.program = p;
                        changed = true;
                    }
                }
                ui.separator();
                ui.label("Bank:");
                for (lead, name) in [(false, "main"), (true, "lead")] {
                    if ui.selectable_label(r.lead_bank == lead, name).clicked() {
                        r.lead_bank = lead;
                        changed = true;
                    }
                }
                if changed {
                    self.apply(r, None);
                }
            });

            ui.separator();

            // ---- knobs ----
            for k in KNOBS {
                let i = k.idx as usize;
                ui.horizontal(|ui| {
                    ui.add_sized(
                        [88.0, 18.0],
                        egui::Label::new(egui::RichText::new(k.name).strong()),
                    );
                    let mut v = self.rig.vals[i] as f32;
                    let resp = ui.add(
                        egui::Slider::new(&mut v, 0.0..=127.0)
                            .fixed_decimals(0)
                            .show_value(true),
                    );
                    if resp.changed() {
                        self.rig.vals[i] = v.round() as u8;
                        self.showing = None;
                        self.send_knob(k.idx);
                    }
                    if ui.small_button("64").clicked() {
                        self.rig.vals[i] = NEUTRAL;
                        self.showing = None;
                        self.send_knob(k.idx);
                    }
                });
                ui.label(egui::RichText::new(k.blurb).small().weak());
                ui.add_space(2.0);
            }

            ui.separator();

            // ---- A/B ----
            ui.horizontal(|ui| {
                ui.label("A/B:");
                if ui.button("store A").clicked() {
                    self.slot_a = self.rig;
                    self.status = "stored A".into();
                }
                if ui.button("store B").clicked() {
                    self.slot_b = self.rig;
                    self.status = "stored B".into();
                }
                ui.separator();
                if ui
                    .selectable_label(self.showing == Some('A'), "recall A")
                    .clicked()
                {
                    self.apply(self.slot_a, Some('A'));
                }
                if ui
                    .selectable_label(self.showing == Some('B'), "recall B")
                    .clicked()
                {
                    self.apply(self.slot_b, Some('B'));
                }
            });

            // ---- transport ----
            ui.horizontal(|ui| {
                if ui
                    .button(if self.playing { "pause" } else { "play" })
                    .clicked()
                {
                    self.playing = !self.playing;
                    self.tx.push(Cmd::Play(self.playing));
                }
                if ui.selectable_label(self.solo, "solo guitar").clicked() {
                    self.solo = !self.solo;
                    self.tx.push(Cmd::Solo(self.solo));
                }
                if ui.button("panic").clicked() {
                    self.tx.push(Cmd::Panic);
                }
                if ui.button("reset knobs").clicked() {
                    let mut r = self.rig;
                    r.vals = [NEUTRAL; 6];
                    self.apply(r, None);
                }
            });

            ui.separator();

            // ---- export: the tool's actual output ----
            ui.horizontal(|ui| {
                if ui.button("copy settings").clicked() {
                    ctx.copy_text(self.rig.export());
                    self.status = "settings copied to clipboard".into();
                }
                if !self.status.is_empty() {
                    ui.label(egui::RichText::new(&self.status).small().weak());
                }
            });
            let mut txt = self.rig.export();
            egui::ScrollArea::vertical()
                .max_height(140.0)
                .show(ui, |ui| {
                    ui.add(
                        egui::TextEdit::multiline(&mut txt)
                            .font(egui::TextStyle::Monospace)
                            .desired_width(f32::INFINITY),
                    );
                });

            // ---- meters ----
            if let Some(e) = &self.engine {
                let v = e.meters.voices.load(Ordering::Relaxed);
                let peak = e.meters.peak_x1e4.load(Ordering::Relaxed) as f32 / 1e4;
                let xr = e.meters.xruns.load(Ordering::Relaxed);
                ui.horizontal(|ui| {
                    ui.label(egui::RichText::new(format!("voices {v}")).small().weak());
                    ui.label(
                        egui::RichText::new(format!("peak {peak:.2}"))
                            .small()
                            .color(if peak > 0.99 {
                                egui::Color32::RED
                            } else {
                                egui::Color32::GRAY
                            }),
                    );
                    if xr > 0 {
                        ui.colored_label(egui::Color32::RED, format!("xruns {xr}"));
                    }
                });
            }
        });
    }
}
