import csv
from datetime import datetime, timedelta
from dateutil.parser import parse
from telegram import Update  # Add this import for Update class
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import BotCommand
import logging
import requests
import os

class DomainMonitorBot:
    def __init__(self, token):
        self.inventory = {}
        self.authorized_users = [
            7949976647,  # Admin
            7845296753   # Additional authorized user
        ]
        self.notification_chats = ['7949976647', '7845296753']  # Separate notification targets
        
        # Rate limiting setup
        self.rate_limit = {}
        self.rate_limit_duration = timedelta(minutes=1)
        self.rate_limit_max = 5
        
        # Set up logging
        logging.basicConfig(
            filename='bot.log',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
        # Initialize application
        self.application = Application.builder().token(token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("status", self.get_status))
        self.application.add_handler(CommandHandler("check", self.check_domains))
        
        # Load domains from CSV on startup
        self.load_domains_from_csv()

        # Define the 'start' method here
    async def start(self, update: Update, context):
        """Handle the /start command"""
        user = update.effective_user
        await update.message.reply_text(f"Hello {user.first_name}, I'm your Domain Monitor Bot! I'm here to notify you about domain expiration dates.")
        logging.info(f"User {user.id} initiated the /start command.")

    def load_domains_from_csv(self, filename='domains.csv'):
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.add_domain(
                        name=row['domain_name'],
                        renewal_date=row['expiration_date']   
                    )
            logging.info(f"Successfully loaded domains from {filename}")
        except Exception as e:
            logging.error(f"Failed to load CSV: {str(e)}")

    async def send_telegram_alert(self, context):
        alert_domains = self.get_immediate_expiry_domains(days=5)
        
        if alert_domains:
            message = "🚨 URGENT Domain Expiration Alert:\n\n"
            message += "\n".join(
                [f"- {d['name']} expires on {d['renewal_date'].strftime('%Y-%m-%d')}"
                 f" ({self._days_remaining(d['renewal_date'])} days left)"
                 for d in alert_domains]
            )
            
            # Send to all notification chats
            for chat_id in self.notification_chats:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message
                    )
                    logging.info(f"Sent alert to {chat_id}")
                except Exception as e:
                    logging.error(f"Failed to send to {chat_id}: {str(e)}")

    def get_immediate_expiry_domains(self, days=5):
        today = datetime.now().date()
        return [{
            'name': domain,
            'renewal_date': info['renewal_date'].date(),
            'days_remaining': (info['renewal_date'].date() - today).days
        } for domain, info in self.inventory.items() 
         if info['renewal_date'] and (info['renewal_date'].date() - today).days <= days]

    def _days_remaining(self, renewal_date):
        return (renewal_date.date() - datetime.now().date()).days

    async def setup_commands(self):
        # Set bot commands using BotCommand
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("check", "Check expiring domains")
        ]
        await self.application.bot.set_my_commands(commands)

    def run(self):
        try:
            logging.info("Bot starting...")

            # Schedule daily notifications
            self.application.job_queue.run_daily(
                self.send_daily_notification,
                time=datetime.time(hour=10, minute=0)  # Make sure to import 'datetime' for time if needed
            )

            # Schedule urgent checks every 2 days
            self.application.job_queue.run_repeating(
                self.send_telegram_alert,
                interval=timedelta(days=2),
                first=10
            )

            # Start polling
            self.application.run_polling()

        except Exception as e:
            logging.error(f"Error running bot: {str(e)}")
            raise

# Configuration
TOKEN = '7505234682:AAE6l0ybYR62JH9bcVyc0CDRNRDgK6PpkqQ'  # Replace with your actual token
bot = DomainMonitorBot(TOKEN)
bot.run()
