# Target Product Monitor

A Python script to monitor Target product availability and get notified when items come back in stock.

## Features

- Monitor multiple Target products simultaneously
- Desktop notifications when products become available
- Discord webhook notifications
- Configurable check intervals
- Persistent storage of monitored products
- Simple command-line interface

## Requirements

- Python 3.7 or higher
- Required packages listed in `requirements.txt`

## Installation

1. Clone this repository or download the files
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the script:
   ```
   python target_monitor.py
   ```

2. Use the menu options:
   - Option 1: Add a new product to monitor
   - Option 2: Start monitoring all products
   - Option 3: View all monitored products
   - Option 4: Set Discord webhook
   - Option 5: Exit the program

3. When adding a product:
   - Enter the full Target product URL
   - Provide a name for the product (for easy reference)

4. To set up Discord notifications:
   - Create a webhook in your Discord server (Server Settings > Integrations > Webhooks)
   - Copy the webhook URL
   - Use Option 4 in the menu to set the webhook URL

5. The monitor will:
   - Check product availability at the specified interval
   - Send desktop notifications when products become available
   - Send Discord notifications if a webhook is configured
   - Save the monitoring history to `products.json`

## Notes

- The default check interval is 5 minutes (300 seconds)
- You can press Ctrl+C to stop the monitoring process
- Product data is saved in `products.json` and persists between runs
- Discord webhook URL is saved in `config.json`
- The script uses both desktop notifications and Discord webhooks to alert you when products become available

## Discord Notification Format

When a product becomes available, you'll receive a Discord message with:
- Product name
- Direct link to the product
- Timestamp
- Target-themed formatting

## Disclaimer

This tool is for personal use only. Please be mindful of Target's terms of service and rate limiting when using this monitor. 