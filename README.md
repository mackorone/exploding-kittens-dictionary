# exploding-kittens-dictionary

> A list of all valid English words, according to Exploding Kittens

## Introduction

In November of 2021, I sent the following email to support@explodingkittens.com:

> Hi! My name is Mack. I'm a software developer and I'd like to build a bot to
> play *A Little Wordy*. Before I can do that, I need a list of words that are
> considered valid. As far as I can tell, the
> [website](https://ek.explodingkittens.com/dictionary) only provides an
> endpoint for checking the validity of individual words - there's no exhaustive
> list of all valid words. Would you consider making one available? If not, my
> plan is to find some exhaustive list of English words, check the validity of
> each word using your API, and publish the list of all valid words to GitHub.

I got the following reply:

> Thanks for reaching out! Hmm, I don't think we have that list available at
> this time. Your best bet would be to use the Scrabble Dictionary.

Hence this repository.

## How it works

The script fetches existing lists of English words. It normalizes and
deduplicates the results, and then queries the Exploding Kittens Dictionary API
to determine which words are valid. Results are written to a file specified on
the command line.

Installation:
```
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements/requirements.txt
```

Example invocation:
```
python script.py --output words.txt
```
