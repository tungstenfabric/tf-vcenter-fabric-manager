import re
from setuptools import find_packages, setup


def requirements(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
    c = re.compile(r"\s*#.*")
    return list(filter(bool, map(lambda y: c.sub("", y).strip(), lines)))


setup(
    name="contrail-vcenter-fabric-manager",
    version="0.1dev",
    packages=find_packages(),
    package_data={"": ["*.html", "*.css", "*.xml", "*.yml"]},
    zip_safe=False,
    long_description="Contrail vCenter Fabric Manager",
    test_suite="tests",
    install_requires=requirements("requirements.txt"),
    tests_require=requirements("test-requirements.txt"),
    entry_points={
        "console_scripts": [
            "contrail-vcenter-fabric-manager = cvfm.__main__:server_main"
        ]
    },
)
