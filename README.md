# multi-site-monitor

Small test script for the Google PageSpeed Insights (PSI) API.

## Setup

1. Clone the repo and create a virtual environment:

   ```bash
   python -m venv .venv
   .venv/Scripts/activate   # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your PSI API key:

   ```
   PAGESPEED_API_KEY=your_api_key_here
   ```

   Get a key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) with the PageSpeed Insights API enabled. `.env` is gitignored — never commit it.

## Usage

```bash
python test_pagespeed.py
```

Runs a mobile PSI analysis against `https://aireadypage.com` and prints the performance score and page title.
