import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.camera import Camera, check_camera
from engine.render import expand_camera, Path2
spec = json.load(open(sys.argv[1]))
tr = {e["id"]: Path2(e["from"], e["to"], e["t0"], e["dur"], e.get("bulge", 0.08), e.get("ease", "linear")) for e in spec["elements"] if e["type"] == "tracked"}
ok, rep, sp = check_camera(Camera(expand_camera(spec["camera"], tr)), spec["duration"], spec.get("fps", 60))
print("OK" if ok else "FAIL", rep); 
for s in sp[:30]: print("  spike", s)
