# SPDX-License-Identifier: GPL-3.0-or-later
"""Sequential Windows off/on/on/off host-timing comparison with private saves."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from summarize_latency import summarize

def ensure_idle():
    check=subprocess.run(["powershell", "-NoProfile", "-Command",
        "if (Get-Process -Name recomp_program_runner,soulcalibur2,soulcalibur2-launcher,recomp_graphics_inventory_test -ErrorAction SilentlyContinue) { exit 1 }"],capture_output=True)
    if check.returncode:
        raise RuntimeError("Close the existing game/launcher before starting a latency test")

def close(process):
    user32=ctypes.windll.user32
    @ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
    def visitor(hwnd,param):
        owner=ctypes.c_ulong();user32.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value==process.pid:user32.PostMessageW(hwnd,0x0010,0,0)
        return True
    user32.EnumWindows(visitor,0)
    try:return process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.terminate();process.wait()
        raise RuntimeError("Game did not close cleanly; trace is invalid")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe",type=Path,required=True)
    ap.add_argument("--disc",type=Path,required=True)
    ap.add_argument("--seed-storage",type=Path,required=True,help="Read-only source containing partition1")
    ap.add_argument("--output",type=Path,required=True,help="New directory under private/")
    ap.add_argument("--rate",type=float,default=144)
    ap.add_argument("--seconds",type=float,default=75)
    ap.add_argument("--hidden",action="store_true",help="Diagnostic only; a hidden window may provide no swapchain samples")
    args=ap.parse_args()
    if os.name!="nt":ap.error("This process/window harness currently supports Windows only")
    if not 30<=args.rate<=1000 or args.seconds<60:ap.error("Rate must be 30..1000; allow at least 60 seconds per run")
    args.output=args.output.resolve()
    if "private" not in args.output.parts:ap.error("Keep generated validation output under private/")
    args.output.mkdir(parents=True,exist_ok=False)
    results=[]
    for index,rate in enumerate(["off",str(args.rate),str(args.rate),"off"],1):
        ensure_idle()
        folder=args.output/f"{index}-{rate}";folder.mkdir()
        shutil.copytree(args.seed_storage/"partition1",folder/"storage/partition1")
        settings=folder/"settings.ini"
        settings.write_text("[features]\npreset=custom\ngraphics_prepare=1\n",encoding="utf-8")
        trace=folder/"latency.csv"
        env=os.environ.copy()
        for key in ["SC2_RAM_DUMP","SC2_RAM_DUMP_AT","RECOMP_D3D_FRAME_DUMP","RECOMP_RENDER_TRACE"]:env.pop(key,None)
        env.update(RECOMP_LATENCY_TRACE=str(trace),RECOMP_RENDER_FPS=rate)
        if args.hidden:env["RECOMP_HEADLESS"]="1"
        else:env.pop("RECOMP_HEADLESS",None)
        cmd=[str(args.exe.resolve()),"--disc",str(args.disc.resolve()),"--storage",str(folder/"storage"),
             "--settings",str(settings),"--skip-intro","--input-script-only"]
        for step in ["5:120:start","34#2:120:A","34#2:300:A","34#2:600:A","6:150:A",
                     "6:200:down","6:220:down","6:240:down","6:260:down","6:320:A",
                     "6#2:150:A","6#2:300:A","10:150:A","10:300:A","10:700:down","10:900:A"]:
            cmd += ["--input-scene",step]
        for poll in range(600,1800,40):cmd += ["--input-scene",f"7:{poll}:X"]
        print(f"Starting {index}/4: interpolation {rate}",flush=True)
        with (folder/"stdout.log").open("w") as out,(folder/"stderr.log").open("w") as err:
            process=subprocess.Popen(cmd,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                deadline=time.monotonic()+args.seconds
                while process.poll() is None and time.monotonic()<deadline:time.sleep(.25)
                code=close(process) if process.poll() is None else process.returncode
            finally:
                if process.poll() is None:process.terminate();process.wait()
        if code!=0:raise RuntimeError(f"Run {index} failed with exit {code}")
        report=summarize(trace)
        if report["submitted_frames"]<300 or report["trace_dropped_rows"]:
            raise RuntimeError("Insufficient combat samples or trace overflow; do not report latency")
        report.update(interpolation=rate,exit_code=code,visible=not args.hidden)
        results.append(report)
        (args.output/"summary.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
        print(json.dumps(report),flush=True)
    print("Finished all four runs; all game processes have exited.",flush=True)

if __name__=="__main__":main()
