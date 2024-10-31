## To do:
- Add slack integration
- Connect to Opsgenie or another calendar to pull engineer's work shift
- Add a test mode to simulate assigning tickets

## How to setup the project:
1. Install pyenv to manage python versions, [instructions](https://github.com/pyenv/pyenv?tab=readme-ov-file#automatic-installer).
2. Install Python 3.12 using pyenv ```pyenv install 3.12```
3. Clone the dispatcher repo
4. Change directory to the repo directory
5. Set python version in the repo dir ```pyenv local 3.12```
6. Create a virtual environment in the repo ```python -m venv .venv```
7. Activate virtual env ```source .venv/bin/activate```
8. Install Python libraries for this project ```pip instal -r requirements.txt``` 