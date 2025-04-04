import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from plyer import notification
from discord_webhook import DiscordWebhook, DiscordEmbed
import json
import os
from dotenv import load_dotenv

class TargetMonitor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.products = self.load_products()
        self.discord_webhook_url = self.load_discord_webhook()
        self.last_notification_time = {}  # Track last notification time for each product
        self.redsky_key = "9f36aeafbe60771e321a7cc95a78140772ab3e96"  # Working Redsky API key

    def load_products(self):
        if os.path.exists('products.json'):
            with open('products.json', 'r') as f:
                return json.load(f)
        return []

    def load_discord_webhook(self):
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
                return config.get('discord_webhook_url')
        return None

    def save_discord_webhook(self, webhook_url):
        config = {}
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
        
        config['discord_webhook_url'] = webhook_url
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        self.discord_webhook_url = webhook_url

    def save_products(self):
        with open('products.json', 'w') as f:
            json.dump(self.products, f, indent=4)

    def add_product(self, url, name):
        # Extract Tcin from URL
        tcin = self.extract_tcin_from_url(url)
        if not tcin:
            print("Could not extract TCIN from URL. Please make sure the URL is in the format: https://www.target.com/p/product-name/-/A-TCIN")
            return False
        
        self.products.append({
            'url': url,
            'name': name,
            'tcin': tcin,
            'last_checked': None,
            'in_stock': False
        })
        self.save_products()
        return True
    
    def extract_tcin_from_url(self, url):
        # Extract TCIN from URL
        # Example URL: https://www.target.com/p/himalayan-salted-dark-chocolate-almonds-13oz-good-38-gather-8482/-/A-78099811
        try:
            # Split by '/' and get the last part
            parts = url.split('/')
            tcin = None
            for part in parts:
                if part.startswith('A-'):
                    # Extract the TCIN (remove 'A-' prefix)
                    # Split by any non-numeric characters and take the first part
                    tcin = part[2:].split('?')[0].split('#')[0]
                    # Keep only numeric characters
                    tcin = ''.join(c for c in tcin if c.isdigit())
                    break
            
            if tcin and tcin.isdigit():
                print(f"Extracted TCIN: {tcin}")
                return tcin
            else:
                print("Invalid TCIN format - must be numeric")
                return None
                
        except Exception as e:
            print(f"Error extracting TCIN: {e}")
            return None

    def check_availability(self, url):
        try:
            # Extract TCIN from URL
            tcin = self.extract_tcin_from_url(url)
            if not tcin:
                print("Could not extract TCIN from URL")
                return None
            
            # Use Target's Redsky API to check availability
            redsky_url = f"https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
            
            # Parameters for the Redsky API
            params = {
                'key': self.redsky_key,
                'tcin': tcin,
                'is_bot': 'false',
                'store_id': '1407',
                'pricing_store_id': '1407',
                'has_pricing_store_id': 'true',
                'has_financing_options': 'true',
                'include_obsolete': 'true',
                'visitor_id': '0192FC2116550201A38E4211CC48D7DB',
                'skip_personalized': 'true',
                'skip_variation_hierarchy': 'true',
                'channel': 'WEB',
                'page': f'/p/A-{tcin}'
            }
            
            response = requests.get(redsky_url, params=params, headers=self.headers)
            
            if response.status_code != 200:
                print(f"Redsky API request failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
            
            data = response.json()
            
            # Save API response for debugging
            with open("target_api_response.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print("Saved API response to target_api_response.json for inspection")
            
            # Check availability in the API response
            is_in_stock = False
            
            # Check if the product exists and has data
            if 'data' in data and 'product' in data['data']:
                product = data['data']['product']
                
                # Check for eligibility_rules in the direct item path
                if 'item' in product and 'eligibility_rules' in product['item']:
                    print(f"Product has eligibility_rules in direct item path: {product['item']['eligibility_rules']}")
                    is_in_stock = True
                
                # Check for eligibility_rules in the children.item path
                elif 'children' in product and 'item' in product['children'] and 'eligibility_rules' in product['children']['item']:
                    print(f"Product has eligibility_rules in children.item path: {product['children']['item']['eligibility_rules']}")
                    is_in_stock = True
            
            if is_in_stock:
                print("Product is in stock!")
            else:
                print("Product is out of stock")
            
            return is_in_stock
                
        except Exception as e:
            print(f"Error in check_availability: {e}")
            return None

    def monitor_products(self, check_interval=300):  # 5 minutes default
        while True:
            for product in self.products:
                print(f"Checking {product['name']}...")
                is_in_stock = self.check_availability(product['url'])
                
                if is_in_stock is not None:
                    current_time = datetime.now()
                    
                    # Check if we should send a notification (in stock and either:
                    # 1. Was previously out of stock, or
                    # 2. It's been more than 1 minute since the last notification)
                    should_notify = False
                    
                    if is_in_stock:
                        if not product['in_stock']:
                            # Item just came back in stock
                            should_notify = True
                        else:
                            # Item was already in stock, check cooldown
                            last_notification = self.last_notification_time.get(product['url'])
                            if last_notification is None or (current_time - last_notification) > timedelta(minutes=1):
                                should_notify = True
                    
                    if should_notify:
                        self.send_notification(product['name'], product['url'])
                        if self.discord_webhook_url:
                            self.send_discord_notification(product['name'], product['url'])
                            # Update last notification time
                            self.last_notification_time[product['url']] = current_time
                    
                    product['in_stock'] = is_in_stock
                    product['last_checked'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    self.save_products()
                
                time.sleep(2)  # Small delay between checks
            
            print(f"Waiting {check_interval} seconds before next check...")
            time.sleep(check_interval)

    def send_notification(self, product_name, url):
        notification.notify(
            title='Target Product In Stock!',
            message=f'{product_name} is now in stock!\n{url}',
            app_icon=None,
            timeout=10,
        )

    def send_discord_notification(self, product_name, url):
        try:
            webhook = DiscordWebhook(url=self.discord_webhook_url)
            
            embed = DiscordEmbed(
                title="🎯 Target Product In Stock!",
                description=f"**{product_name}** is now available!",
                color="03b2f8"  # Target red color
            )
            
            embed.add_embed_field(name="Product URL", value=url, inline=False)
            embed.set_timestamp()
            embed.set_footer(text="Target Product Monitor")
            
            webhook.add_embed(embed)
            webhook.execute()
        except Exception as e:
            print(f"Error sending Discord notification: {e}")

def main():
    monitor = TargetMonitor()
    
    while True:
        print("\nTarget Product Monitor")
        print("1. Add new product")
        print("2. Start monitoring")
        print("3. View products")
        print("4. Set Discord webhook")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == '1':
            url = input("Enter Target product URL: ")
            name = input("Enter product name: ")
            if monitor.add_product(url, name):
                print("Product added successfully!")
            else:
                print("Failed to add product.")
        
        elif choice == '2':
            interval = input("Enter check interval in seconds (default 300): ")
            try:
                interval = int(interval) if interval else 300
                print("Starting monitor... Press Ctrl+C to stop")
                monitor.monitor_products(interval)
            except KeyboardInterrupt:
                print("\nMonitor stopped")
        
        elif choice == '3':
            if not monitor.products:
                print("No products added yet")
            else:
                for product in monitor.products:
                    print(f"\nName: {product['name']}")
                    print(f"URL: {product['url']}")
                    print(f"TCIN: {product.get('tcin', 'N/A')}")
                    print(f"Last checked: {product['last_checked']}")
                    print(f"In stock: {product['in_stock']}")
        
        elif choice == '4':
            webhook_url = input("Enter Discord webhook URL: ")
            monitor.save_discord_webhook(webhook_url)
            print("Discord webhook URL saved successfully!")
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 