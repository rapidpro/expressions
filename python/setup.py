from setuptools import setup, find_packages
from collections import defaultdict


extra_packages = defaultdict(list)


def _is_requirement(line):
    """Returns whether the line is a valid package requirement."""
    line = line.strip()
    return line and not (line.startswith("-r") or line.startswith("#"))


def _read_requirements(filename, extra_packages):
    """Returns a list of package requirements read from the file."""
    requirements_file = open(filename).read()

    hard_requirements = []
    for line in requirements_file.splitlines():
        if _is_requirement(line):
            if line.find(';') > -1:
                dep, condition = tuple(line.split(';'))
                extra_packages[condition.strip()].append(dep.strip())
            else:
                hard_requirements.append(line.strip())
    return hard_requirements, extra_packages

required_packages, extra_packages = _read_requirements("requirements/base.txt", extra_packages)
test_packages, extra_packages = _read_requirements("requirements/tests.txt", extra_packages)

setup(
    name='rapidpro-expressions',
    version='1.8',
    description='Python implementation of the RapidPro expression and templating system',
    url='https://github.com/rapidpro/expressions',

    author='Nyaruka',
    author_email='code@nyaruka.com',

    license='BSD',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],

    keywords='rapidpro templating',
    packages=find_packages(),
    package_data={'temba_expressions': ['month.aliases']},
    install_requires=required_packages,
    extra_packages=extra_packages,
    test_suite='nose.collector',
    tests_require=required_packages + test_packages,
)
