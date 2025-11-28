import sys, traceback, os
try:
    import torch
    print("IMPORT OK\ntorch.__file__:", getattr(torch, '__file__', 'N/A'))
    try:
        import torch._C as _C
        print("torch._C OK ->", getattr(_C, '__file__', 'N/A'))
    except Exception:
        print("Failed loading torch._C:")
        traceback.print_exc()
except Exception:
    print("IMPORT FAILED:")
    traceback.print_exc()

print("\nCWD:", os.getcwd())
print("\nFirst 15 sys.path entries:")
for i,p in enumerate(sys.path[:15],1):
    print(f"{i}. {p}")
