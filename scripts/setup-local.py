#!/usr/bin/env python3
"""Explicitly install built sibling Project Units into the local station Project.

This is development assembly, not a package manager or a release downloader.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile


def safe_path(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'unsafe relative path: {relative}')
    candidate = root.joinpath(*path.parts)
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'path escapes root: {candidate}')
    return candidate


def assemble(project, workspace):
    project, workspace = project.resolve(), workspace.resolve()
    manifest = json.loads((workspace / 'repositories.json').read_text())
    plans = []
    destinations = set()
    for repository in manifest['repositories']:
        if 'files' not in repository:
            continue  # Host and Project records do not deploy Unit artifacts.
        source_root = safe_path(workspace, repository['name'])
        for source, destination in repository['files'].items():
            source_path = safe_path(source_root, source)
            target = safe_path(project, destination)
            if destination in destinations:
                raise ValueError(f'duplicate deployment target: {destination}')
            destinations.add(destination)
            if not source_path.is_file() or source_path.stat().st_size == 0:
                raise FileNotFoundError(f'missing built/source asset: {source_path}; build its repository first')
            plans.append((repository['name'], source_path, target))
    # Preflight all sources before changing anything. No symlink installation or
    # implicit builds/downloads; repeat runs deliberately refresh owned assets.
    receipt = []
    for name, source, target in plans:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
        try:
            shutil.copyfile(source, temporary_path)
            temporary_path.replace(target)
        finally:
            temporary_path.unlink(missing_ok=True)
        receipt.append({'repository': name, 'file': target.relative_to(project).as_posix(),
                        'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    receipt_path = project / 'build.nosync/local-assembly.json'
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Installed {len(plans)} files into {project}; receipt: {receipt_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    assemble(Path(__file__).resolve().parents[1], args.workspace)
