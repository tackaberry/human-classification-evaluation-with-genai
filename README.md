# human-classification-evaluation-with-genai

This use GenAI to evaluate the accuracy of human classification of plant samples.

<img src="screenshot.png" alt="screenshot" style="width:600px;" />


### Local Environment Setup

Dependiencies
```bash
sudo apt-get install python3-virtualenv
virtualenv env
```

Install requirements
```bash
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env # change variables in .env file
```

Start app
```bash
mesop main.py
```