from setuptools import setup, find_packages

setup(
    name='rgtools',
    version='0.0.1',
    # url='https://github.com/saadgulzar/india_names',
    author='Erik Sorensen',
    description='Repository with the tooling for capturing data from social science registry trials',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=['pandas==2.0.3'],
)