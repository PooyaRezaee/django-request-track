from setuptools import setup, find_namespace_packages

setup(
    name="django-request-track",
    packages=find_namespace_packages(include=['request_track', 'request_track.*']),
    include_package_data=True,
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
)
