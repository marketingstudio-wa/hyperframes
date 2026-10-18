#!/usr/bin/env python3
"""WA Construct / Home Estimator video studio.

    python3 vstudio.py jobs/my-video.yaml [--only vertical]
"""
import argparse
import json

from studio import pipeline

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("job")
ap.add_argument("--only", action="append", choices=list(pipeline.FORMATS), help="render just these formats")
args = ap.parse_args()
print(json.dumps(pipeline.run(args.job, args.only), indent=1))
