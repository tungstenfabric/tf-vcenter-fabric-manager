# -*- mode: python; -*-

#
# Copyright (c) 2018 Juniper Networks, Inc. All rights reserved.
#
import itertools
import os
import fnmatch

env = DefaultEnvironment()

setup_sources = [
    'setup.py',
    'MANIFEST.in',
    'requirements.txt',
    'test-requirements.txt',
    'tox.ini',
    '.coveragerc',
    'pyproject.toml',
    'cvfm',
    'tests'
]
setup_sources_rules = [
    env.Install(Dir('.'), "#vcenter-fabric-manager/" + file)
    for file in setup_sources
]

cvfm_sandesh_files = ["vcenter_fabric_manager.sandesh"]
cvfm_sandesh = [
    env.SandeshGenPy(sandesh_file, "cvfm/sandesh/", False)
    for sandesh_file in cvfm_sandesh_files
]

cd_cmd = 'cd ' + Dir('.').path + ' && '
sdist_depends = []
sdist_depends.extend(setup_sources_rules)
sdist_depends.extend(cvfm_sandesh)
sdist_gen = env.Command('dist/contrail-vcenter-fabric-manager-0.1dev.tar.gz',
                        'setup.py', cd_cmd + 'python setup.py sdist')

env.Depends(sdist_gen, sdist_depends)

test_target = env.SetupPyTestSuite(sdist_gen, use_tox=True)
env.Alias('vcenter-fabric-manager:test', test_target)

env.Alias("cvfm", sdist_depends)

install_cmd = env.Command(
    None,
    "setup.py",
    "cd "
    + Dir(".").path
    + " && python setup.py install %s" % env["PYTHON_INSTALL_OPT"],
)

env.Depends(install_cmd, sdist_depends)
env.Alias("cvfm-install", install_cmd)