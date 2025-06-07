from setuptools import setup, find_packages

setup(
    name="website-cloning-system",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.0.16",
        "firecrawl>=0.3.2",
        "beautifulsoup4>=4.12.0",
        "pillow>=10.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "pydantic>=2.0.0",
        "requests>=2.28.0",
        "aiohttp>=3.8.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.9",
    author="Orchids Team",
    description="Multi-agent website cloning system using LangGraph",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
