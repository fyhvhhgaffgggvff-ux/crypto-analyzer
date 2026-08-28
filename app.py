name: Run Bybit Bot

on:
  workflow_dispatch:
  schedule:
    - cron: '0 * * * *'

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt

      - name: Setup Cloudflare Warp
        run: |
          curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
          echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list
          sudo apt-get update && sudo apt-get install cloudflare-warp -y
          sudo warp-cli --accept-tos registration new || true
          sudo warp-cli --accept-tos mode proxy
          sudo warp-cli --accept-tos proxy port 40000
          sudo warp-cli --accept-tos connect
          sleep 3

      - name: Run Script
        env:
          BYBIT_API_KEY: ${{ secrets.BYBIT_API_KEY }}
          BYBIT_API_SECRET: ${{ secrets.BYBIT_API_SECRET }}
        run: |
          python main.py
