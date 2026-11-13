# -*- coding: utf-8 -*-
"""Diagnóstico: imprime límites de cada parte tras construirla."""
import importlib.util
import os
import sys

spec = importlib.util.spec_from_file_location(
    'build_sumi', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_sumi.py'))
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)  # no ejecuta main()

bs.clean_scene()
fur, special = bs.build_body_parts()
for o in fur + list(special.values()):
    xs = [v.co.x for v in o.data.vertices]
    ys = [v.co.y for v in o.data.vertices]
    zs = [v.co.z for v in o.data.vertices]
    print(f'{o.name:16s} loc={tuple(round(c,2) for c in o.location)} '
          f'x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}] z[{min(zs):.2f},{max(zs):.2f}]')
