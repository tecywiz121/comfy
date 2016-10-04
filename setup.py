from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    with open('README.md') as f:
        long_description = f.read()

setup(name='comfy',
      version='0.0.1',
      description='Formal view for configurations and command line options',
      long_description=long_description,

      author='Sam Wilson',
      author_email='sam@binarycake.ca',

      url='https://github.com/tecywiz121/comfy',

      license='MIT',

      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: MIT License'
      ],

      packages=['comfy'])
