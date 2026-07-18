import re,sys
roots={}
for ln in sys.stdin:
    m=re.match(r"(\S+\.wav)\s+([\d.]+)\s+",ln)
    if m: roots[m.group(1)]=float(m.group(2))
fam=sys.argv[1]; zones=sys.argv[2].split(",")
def emit(dyn,rr):
    suf=f"_{dyn}"+("_rr2" if rr else "")
    print(f"fn {fam}_{dyn}{'_rr2' if rr else ''}() -> &'static [Zone] {{")
    print("    static B: OnceLock<Vec<Zone>> = OnceLock::new();")
    print("    B.get_or_init(|| {"); print("        bank!(")
    for z in zones:
        fn=f"{fam}_{z}{suf}.wav"; print(f'            "{fn}" => {roots[fn]:.2f},')
    print("        )"); print("    })"); print("}"); print()
for d in ("pp","mf","f"):
    emit(d,False); emit(d,True)
print(f"pub fn {fam}_bank(vel: u8, rr2: bool) -> &'static [Zone] {{")
print("    match (vel, rr2) {")
print(f"        (0..=51, false) => {fam}_pp(),")
print(f"        (0..=51, true) => {fam}_pp_rr2(),")
print(f"        (52..=95, false) => {fam}_mf(),")
print(f"        (52..=95, true) => {fam}_mf_rr2(),")
print(f"        (_, false) => {fam}_f(),")
print(f"        (_, true) => {fam}_f_rr2(),")
print("    }"); print("}")
