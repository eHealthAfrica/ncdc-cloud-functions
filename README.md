# Cloud Functions

A repository of cloud functions (Google Cloud Functions)

## Table of Content
- [Setup](#setup)
    - [Python](#python)
    - [JavaScript](#javascript)
- [Development](#development)
    - [Python](#python)
    - [JavaScript](#python)
- [Deployment](#deployment)
- [Usage](#usage)


## Setup

```bash
# clone repository
git clone https://github.com/eHealthAfrica/cloud-functions.git
cd cloud-functions
```
Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/quickstarts). Using the instructions [here](https://cloud.google.com/sdk/docs/quickstarts)

### Python

- Make sure you have [Python](https://www.python.org/) and [pip](https://pypi.org/project/pip/) installed. (preferably python 3.7, pip 19.0).
- Setup virtual environment.
```bash
python -m venv venv
```
- Set your shell to use the venv paths for Python by activating the virtual environment.
```bash
source venv/bin/activate
```
- Install packages without affecting other projects or your global Python installation.
```bash
pip install google-cloud-storage
```
- **Note** If you want to stop using the virtual environment and go back to your global Python, you can deactivate it.
```bash
deactivate
```

### JavaScript

- Make sure [Node.js](https://nodejs.org/en/) and [NPM](https://www.npmjs.com/) are installed.
- Install [Express.js](https://expressjs.com/)
```bash
npm install express --save
```
- Install Google Cloud libraries for Node.js
```bash
npm install --save @google-cloud/storage
```

*[Return to TOC](#table-of-contents)*


## Development

Files should be placed in the following structure:

```bash
Language (folder)
|-- [function name] (folder)
    |-- main.py | index.js (file)
        |-- [function name] (function)

```
Reference sample code [here](#) or visit [Writing Google Cloud Functions](https://cloud.google.com/functions/docs/writing) for more information.


*[Return to TOC](#table-of-contents)*


## Deployment

To deploy your functions to the cloud use the following:
- Setup a [google cloud project](https://console.cloud.google.com/projectselector2/home/dashboard?_ga=2.92033183.489937636.1590048515-1924033251.1589721727)
- Enable the Cloud Functions API [here](https://console.cloud.google.com/flows/enableapi?apiid=cloudfunctions&redirect=https://cloud.google.com/functions/quickstart&_ga=2.92033183.489937636.1590048515-1924033251.1589721727)
- Navigate to the `Function Group` folder
- From your Terminal/Command Prompt run:
```bash
gcloud functions deploy [function name]
```


## Usage
- [Hosted Functions](#hosted-functions)
