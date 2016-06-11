from setuptools import setup, find_packages

setup(
    name = "imap-filter-client",
    description = "Small python IMAP client daemon for filtering email messages",
    version = "1.0.0",
    author = 'Lajos Santa',
    author_email = 'santa.lajos@coldline.hu',
    url = 'https://github.com/voidpp/imap-filter-client',
    install_requires = [
        "voidpp-tools>=1.5.3,<=1.6.0",
        "voidpp-web-tools>=1.0.0,<=2.0.0",
        "IMAPClient==1.0.1",
        "simple-crypt==4.1.7",
        "PyYAML==3.11",
        "gevent==1.1.1",
    ],
    scripts = [
        "bin/imap-filter-client"
    ],
    packages = find_packages(),
)
