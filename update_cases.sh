#!/usr/bin/env bash

nix develop --command uv run jpamb build --compile
nix develop --command uv run jpamb build --decompile

