## To do:
- ~~Add slack integration~~
- ~~Connect to Opsgenie or another calendar to pull engineer's work shift~~
- ~~Add a test mode to simulate assigning tickets~~
- ~~Need to decide where to set availability and organizations~~
- ~~Clean up the code~~
- ~~Handle PTO~~
- Finally enable the ticket assignment

## How to setup the project:
1. Install pyenv to manage python versions, [instructions](https://github.com/pyenv/pyenv?tab=readme-ov-file#automatic-installer).
2. Install Python 3.12 using pyenv ```pyenv install 3.12```
3. Clone the dispatcher repo
4. Change directory to the repo directory
5. Set python version in the repo dir ```pyenv local 3.12```
6. Create a virtual environment in the repo ```python -m venv .venv```
7. Activate virtual env ```source .venv/bin/activate```
8. Install Python libraries for this project ```pip instal -r requirements.txt``` 

## How to deploy:
1. [Create the dependency layer](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html#python-layer-packaging):
    ```
    mkdir python
    cp -r .venv/lib python/
    zip -r layer_content.zip python
    ```
2. Upload the `layer_content.zip` to S3 and add/edit the lambda function layer.
3. Create the function package:
    ```
    zip -r package.zip *.py
    ```
4. Upload the package to the lambda function.
5. Don't forget to se the environment variables in the lambda configuration.