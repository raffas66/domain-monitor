import csv
from datetime import datetime, timedelta, time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import requests
import os


class DomainMonitorBot:
    def __init__(self, token):
        self.inventory = {}  # Now stores only domain names
        self.authorized_users = [
            7949976647,  # Admin
            7845296753   # Additional authorized user
        ]
        # Separate notification targets
        self.notification_chats = ['7949976647', '7845296753']

        # Set up logging
        logging.basicConfig(
            filename='bot.log',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        # Initialize application
        self.application = Application.builder().token(token).build()
        # Ensure job_queue is properly initialized
        self.job_queue = self.application.job_queue

        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("status", self.get_status))
        self.application.add_handler(
            CommandHandler("check", self.check_domains))

        # Load domains from CSV on startup
        self.load_domains_from_csv()

    async def start(self, update: Update, context):
        """Handle the /start command"""
        user = update.effective_user
        await update.message.reply_text(f"Hello {user.first_name}, I'm your Domain Monitor Bot! I'm here to notify you about domain expiration dates.")
        logging.info(f"User {user.id} initiated the /start command.")

    async def get_status(self, update: Update, context):
        """Handle /status command"""
        status_report = self._generate_status_report()
        await update.message.reply_text(
            text=status_report,
            parse_mode="MarkdownV2"
        )

    async def check_domains(self, update: Update, context):
        """Handle /check command"""
        alert_domains = self.get_immediate_expiry_domains(days=5)
        if alert_domains:
            await self.send_telegram_alert(context.bot)
        else:
            await update.message.reply_text("✅ No domains expiring within 5 days!")

    def _generate_status_report(self):
        report = "📊 **Domain Status Report**\n\n"
        for domain, info in self.inventory.items():
            days_left = (info['renewal_date'].date() -
                         datetime.now().date()).days
            report += (
                f"• **{domain}**\n"
                f"  - Expires: `{info['renewal_date'].strftime('%d-%b-%Y')}`\n"
                f"  - Days Left: `{days_left}`\n"
                f"  - Status: {info.get('situation', 'Unknown')}\n\n"
            )
        return report

    def load_domains_from_csv(self, filename='domains.csv'):
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.add_domain(
                        name=row['domain_name']  # Only add the domain name now
                    )
            logging.info(f"Successfully loaded domains from {filename}")
        except Exception as e:
            logging.error(f"Failed to load CSV: {str(e)}")

    def add_domain(self, name):
        """Add a domain to the inventory"""
        self.inventory[name] = {
        }  # Now the inventory only contains domain names


async def send_telegram_alert(self, context):
    alert_domains = self.get_immediate_expiry_domains(days=5)

    if alert_domains:
        message = "🚨 **URGENT DOMAIN ALERT** 🚨\n\n"
        for domain in alert_domains:
            info = self.inventory[domain['name']]
            expiration_date = info['renewal_date'].strftime("%d-%b-%Y")
            days_left = (info['renewal_date'].date() -
                         datetime.now().date()).days

            message += (
                f"🔹 **{domain['name']}**\n"
                f"▫️ *Expires*: `{expiration_date}`\n"
                f"▫️ *Days Left*: `{days_left}`\n"
                f"▫️ *Provider*: {info.get('provider', 'N/A')}\n"
                f"▫️ *Portal*: {info.get('link', 'Not available')}\n\n"
            )

        # Send to all notification chats with error handling
        for chat_id in self.notification_chats:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="MarkdownV2"  # Fixed parse mode
                )
            except Exception as e:
                logging.error(f"Failed to send alert to {chat_id}: {str(e)}")
                # Consider adding retry logic here

    def get_immediate_expiry_domains(self):
        # Since we are no longer dealing with renewal dates, this function is no longer relevant
        # Return all domains in the inventory
        return [{'name': domain} for domain in self.inventory]

    async def send_daily_notification(self, context):
        """This is the function that sends a daily notification."""
        message = "Merhaba!, This is your daily domain check notification!"
        for chat_id in self.notification_chats:
            try:
                await context.bot.send_message(chat_id=chat_id, text=message)
                logging.info(f"Sent daily notification to {chat_id}")
            except Exception as e:
                logging.error(
                    f"Failed to send daily notification to {chat_id}: {str(e)}")

    def run(self):  # PROPERLY INDENTED UNDER CLASS
        """Start the bot and handle job scheduling"""
        try:
            logging.info("Bot starting...")

            # Schedule notifications
            self.application.job_queue.run_daily(  # Fixed: use application.job_queue
                self.send_daily_notification,
                time=time(hour=10, minute=0)
            )
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
# Replace with your actual token
TOKEN = '7505234682:AAFCO9sFT3qUC1xXFqU7MHQ1SpNTiY30U-A'
bot = DomainMonitorBot(TOKEN)
bot.run()
