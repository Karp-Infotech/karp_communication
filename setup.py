from setuptools import setup, find_packages


setup(
    name="karp_communication",
    version=1,
    description="Tools to communicate with colaborators",
    author="Karp Infotech",
    author_email="sushil.pal@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'selenium>=4.0.0',  # Add Selenium as a dependency
    ]
)
