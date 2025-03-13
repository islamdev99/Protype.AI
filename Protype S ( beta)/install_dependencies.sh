
#!/bin/bash

# Create a directory for libraries
mkdir -p .pythonlibs

# Install all dependencies in the local directory
pip install --target=./.pythonlibs -r requirements.txt

# Create a requirements.txt file if it doesn't exist
if [ ! -f requirements.txt ]; then
  echo "Creating requirements.txt from pyproject.toml dependencies"
  python -c "
import re
import toml

try:
    with open('pyproject.toml', 'r') as f:
        data = toml.load(f)
        deps = data.get('project', {}).get('dependencies', [])
        with open('requirements.txt', 'w') as req:
            for dep in deps:
                # Remove version specifiers
                clean_dep = re.sub(r'>=.*', '', dep)
                req.write(f'{clean_dep}\n')
except Exception as e:
    print(f'Error creating requirements.txt: {e}')
    with open('requirements.txt', 'w') as req:
        req.write('flask>=3.1.0\n')
        req.write('waitress>=3.0.2\n')
        req.write('beautifulsoup4>=4.13.3\n')
        req.write('google-generativeai>=0.8.4\n')
        req.write('celery>=5.4.0\n')
        req.write('matplotlib>=3.10.1\n')
        req.write('networkx>=3.4.2\n')
        req.write('numpy>=2.2.3\n')
        req.write('pandas>=2.2.3\n')
        req.write('scikit-learn>=1.6.1\n')
        req.write('spacy>=3.8.4\n')
        req.write('requests>=2.32.3\n')
"

  echo "Created requirements.txt"
fi

echo "Installing all dependencies to .pythonlibs directory..."
pip install --target=./.pythonlibs -r requirements.txt

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm --target ./.pythonlibs

echo "Dependencies installed successfully!"
