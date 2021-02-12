from setuptools import find_packages, setup

setup(
    name="webchela",
    version="1.2.2",
    url="https://github.com/livelace/webchela",
    author="Oleg Popov",
    author_email="o.popov@livelace.ru",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "webchela=webchela.server.__main__:main",
            "webchela-cli=webchela.client.__main__:main"
        ],
    }
)
