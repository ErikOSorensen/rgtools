from setuptools import setup, find_packages

setup(
    name='rgtools',
    version='2.0.0',
    # url='https://github.com/saadgulzar/india_names',
    author='Erik Sorensen',
    description='Repository with the tooling for capturing data from social science registry trials',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=['numpy==1.25.1'
        'pandas==2.0.3',
                      'xmlschema==2.3.1',
                      'Jinja2==3.1.2',
                      'openpyxl==3.1.3',
                        'PyMuPDF==1.24.4'
                      ],
)